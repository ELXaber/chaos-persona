# skills/model_editor/apply.py
# Two-phase, human-in-the-loop:
#   apply_edits()   validate -> baseline on BASE_PORT -> export .cvec.gguf -> return launch command
#   (you relaunch llama-server with the cvec on STEERED_PORT)
#   check_steered() run the same prompts against STEERED_PORT, score vs baseline
import hashlib
import json
import os
import re
import subprocess
import time
from typing import Any, Dict

from .schemas import (ApplyRequest, ARTIFACT_DIR, VERIFY_DIR, BASE_GGUF, BASE_PORT, HF_MODEL_ID,
                      NEURON_STEERING_DIR, STEERED_PORT, VerifyItem)
from .verify_suite import run_verify, has_errors, score_run

_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,60}$")


def _artifact_id(req: ApplyRequest) -> str:
    key = json.dumps([(e.layer, e.neuron, e.dose) for e in req.edits], sort_keys=True)
    return f"{req.label}-{hashlib.sha256(key.encode()).hexdigest()[:8]}"


EXPORT_BACKEND = os.environ.get("CAIOS_EXPORT_BACKEND", "neuron_steering").lower()


def _build_export_cmd(req: ApplyRequest, out_path: str):
    """
    Returns (cmd_list, error). Backends:
      neuron_steering  built-in: uv run python -m neuron_steering.ncvec export ...
      cmd              CAIOS_EXPORT_CMD = JSON list with placeholders:
                         {model}      HF model id (from config)
                         {out}        absolute output path
                         {push_args}  expands to: --push L:N:D --push L:N:D ...
                         {pushes}     expands to: L:N:D L:N:D ...  (for tools with their own flag)
                       Example:
                         ["uv","run","gne","export","--model","{model}","{push_args}","-o","{out}"]
    The template comes from the operator's environment, never from the LLM. Placeholder
    values are built only from validated ints/floats, and the command runs without a shell.
    """
    pushes = [f"{int(e.layer)}:{int(e.neuron)}:{float(e.dose):g}" for e in req.edits]
    out_abs = os.path.abspath(out_path)

    if EXPORT_BACKEND == "neuron_steering":
        cmd = ["uv", "run", "python", "-m", "neuron_steering.ncvec", "export",
               "--model", HF_MODEL_ID, "-o", out_abs]
        for p in pushes:
            cmd += ["--push", p]
        return cmd, None

    if EXPORT_BACKEND == "cmd":
        raw = os.environ.get("CAIOS_EXPORT_CMD", "")
        try:
            template = json.loads(raw)
            if not (isinstance(template, list) and all(isinstance(t, str) for t in template)):
                raise ValueError("must be a JSON list of strings")
        except Exception as ex:
            return None, f"CAIOS_EXPORT_CMD invalid: {ex}"
        if "{out}" not in template:
            return None, "CAIOS_EXPORT_CMD must contain an {out} token"
        cmd = []
        for tok in template:
            if tok == "{push_args}":
                for p in pushes:
                    cmd += ["--push", p]
            elif tok == "{pushes}":
                cmd += pushes
            elif tok == "{model}":
                cmd.append(HF_MODEL_ID)
            elif tok == "{out}":
                cmd.append(out_abs)
            else:
                cmd.append(tok)
        return cmd, None

    return None, f"unknown export backend {EXPORT_BACKEND!r} (use 'neuron_steering' or 'cmd')"


def _export_cvec(req: ApplyRequest, out_path: str) -> Dict[str, Any]:
    cmd, err = _build_export_cmd(req, out_path)
    if err:
        return {"ok": False, "error": err}
    cwd = NEURON_STEERING_DIR or None
    if cwd and not os.path.isdir(cwd):
        return {"ok": False, "error": f"CAIOS_NEURON_STEERING_DIR is not a directory: {cwd}"}
    if EXPORT_BACKEND == "neuron_steering" and not cwd:
        return {"ok": False, "error": "CAIOS_NEURON_STEERING_DIR not set"}
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=900)
    except Exception as ex:
        return {"ok": False, "error": str(ex)}
    if r.returncode != 0 or not os.path.exists(out_path):
        return {"ok": False, "error": (r.stderr or r.stdout)[-800:]}
    return {"ok": True}


def _launch_command(cvec_path: str) -> str:
    return (f'llama-server.exe -m "{BASE_GGUF or "<base .gguf>"}" '
            f'--control-vector "{os.path.abspath(cvec_path)}" '
            f'--port {STEERED_PORT} --ctx-size 8192 -ngl 99 --chat-template chatml')


def apply_edits(req: ApplyRequest) -> Dict[str, Any]:
    errs = req.validate()
    if errs:
        return {"status": "error", "errors": errs}

    items = req.verify
    print(f"[MODEL_EDITOR] baseline on port {BASE_PORT} ...")
    baseline = run_verify(BASE_PORT, items)
    if has_errors(baseline):
        return {"status": "error",
                "error": f"base server not reachable/valid on port {BASE_PORT}",
                "detail": baseline}

    art_id = _artifact_id(req)
    cvec_path = os.path.join(str(ARTIFACT_DIR), f"{art_id}.cvec.gguf")
    if not os.path.exists(cvec_path):
        exp = _export_cvec(req, cvec_path)
        if not exp["ok"]:
            return {"status": "error", "error": "cvec export failed", "detail": exp["error"]}

    manifest = {
        "artifact_id": art_id, "cvec": cvec_path, "created": time.time(),
        "hypothesis": req.hypothesis,
        "edits": [vars(e) for e in req.edits],
        "verify": [vars(v) for v in items],
        "baseline": baseline, "after": None, "score": None,
    }
    with open(os.path.join(str(ARTIFACT_DIR), f"{art_id}.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return {
        "status": "awaiting_steered_server",
        "artifact_id": art_id,
        "cvec": cvec_path,
        "launch_command": _launch_command(cvec_path),
        "next": f"Start the steered server on port {STEERED_PORT}, then call check_steered "
                f"with artifact_id={art_id}.",
        "baseline": baseline,
    }


def check_steered(artifact_id: str, port: int = STEERED_PORT) -> Dict[str, Any]:
    if not artifact_id:   # the chat history truncates old turns, so default to the newest artifact
        mans = sorted((p for p in os.listdir(str(ARTIFACT_DIR)) if p.endswith(".json")),
                      key=lambda p: os.path.getmtime(os.path.join(str(ARTIFACT_DIR), p)))
        if not mans:
            return {"status": "error", "error": "no artifacts yet"}
        artifact_id = mans[-1][:-5]
    if not _ID.match(artifact_id or ""):
        return {"status": "error", "error": "bad artifact_id"}
    mpath = os.path.join(str(ARTIFACT_DIR), f"{artifact_id}.json")
    if not os.path.exists(mpath):
        return {"status": "error", "error": f"unknown artifact {artifact_id}"}
    with open(mpath, "r", encoding="utf-8") as f:
        m = json.load(f)

    items = [VerifyItem(v["prompt"], v["expect"], v["role"]) for v in m["verify"]]
    after = run_verify(int(port), items)
    if has_errors(after):
        return {"status": "error",
                "error": f"steered server not reachable/valid on port {port}", "detail": after}

    score = score_run(items, m["baseline"], after)
    m["after"], m["score"] = after, {k: v for k, v in score.items() if k != "rows"}
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)
    with open(os.path.join(str(VERIFY_DIR), f"{artifact_id}_{int(time.time())}.json"),
              "w", encoding="utf-8") as f:
        json.dump(score, f, indent=2)
    return {"status": "checked", "artifact_id": artifact_id, **score}
