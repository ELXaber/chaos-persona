# skills/model_editor/probe.py
# Read-only client for the neuron-steering GUI server (app/server.py), which holds the target
# model (Qwen3.5-4B, "small") in neuron-explorer's runtime. Start it with:
#     uv run python app/server.py        (default http://127.0.0.1:8787; set CAIOS_PROBE_URL if different)
# Routes used (verified against app/server.py and app/models.py):
#     POST /api/contrast  {model, a, b}      -> {"results": [{layer, neuron, expert, score, act}]}
#     POST /api/fires     {model, text}      -> {"tokens", "per_token", "overall": [{layer, neuron, score, act, pos}]}
#     GET  /api/lens      model,layer,neuron,k -> {"up": ..., "down": ...}   (weight-only logit lens)
#     GET  /api/search    model,q            -> {"results": [{layer, neuron, sign}]}  (neurons whose lens has the word)
# The server runs one job at a time and answers {"error": ...} when busy.
# Two more modes run neuron_steering.find as a command (they are not server routes):
#     concept  neurons whose steer lens MEANS a phrase (loads a small embedding model; first run builds a cache)
#     hub      a neuron's strongest direct-path drivers and readers (cached weights only, fast)
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List

from .schemas import NEURON_STEERING_DIR, PROBE_DIR, PROBE_MODEL, PROBE_URL, ProbeRequest

_TOOL_TAG = re.compile(r"\[TOOL:\w+[^\]]*\]")
TIMEOUT = 900   # the first call loads the model


class ProbeError(Exception):
    pass


def _http(method: str, path: str, body: Dict[str, Any] = None, query: Dict[str, Any] = None) -> Any:
    url = PROBE_URL.rstrip("/") + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if data else {})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            out = json.loads(r.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise ProbeError(f"probe server not reachable at {PROBE_URL} ({e.reason}); "
                         f"start it with: uv run python app/server.py")
    if isinstance(out, dict) and out.get("error"):
        raise ProbeError(str(out["error"]))
    return out


def _rows(rows: List[dict], k: int) -> List[dict]:
    out = []
    for r in rows[:k]:
        try:
            out.append({"layer": int(r["layer"]), "neuron": int(r["neuron"]),
                        "score": round(float(r["score"]), 3)})
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _clip(x: Any, k: int = 16) -> Any:
    """Lens output shape is the explorer's own; pass it through, bounded, with tool tags stripped."""
    if isinstance(x, list):
        x = x[:k]
    return json.loads(_TOOL_TAG.sub("[STRIPPED_TOOL_TAG]", json.dumps(x))[:4000]) \
        if len(json.dumps(x)) <= 4000 else str(x)[:2000]


def _contrast(req: ProbeRequest) -> Dict[str, Any]:
    r = _http("POST", "/api/contrast", {"model": PROBE_MODEL, "a": "\n".join(req.inputs),
                                        "b": "\n".join(req.control_inputs)})
    return {"candidates": _rows(r.get("results", []), req.top_k),
            "meaning": "score = (mean activation on failure prompts - mean on controls) / the neuron's usual range. "
                       "Positive: more active on failures (try a NEGATIVE dose to suppress it); "
                       "negative: less active (try a POSITIVE dose)."}


def _activations(req: ProbeRequest) -> Dict[str, Any]:
    per = []
    for p in req.inputs:
        r = _http("POST", "/api/fires", {"model": PROBE_MODEL, "text": p})
        per.append({"prompt": p, "tokens": r.get("tokens", [])[:60],
                    "top": _rows(r.get("overall", []), req.top_k)})
    return {"per_prompt": per,
            "meaning": "score = activation relative to the neuron's usual range (|score| > 1 is unusually strong). "
                       "Only the prompt's own tokens are read, not the model's generated answer."}


def _lens(req: ProbeRequest) -> Dict[str, Any]:
    out = {}
    for n in req.neurons:
        layer, neuron = (int(x) for x in n.split(":"))
        r = _http("GET", "/api/lens", query={"model": PROBE_MODEL, "layer": layer, "neuron": neuron, "k": 12})
        out[n] = {"pushes_toward": _clip(r.get("up")), "pushes_away_from": _clip(r.get("down"))}
    return {"lens": out, "meaning": "tokens each neuron's output promotes (up) or suppresses (down)."}


def _search(req: ProbeRequest) -> Dict[str, Any]:
    out = {}
    for w in req.words:
        r = _http("GET", "/api/search", query={"model": PROBE_MODEL, "q": w})
        out[w] = [{"layer": x.get("layer"), "neuron": x.get("neuron"), "sign": x.get("sign")}
                  for x in r.get("results", [])[:req.top_k]]
    return {"neurons_by_word": out,
            "meaning": "neurons whose logit lens contains the word; sign + means a positive push promotes it."}


def _cli(args: List[str], timeout: int) -> str:
    if not NEURON_STEERING_DIR or not os.path.isdir(NEURON_STEERING_DIR):
        raise ProbeError("CAIOS_NEURON_STEERING_DIR is not set to the neuron-steering checkout")
    cmd = ["uv", "run", "python", "-m", "neuron_steering.find", *args]      # list, no shell
    try:
        r = subprocess.run(cmd, cwd=NEURON_STEERING_DIR, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise ProbeError("`uv` not found on PATH")
    except subprocess.TimeoutExpired:
        raise ProbeError(f"find timed out after {timeout}s")
    if r.returncode != 0:
        raise ProbeError((r.stderr or r.stdout)[-500:])
    return _TOOL_TAG.sub("[STRIPPED_TOOL_TAG]", r.stdout)[:4000]


def _concept(req: ProbeRequest) -> Dict[str, Any]:
    out_path = os.path.abspath(os.path.join(str(PROBE_DIR), f"concept_{int(time.time())}.json"))
    phrases = [re.sub(r"^[-\s]+", "", w)[:60] for w in req.words]        # no leading '-' (option injection)
    args = ["concept", "-k", str(min(req.top_k, 20)), "-o", out_path]
    if req.layers:
        args += ["--layers", req.layers]
    text = _cli(args + ["--"] + phrases, timeout=900)
    cands = []
    try:
        for c in json.load(open(out_path, encoding="utf-8")):
            l, n, dose = c["pushes"][0]
            cands.append({"name": str(c["name"])[:80], "layer": int(l), "neuron": int(n), "dose": float(dose)})
    except Exception:
        pass
    return {"candidates": cands, "report": text,
            "meaning": "neurons whose output means the phrase. The sign of dose is the push that PROMOTES the "
                       "concept (use the opposite sign to suppress it). Default layers 8-21; widen with layers=\"4-23\"."}


def _hub(req: ProbeRequest) -> Dict[str, Any]:
    layer, neuron = (int(x) for x in req.neurons[0].split(":"))
    text = _cli(["hub", str(layer), str(neuron), "-k", str(min(req.top_k, 16))], timeout=180)
    return {"report": text,
            "meaning": "'driven by' = neurons that feed this one; 'writes into' = neurons it feeds. "
                       "Check these before pushing: they show what else a push is likely to move."}


_MODES = {"contrast": _contrast, "activations": _activations, "logit_lens": _lens, "search": _search,
          "concept": _concept, "hub": _hub}


def run_probe(req: ProbeRequest) -> Dict[str, Any]:
    errs = req.validate()
    if errs:
        return {"status": "error", "errors": errs}
    try:
        result = {"status": "ok", "mode": req.mode, **_MODES[req.mode](req)}
    except ProbeError as e:
        return {"status": "error", "error": str(e)}
    except Exception as e:
        return {"status": "error", "error": f"probe failed: {type(e).__name__}: {e}"}
    path = os.path.join(str(PROBE_DIR), f"probe_{int(time.time())}_{req.mode}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"request": vars(req), **result}, f, indent=2)
    result["log"] = path
    return result
