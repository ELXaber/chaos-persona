# skills/model_editor/probe.py
# Read-only. The *backend* (whatever actually reads activations) is pluggable because it
# needs full-precision HF weights, not the GGUF. Configure ONE of:
#   CAIOS_PROBE_BACKEND=http  CAIOS_PROBE_URL=http://127.0.0.1:8791/<route>
#       POST {"mode","prompt","layers","top_k"} -> {"neurons":[{"layer","neuron","score","note"?}]}
#   CAIOS_PROBE_BACKEND=cmd   CAIOS_PROBE_CMD='["uv","run","python","my_probe.py","{mode}","{prompt}","{top_k}"]'
#       stdout JSON in the same shape
# Adapt _call_backend() to the explorer's real routes/CLI; everything else is backend-independent.
import json
import os
import re
import subprocess
import time
import urllib.request
from collections import defaultdict
from typing import Any, Dict, List

from .schemas import ProbeRequest, PROBE_DIR, NEURON_STEERING_DIR

_TOOL_TAG = re.compile(r"\[TOOL:\w+[^\]]*\]")


class ProbeNotConfigured(Exception):
    pass


def _call_backend(mode: str, prompt: str, layers, top_k: int) -> List[dict]:
    backend = os.environ.get("CAIOS_PROBE_BACKEND", "").lower()
    if backend == "http":
        url = os.environ["CAIOS_PROBE_URL"]
        body = json.dumps({"mode": mode, "prompt": prompt, "layers": layers, "top_k": top_k}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read().decode("utf-8")).get("neurons", [])
    if backend == "cmd":
        template = json.loads(os.environ["CAIOS_PROBE_CMD"])
        sub = {"{mode}": mode, "{prompt}": prompt, "{top_k}": str(int(top_k)),
               "{layers}": ",".join(map(str, layers or []))}
        cmd = [sub.get(tok, tok) for tok in template]       # list, no shell
        r = subprocess.run(cmd, cwd=NEURON_STEERING_DIR or None, capture_output=True,
                           text=True, timeout=600)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout)[-500:])
        return json.loads(r.stdout).get("neurons", [])
    raise ProbeNotConfigured("set CAIOS_PROBE_BACKEND to 'http' or 'cmd' (see probe.py header)")


def _normalize(raw: List[dict]) -> List[dict]:
    out = []
    for n in raw:
        try:
            out.append({"layer": int(n["layer"]), "neuron": int(n["neuron"]),
                        "score": float(n["score"]),
                        "note": _TOOL_TAG.sub("[STRIPPED_TOOL_TAG]", str(n.get("note", "")))[:120]})
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _mean_scores(prompts: List[str], mode: str, layers, top_k: int) -> Dict[tuple, float]:
    acc = defaultdict(float)
    for p in prompts:
        for n in _normalize(_call_backend(mode, p, layers, top_k)):
            acc[(n["layer"], n["neuron"])] += n["score"]
    return {k: v / max(len(prompts), 1) for k, v in acc.items()}   # missing = 0


def rank_candidates(fail: Dict[tuple, float], ctrl: Dict[tuple, float], top_k: int) -> List[dict]:
    """Neurons that differ most between failure prompts and control prompts. Pure code."""
    keys = set(fail) | set(ctrl)
    rows = [{"layer": k[0], "neuron": k[1],
             "fail_mean": round(fail.get(k, 0.0), 4),
             "ctrl_mean": round(ctrl.get(k, 0.0), 4),
             "diff": round(fail.get(k, 0.0) - ctrl.get(k, 0.0), 4)} for k in keys]
    rows.sort(key=lambda r: abs(r["diff"]), reverse=True)
    return rows[:top_k]


def run_probe(req: ProbeRequest) -> Dict[str, Any]:
    errs = req.validate()
    if errs:
        return {"status": "error", "errors": errs}
    try:
        # over-fetch per prompt so the differential has room to work
        fetch_k = min(100, req.top_k * 5)
        fail = _mean_scores(req.inputs, req.mode, req.layers, fetch_k)
        ctrl = _mean_scores(req.control_inputs, req.mode, req.layers, fetch_k) if req.control_inputs else {}
    except ProbeNotConfigured as e:
        return {"status": "error", "error": str(e)}
    except Exception as e:
        return {"status": "error", "error": f"probe backend failed: {e}"}

    result = {
        "status": "ok", "mode": req.mode,
        "candidates": rank_candidates(fail, ctrl, req.top_k),
        "summary": f"{len(req.inputs)} failure / {len(req.control_inputs)} control prompts; "
                   f"ranked by |fail_mean - ctrl_mean|",
    }
    path = os.path.join(str(PROBE_DIR), f"probe_{int(time.time())}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"request": vars(req), **result}, f, indent=2)
    result["log"] = path
    return result
