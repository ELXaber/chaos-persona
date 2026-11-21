# skills/model_editor/schemas.py
# Config + request shapes + validation. Everything that comes from the LLM is
# validated here; paths, model ids and ports come from env/config, never from the LLM.
import json
import os
import pathlib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

# ---- config (env overrides) -------------------------------------------------
EDIT_ROOT = pathlib.Path("working") / "model_edits"
REQUEST_DIR = EDIT_ROOT / "requests"
ARTIFACT_DIR = EDIT_ROOT / "artifacts"
PROBE_DIR = EDIT_ROOT / "probes"
VERIFY_DIR = EDIT_ROOT / "verify"
for _d in (REQUEST_DIR, ARTIFACT_DIR, PROBE_DIR, VERIFY_DIR):
    _d.mkdir(parents=True, exist_ok=True)

HF_MODEL_ID = os.environ.get("CAIOS_EDIT_HF_MODEL", "Qwen/Qwen3.5-4B")
NEURON_STEERING_DIR = os.environ.get("CAIOS_NEURON_STEERING_DIR", "")   # repo checkout (uv project)
BASE_GGUF = os.environ.get("CAIOS_EDIT_BASE_GGUF", "")                 # only used to print the launch command
BASE_PORT = int(os.environ.get("CAIOS_EDIT_BASE_PORT", "8081"))        # unsteered target server
STEERED_PORT = int(os.environ.get("CAIOS_EDIT_STEERED_PORT", "8082"))  # steered target server
N_LAYERS = int(os.environ.get("CAIOS_EDIT_N_LAYERS", "32"))
N_NEURONS = int(os.environ.get("CAIOS_EDIT_N_NEURONS", "0"))            # 0 = range unchecked; set from model config

MAX_DOSE = 2.0
MAX_EDITS = 4
MAX_VERIFY_ITEMS = 12
_SAFE_LABEL = re.compile(r"^[a-z0-9][a-z0-9._-]{0,39}$")


def safe_request_path(path: str) -> pathlib.Path:
    """Request JSON files must live under working/model_edits/."""
    p = pathlib.Path(path).resolve()
    root = EDIT_ROOT.resolve()
    if p != root and root not in p.parents:
        raise ValueError(f"request path must be under {EDIT_ROOT}")
    return p


def load_json_request(path: str) -> Dict[str, Any]:
    p = safe_request_path(path)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


# ---- probe ------------------------------------------------------------------
PROBE_URL = os.environ.get("CAIOS_PROBE_URL", "http://127.0.0.1:8787")   # neuron-steering app/server.py
PROBE_MODEL = os.environ.get("CAIOS_PROBE_MODEL", "small")              # "small" = Qwen3.5-4B in that app
PROBE_MODES = ("contrast", "activations", "logit_lens", "search", "concept", "hub")


def clean_prompt(p: str) -> str:
    """One line, bounded. The server's Contrast splits its inputs on newlines."""
    return " ".join(str(p).split())[:300]


@dataclass
class ProbeRequest:
    mode: Literal["contrast", "activations", "logit_lens", "search", "concept", "hub"]
    inputs: List[str] = field(default_factory=list)          # failure prompts
    control_inputs: List[str] = field(default_factory=list)  # prompts the model gets right
    neurons: List[str] = field(default_factory=list)         # "14:8949" addresses, for logit_lens
    words: List[str] = field(default_factory=list)           # tokens (search) or phrases (concept)
    layers: str = ""                                         # "first-last" for concept, e.g. "4-23"
    top_k: int = 20

    def validate(self) -> List[str]:
        errs = []
        if self.mode not in PROBE_MODES:
            errs.append(f"mode must be one of {PROBE_MODES}")
        if not (1 <= self.top_k <= 60):
            errs.append("top_k must be 1..60")
        if len(self.inputs) + len(self.control_inputs) > 16:
            errs.append("at most 16 prompts per probe")
        if self.mode == "contrast" and not (self.inputs and self.control_inputs):
            errs.append("contrast needs failure prompts (fail1..) and control prompts (ctrl1..)")
        if self.mode == "activations" and not self.inputs:
            errs.append("activations needs at least one failure prompt (fail1)")
        if self.mode == "logit_lens":
            if not self.neurons or len(self.neurons) > 8:
                errs.append("logit_lens needs 1-8 neurons like 14:8949")
            for n in self.neurons:
                try:
                    layer, neuron = (int(x) for x in n.split(":"))
                    if not (0 <= layer < N_LAYERS) or neuron < 0:
                        errs.append(f"neuron {n} out of range")
                except ValueError:
                    errs.append(f"bad neuron address {n!r} (use layer:neuron)")
        if self.mode in ("search", "concept") and not (1 <= len(self.words) <= 4):
            errs.append(f"{self.mode} needs 1-4 words/phrases")
        if self.mode == "hub":
            if len(self.neurons) != 1:
                errs.append("hub needs exactly one neuron like 14:8949")
            else:
                try:
                    layer, neuron = (int(x) for x in self.neurons[0].split(":"))
                    if not (0 <= layer < N_LAYERS) or neuron < 0:
                        errs.append("neuron out of range")
                except ValueError:
                    errs.append("bad neuron address (use layer:neuron)")
        if self.layers and not re.fullmatch(r"\d{1,2}-\d{1,2}", self.layers):
            errs.append("layers must look like 4-23")
        return errs

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ProbeRequest":
        return ProbeRequest(
            mode=d.get("mode", "contrast"),
            inputs=[clean_prompt(x) for x in d.get("inputs", [])],
            control_inputs=[clean_prompt(x) for x in d.get("control_inputs", [])],
            neurons=[str(x) for x in d.get("neurons", [])],
            words=[str(x).strip() for x in d.get("words", []) if str(x).strip()],
            layers=str(d.get("layers", "")),
            top_k=int(d.get("top_k", 20)),
        )


# ---- edits ------------------------------------------------------------------
@dataclass
class EditOp:
    layer: int
    neuron: int
    dose: float      # signed push, same meaning as --push LAYER:NEURON:DOSE

    def validate(self) -> List[str]:
        errs = []
        if not (0 <= self.layer < N_LAYERS):
            errs.append(f"layer {self.layer} out of range 0..{N_LAYERS - 1}")
        if self.neuron < 0 or (N_NEURONS and self.neuron >= N_NEURONS):
            errs.append(f"neuron {self.neuron} out of range")
        if not (abs(self.dose) <= MAX_DOSE) or self.dose == 0:
            errs.append(f"dose {self.dose} must be nonzero with |dose| <= {MAX_DOSE}")
        return errs


@dataclass
class VerifyItem:
    prompt: str
    expect: str                                   # regex the correct answer must match
    role: Literal["target", "control"] = "control"


@dataclass
class ApplyRequest:
    label: str
    edits: List[EditOp]
    verify: List[VerifyItem]
    hypothesis: str = ""

    def validate(self) -> List[str]:
        errs = []
        if not _SAFE_LABEL.match(self.label or ""):
            errs.append("label must match [a-z0-9][a-z0-9._-]{0,39}")
        if not self.edits:
            errs.append("edits cannot be empty")
        if len(self.edits) > MAX_EDITS:
            errs.append(f"at most {MAX_EDITS} edits per artifact")
        for e in self.edits:
            errs += e.validate()
        roles = [v.role for v in self.verify]
        if "target" not in roles or "control" not in roles:
            errs.append("verify needs at least one 'target' and one 'control' item")
        if len(self.verify) > MAX_VERIFY_ITEMS:
            errs.append(f"at most {MAX_VERIFY_ITEMS} verify items")
        for v in self.verify:
            try:
                re.compile(v.expect)
            except re.error as ex:
                errs.append(f"bad expect regex {v.expect!r}: {ex}")
        return errs

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ApplyRequest":
        # required keys raise KeyError on purpose: no silent defaults on edit values
        edits = [EditOp(int(e["layer"]), int(e["neuron"]), float(e["dose"])) for e in d["edits"]]
        verify = [VerifyItem(str(v["prompt"]), str(v["expect"]), v.get("role", "control"))
                  for v in d["verify"]]
        return ApplyRequest(label=str(d["label"]), edits=edits, verify=verify,
                            hypothesis=str(d.get("hypothesis", ""))[:500])


# ---- tag-attribute request builders ------------------------------------------
# The dispatcher's tag parser cannot carry JSON (no ']' and no '"' inside a tag), so the LLM
# passes flat attributes and these builders create the request objects. A request=<path> JSON
# file is still accepted for manual/advanced use (see load_json_request).

def _numbered(attrs: Dict[str, str], prefix: str, maxn: int = 8) -> List[str]:
    return [attrs[f"{prefix}{i}"] for i in range(1, maxn + 1) if attrs.get(f"{prefix}{i}")]


def alts_to_regex(alts: str) -> str:
    """'4|four' -> a safe whole-token regex built in code, so the LLM never writes regex."""
    parts = [re.escape(a.strip()) for a in alts.split("|") if a.strip()]
    if not parts:
        raise ValueError("empty expected answer")
    return r"(?<![\w.])(?:" + "|".join(parts) + r")(?!\w)"


def probe_from_attrs(attrs: Dict[str, str]) -> "ProbeRequest":
    return ProbeRequest(
        mode=attrs.get("mode", "contrast"),
        inputs=[clean_prompt(x) for x in _numbered(attrs, "fail")],
        control_inputs=[clean_prompt(x) for x in _numbered(attrs, "ctrl")],
        neurons=[x.strip() for x in attrs.get("neurons", "").split(";") if x.strip()],
        words=[x.strip() for x in attrs.get("words", "").split("|") if x.strip()],
        layers=attrs.get("layers", ""),
        top_k=int(attrs.get("top_k", 20)),
    )


def apply_from_attrs(attrs: Dict[str, str]) -> "ApplyRequest":
    edits = []
    for chunk in attrs.get("edits", "").split(";"):
        if chunk.strip():
            layer, neuron, dose = chunk.strip().split(":")   # ValueError if malformed
            edits.append(EditOp(int(layer), int(neuron), float(dose)))
    verify = []
    for role in ("target", "control"):
        for i in range(1, 9):
            p, x = attrs.get(f"{role}{i}"), attrs.get(f"{role}{i}_expect")
            if p:
                if not x:
                    raise ValueError(f"{role}{i} has no {role}{i}_expect")
                verify.append(VerifyItem(p, alts_to_regex(x), role))
    return ApplyRequest(label=attrs.get("label", ""), edits=edits, verify=verify,
                        hypothesis=attrs.get("hypothesis", "")[:500])
