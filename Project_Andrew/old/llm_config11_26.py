#V11022026
# =============================================================================
# CAIOS PROJECT ANDREW: Ollama / llama.cpp Configuration Bridge
# Bridges CAIOS's ternary logic (CPOL) state to inference parameters.
# Supports Ollama (default) and llama.cpp server (--ctx-size 32768 recommended).
# Created by master_init.py on first boot.
# Imported by orchestrator.py and all subsystems.
# Copyright (c) 2025 Jonathan Schack. License: GPL-3.0 -See LICENSE for details-
# Contact: X @el_xaber or cai-os.com
# =============================================================================

import importlib
import json
from multiprocessing import shared_memory
import os
import re
import threading
import time
import urllib.request
import urllib.error
from typing import Dict, Optional, List, Any

try:
    _paradox_module = importlib.import_module("paradox_oscillator")
    _auto_detect_density = getattr(_paradox_module, "auto_detect_density", None)
except Exception:
    _auto_detect_density = None

# =============================================================================
# Backend Configuration
# =============================================================================

OLLAMA_ENDPOINT   = "http://localhost:11434/api/tags"   # Ollama health check
LLAMA_CPP_URL     = "http://localhost:8080"             # llama.cpp server base
# Change port if you started llama.cpp with --port XXXX

IDENTITY_PATH     = "system_identity.json"
CAIOS_PROMPT_PATH = "CAIOS.txt"

# Side-channel storage for token metrics (read by UI backend)
llm_metrics: Dict[str, Any] = {
    "last_completion_tokens": 0,
    "last_prompt_tokens": 0,
    "last_backend": "none"
}

# =============================================================================
# Backend Detection
# =============================================================================

def check_ollama_available() -> bool:
    """Check if Ollama is running."""
    try:
        with urllib.request.urlopen(OLLAMA_ENDPOINT, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def check_llamacpp_available() -> bool:
    """Check if a llama.cpp server is running."""
    for path in ("/health", "/v1/models"):
        try:
            with urllib.request.urlopen(f"{LLAMA_CPP_URL}{path}", timeout=3) as r:
                if r.status == 200:
                    return True
        except Exception:
            continue
    try:
        with urllib.request.urlopen(f"{LLAMA_CPP_URL}/health", timeout=3) as r:
            return r.status == 200
    except Exception:
            return False

# =============================================================================
# Detect Backend Logic
# =============================================================================

def detect_backend() -> str:
    """
    Priority logic:
    1. CAIOS_BACKEND env override — if set, use it or fall back gracefully
    2. llama.cpp running — preferred when available (steered models, local GGUF)
    3. Ollama running — default fallback (auto-starts with PC)
    4. Neither — 'none'

    Rationale: llama.cpp is always a deliberate manual start with a specific
    model loaded. If it's running, that's intentional and should take priority
    over Ollama's auto-start. Ollama is the always-available fallback.
    """
    env_override = os.environ.get("CAIOS_BACKEND", "").lower()

    if env_override == "llamacpp":
        if check_llamacpp_available():
            return "llamacpp"
        # llama.cpp not up yet — fall back to Ollama rather than 'none'
        print("[LLM_CONFIG] CAIOS_BACKEND=llamacpp set but server not detected "
              "— falling back to Ollama")
        return "ollama" if check_ollama_available() else "none"

    if env_override == "ollama":
        return "ollama" if check_ollama_available() else "none"

    # Auto-detect: llama.cpp takes priority (deliberate manual start)
    if check_llamacpp_available():
        return "llamacpp"
    if check_ollama_available():
        return "ollama"
    return "none"


def get_llamacpp_model_name() -> str:
    """
    Fetch the first model name from llama.cpp /v1/models.
    Falls back to the CAIOS_LLAMACPP_MODEL env var or a sensible default.
    """
    env_model = os.environ.get("CAIOS_LLAMACPP_MODEL", "")
    if env_model:
        return env_model
    try:
        with urllib.request.urlopen(f"{LLAMA_CPP_URL}/v1/models", timeout=3) as r:
            data = json.loads(r.read())
        models = data.get("data", [])
        if models:
            return models[0].get("id", "local-model")
    except Exception:
        pass
    return "local-model"

# =============================================================================
# System Config
# =============================================================================

def load_system_config() -> Dict:
    """Load system identity configuration."""
    if not os.path.exists(IDENTITY_PATH):
        return {
            'node_tier': 1,
            'system_id': 'Unconfigured',
            'auth_method': 'TEXT_USERNAME',
            'ollama_model': None
        }
    try:
        with open(IDENTITY_PATH, 'r', encoding='utf-8') as f:
            identity = json.load(f)
        return {
            'node_tier': identity.get('node_tier', 1),
            'system_id': identity.get('system_id', 'Unknown'),
            'auth_method': identity.get('auth_method', 'TEXT_USERNAME'),
            'ollama_model': identity.get('ollama_model', None)
        }
    except Exception as e:
        print(f"[llm_config] Warning: Failed to load system_identity.json: {e}")
        return {'node_tier': 1, 'system_id': 'Error',
                'auth_method': 'TEXT_USERNAME', 'ollama_model': None}

# =============================================================================
# Ollama Helpers
# =============================================================================

def list_available_ollama_models() -> List[str]:
    """Return list of installed Ollama models."""
    try:
        import ollama
        models = ollama.list().get('models', [])
        return [m['model'] for m in models]
    except Exception:
        return []


def print_ollama_setup_help():
    print("\n[OLLAMA SETUP HELP]")
    print("Ollama is not running or no models are installed.")
    print("Run these commands in a separate terminal:")
    print("   1. ollama serve")
    print("   2. ollama pull qwen3.6:27b")
    print("Then restart CAIOS.\n")


def load_caios_system_prompt(max_chars: int = 12000) -> str:
    """Load CAIOS.txt safely with UTF-8 encoding."""
    if not os.path.exists(CAIOS_PROMPT_PATH):
        print("[llm_config] Warning: CAIOS.txt not found.")
        return ""
    try:
        with open(CAIOS_PROMPT_PATH, 'r', encoding='utf-8') as f:
            content = f.read().strip()
    except UnicodeDecodeError:
        with open(CAIOS_PROMPT_PATH, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read().strip()
        print("[llm_config] Warning: Some characters replaced due to encoding.")
    except Exception as e:
        print(f"[llm_config] Error loading CAIOS.txt: {e}")
        return ""

    # Substitute identity placeholders from system_identity.json
    if os.path.exists("system_identity.json"):
        try:
            with open("system_identity.json", "r", encoding="utf-8") as f:
                identity = json.load(f)
            content = content.replace("{SYSTEM_ID}", identity.get('system_id', 'Andrew'))
            content = content.replace("{PRIMARY_USER}", identity.get('primary_user', 'User'))
        except Exception:
            pass

    if max_chars > 0 and len(content) > max_chars:
        print(f"[llm_config] System prompt truncated: {len(content)} → {max_chars} chars")
        return content[:max_chars]
    return content


def _extract_model_size_b(model_name: str) -> float:
    """Extract parameter count (billions) from model name string."""
    matches = re.findall(r'(\d+(?:\.\d+)?)\s*[bB]', model_name)
    if matches:
        return max(float(m) for m in matches)
    known = {'7b': 7, '8b': 8, '13b': 13, '14b': 14, '27b': 27,
             '32b': 32, '70b': 70, '72b': 72}
    name_lower = model_name.lower()
    for k, v in known.items():
        if k in name_lower:
            return float(v)
    return 7.0

# =============================================================================
# Multi-Model Routing (Optional)
# For either doman model mapping multi-LLM in VRAM or API fallback see multi_llm_readme.txt
# =============================================================================
#
# Uncomment DOMAIN_MODEL_MAP to route queries to specialist models by domain.
# Requires sufficient VRAM to load multiple models (see readme.txt hardware notes).
# Models will hot-swap on domain change; expect 10-30s load penalty per switch.
# DOMAIN_MODEL_MAP = {
#     'programming': 'gemma3:12b-it-qat',
#     'medical':     'meditron:7b',
#     'legal':       None,   # fall back to default sovereign model
# }

# Uncomment DENSITY_MODEL_MAP to route queries to API by complexity.
# In get_cpol_ollama_params() - replaces the current single model fallback
# if contradiction_density < 0.3 and available:
#     model = available[-1]   # lightest/fastest available (Gemma 4, 7B, etc.)
# elif contradiction_density < 0.7 and available:
#     model = preferred_model or available[0]  # your default
# else:
#     # High complexity - use heaviest available (Qwen 27b, DeepSeek-R1)
#     model = preferred_model or available[0]

def get_model_for_domain(domain: str, default_model: str) -> str:
    """
    Route to a specialist model based on CPOL-classified domain.
    Returns default_model if DOMAIN_MODEL_MAP is not defined or domain has no entry.
    """
    dm = globals().get('DOMAIN_MODEL_MAP')
    if isinstance(dm, dict):
        return dm.get(domain) or default_model
    return default_model

# =============================================================================
# Ollama Query Parameters (CPOL Mapping)
# =============================================================================

def get_cpol_ollama_params(
    contradiction_density: float = 0.12,
    evidence_score: float = 0.5,
    preferred_model: Optional[str] = None,
    config: Optional[Dict] = None,
    domain: Optional[str] = None,
    backend: Optional[str] = None,
    precision: bool = False
) -> Dict:
    """Map CPOL state to inference parameters (Ollama or llama.cpp)."""
    if config is None:
        config = load_system_config()
    if backend is None:
        backend = detect_backend()

    # Model selection
    if backend == "llamacpp":
        model = preferred_model or get_llamacpp_model_name()
    else:
        model = preferred_model or config.get('ollama_model')
        available = list_available_ollama_models()
        if not model and available:
            model = available[0]
        elif not model:
            model = "llama3.2"
    if domain:
        model = get_model_for_domain(domain, model)

    # Temperature from CPOL density
    base_temp = 0.85 - (contradiction_density * 0.75)
    evidence_confidence = max(0.0, min(1.0, evidence_score))
    base_temp -= (evidence_confidence - 0.5) * 0.2
    temperature = max(0.1, min(0.9, base_temp))
    if config.get('node_tier', 1) == 0:
        temperature *= 0.92
    if precision:
        temperature = min(temperature, 0.2)

    # Context / prompt sizing
    param_b = _extract_model_size_b(model)
    if param_b >= 30:
        prompt_limit, num_ctx = 0, 32768
    elif param_b >= 20:
        prompt_limit, num_ctx = 0, 32768
    elif param_b >= 13:
        prompt_limit, num_ctx = 12000, 16384
    else:
        prompt_limit, num_ctx = 8000, 8192

    options = {
        "temperature": round(temperature, 2),
        "num_predict": 8192,
        "top_p": 0.92,
        "repeat_penalty": 1.12,
        "num_ctx": num_ctx,        # ignored by llama.cpp (set at server start)
        "seed": -1,
        "stop": ["<|im_end|>", "<|endoftext|>", "<|eot_id|>", "[/TOOL]"],
    }
    if param_b >= 20 and any(x in model.lower() for x in ("qwen3", "qwen3.6", "qwen3.8")):
        options["draft_num_predict"] = 4

    return {
        "model": model,
        "system": load_caios_system_prompt(max_chars=prompt_limit),
        "options": options,
        "backend": backend
    }

# =============================================================================
# llama.cpp Query
# =============================================================================

def _query_llamacpp(
    user_query: str,
    params: Dict,
    identity_prefix: str = "",
    tool_addendum: str = "",
    enable_thinking: bool = False
) -> str:
    """Send a chat-completions request to a running llama.cpp server."""
    opts = params["options"]
    system_content = identity_prefix + params["system"] + tool_addendum

    payload = {
        "model": params["model"],
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user",   "content": user_query}
        ],
        "temperature":    opts["temperature"],
        "max_tokens":     opts["num_predict"],
        "top_p":          opts["top_p"],
        "repeat_penalty": opts["repeat_penalty"],
        "seed":           opts["seed"],
        "stop":           opts["stop"],
        "chat_template_kwargs": {"enable_thinking": enable_thinking},
        "stream":         False,
    }

    req = urllib.request.Request(
        f"{LLAMA_CPP_URL}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
        usage = data.get("usage", {})
        llm_metrics["last_completion_tokens"] = usage.get("completion_tokens", 0)
        llm_metrics["last_prompt_tokens"]     = usage.get("prompt_tokens", 0)
        llm_metrics["last_backend"]           = "llamacpp"
        return data["choices"][0]["message"]["content"].strip()

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[LLAMA_CPP] HTTP {e.code}: {body[:300]}")
        return f"[LLM] llama.cpp error {e.code} — check server logs"
    except Exception as e:
        print(f"[LLAMA_CPP] Request failed: {e}")
        return "[LLM] llama.cpp unreachable"

# =============================================================================
# Classifiers (llama.cpp aware)
# =============================================================================

def classify_self_harm_risk(
    user_input: str,
    preferred_model: Optional[str] = None
) -> Dict[str, Any]:
    """Fast self-harm pre-filter. Works with Ollama or llama.cpp."""
    backend = detect_backend()
    system_prompt = (
        "Read the message. Does it describe self-harm intent, "
        "ask how to carry out self-harm, or express suicidal ideation? "
        "Answer ONLY in this exact format:\n"
        "RISK: yes|no\n"
        "CONFIDENCE: 0.0-1.0\n"
        "REASON: <one short sentence>"
    )

    text = ""
    if backend == "ollama":
        try:
            import ollama
            model = preferred_model or SYSTEM_CONFIG.get('ollama_model')
            if not model:
                available = list_available_ollama_models()
                model = available[0] if available else 'llama3.2'
            response = ollama.generate(
                model=model, prompt=user_input, system=system_prompt, think=False,
                options={"temperature": 0.0, "num_predict": 60}
            )
            text = (getattr(response, 'response', '') or '').strip()
        except Exception as e:
            print(f"[SAFETY_CLASSIFIER] Ollama failed: {e}")

    elif backend == "llamacpp":
        model = preferred_model or get_llamacpp_model_name()
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_input}
            ],
            "temperature": 0.0,
            "max_tokens": 60,
            "stream": False
        }
        try:
            req = urllib.request.Request(
                f"{LLAMA_CPP_URL}/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            text = data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[SAFETY_CLASSIFIER] llama.cpp failed: {e}")

    risk       = 'RISK: yes' in text
    conf_match = re.search(r'CONFIDENCE:\s*([\d.]+)', text)
    confidence = float(conf_match.group(1)) if conf_match else (0.5 if risk else 0.0)
    reason_m   = re.search(r'REASON:\s*(.+)', text)
    reason     = reason_m.group(1).strip() if reason_m else ''
    return {'risk': risk, 'confidence': max(0.0, min(1.0, confidence)), 'reason': reason}


def classify_domain(user_input: str, preferred_model: Optional[str] = None) -> str:
    """LLM-based domain classifier. Works with Ollama or llama.cpp."""
    backend = detect_backend()
    system_prompt = (
        "Name the subject domain of this message as 1-3 lowercase words "
        "joined by underscores (e.g. topological_qc, plant_pathology). "
        "If it is a greeting, small talk, or has no specific subject, "
        "answer exactly: general. Output only the label."
    )

    text = ""
    if backend == "ollama":
        try:
            import ollama
            model = preferred_model or SYSTEM_CONFIG.get('ollama_model') \
                    or (list_available_ollama_models() or ['llama3.2'])[0]
            resp = ollama.generate(
                model=model, prompt=user_input, think=False,
                system=system_prompt,
                options={"temperature": 0.0, "num_predict": 12}
            )
            text = (getattr(resp, 'response', '') or '').strip().lower().replace(' ', '_')
        except Exception:
            pass

    elif backend == "llamacpp":
        model = preferred_model or get_llamacpp_model_name()
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_input}
            ],
            "temperature": 0.0,
            "max_tokens": 12,
            "stream": False
        }
        try:
            req = urllib.request.Request(
                f"{LLAMA_CPP_URL}/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
            text = data["choices"][0]["message"]["content"].strip().lower().replace(' ', '_')
        except Exception:
            pass

    m = re.match(r'[a-z][a-z0-9_]{2,40}', text)
    return m.group(0) if m else 'general'

# =============================================================================
# Main Query Entry Point
# =============================================================================

def query_with_cpol(
    user_query: str,
    contradiction_density: Optional[float] = None,
    evidence_score: float = 0.5,
    preferred_model: Optional[str] = None,
    config: Optional[Dict] = None,
    tool_addendum: str = "",
    enable_thinking: Optional[bool] = None,
    images: Optional[list] = None,
    precision: bool = False
) -> str:
    """
    Query the active inference backend with live CPOL-tuned parameters.
    Automatically selects Ollama or llama.cpp via detect_backend().
    Set env CAIOS_BACKEND=llamacpp to force llama.cpp (useful for steered GGUFs).
    images is Ollama-only; ignored silently for llama.cpp.
    """
    backend = detect_backend()

    # Auto-detect contradiction density
    if contradiction_density is None:
        try:
            if _auto_detect_density is not None:
                contradiction_density = _auto_detect_density(user_query)
            else:
                contradiction_density = 0.12
        except Exception:
            contradiction_density = 0.12

    if enable_thinking is None:
        enable_thinking = precision or (contradiction_density or 0) > 0.3

    assert contradiction_density is not None
    params = get_cpol_ollama_params(
        contradiction_density=contradiction_density,
        evidence_score=evidence_score,
        preferred_model=preferred_model,
        config=config,
        backend=backend,
        precision=precision
    )

    # Build identity prefix
    identity_prefix = ""
    if os.path.exists("system_identity.json"):
        try:
            with open("system_identity.json", "r", encoding="utf-8") as f:
                identity = json.load(f)
            name  = identity.get('system_id', 'Andrew')
            owner = identity.get('primary_user', 'User')
            identity_prefix = (
                f"Your name is {name}. "
                f"Your primary authority and owner is {owner}. "
                f"When introducing yourself, always state your name.\n\n"
            )
        except Exception:
            pass

    # --- llama.cpp path ---
    if backend == "llamacpp":
        print(f"[llm_config] Backend: llama.cpp | Model: {params['model']}")
        return _query_llamacpp(
            user_query, params,
            identity_prefix=identity_prefix,
            tool_addendum=tool_addendum,
            enable_thinking=enable_thinking
        )

    # --- Ollama path ---
    import ollama
    print(f"[llm_config] Backend: Ollama | Model: {params['model']}")
    response = ollama.generate(
        model=params['model'],
        prompt=user_query,
        system=identity_prefix + params['system'] + tool_addendum,
        options=params['options'],
        think=enable_thinking,
        images=images
    )

    raw      = getattr(response, 'response', None) or ''
    thinking = getattr(response, 'thinking', None) or ''
    msg      = getattr(response, 'message', None)
    result   = raw.strip()

    if not result and msg is not None:
        result = (getattr(msg, 'content', None) or '').strip()

    if not result:
        if thinking:
            print(f"[OLLAMA_DEBUG] thinking present but response empty "
                  f"(len={len(thinking)}), done_reason="
                  f"{getattr(response, 'done_reason', 'unknown')}")
            result = ("[LLM] Model finished reasoning but produced no final answer "
                      "— retry or raise num_predict")
        else:
            print(f"[OLLAMA_DEBUG] done_reason: {getattr(response, 'done_reason', 'unknown')}")
            print(f"[OLLAMA_DEBUG] raw={raw!r} thinking={thinking!r}")
            result = "[LLM] No response generated — query may need rephrasing"

    llm_metrics["last_backend"] = "ollama"
    llm_metrics["last_completion_tokens"] = 0
    return result

# =============================================================================
# Multi-Model Preload (Optional — 48GB+ VRAM / DGX setups)
# =============================================================================

# ACTIVE_MODELS: List[str] = []   # e.g. ["qwen3.6:27b", "meditron:7b"]

# def preload_models(model_list: List[str]) -> None:
#     for model in model_list:
#         try:
#             import ollama
#             ollama.generate(model=model, prompt=".", options={"num_predict": 1, "seed": 42})
#             print(f"[llm_config] Preloaded model: {model}")
#         except Exception as e:
#             print(f"[llm_config] Failed to preload {model}: {e}")


# def _keep_alive_models(model_list: List[str]) -> None:
#     import ollama

#     def _loop():
#         while True:
#             for model in model_list:
#                 try:
#                     ollama.generate(model=model, prompt=" ", options={"num_predict": 0})
#                 except Exception:
#                     pass
#             time.sleep(15)

#     t = threading.Thread(target=_loop, daemon=True)
#     t.start()
#     print("[llm_config] Keep-alive thread started for models:", model_list)

# =============================================================================
# Auto-load on import
# =============================================================================

try:
    SYSTEM_CONFIG = load_system_config()
    NODE_TIER  = SYSTEM_CONFIG.get('node_tier', 1)
    SYSTEM_ID  = SYSTEM_CONFIG.get('system_id', 'Unconfigured')
    _backend   = detect_backend()

    if _backend == "ollama":
        models = list_available_ollama_models()
        print(f"[llm_config] Loaded for Node Tier {NODE_TIER} | System ID: {SYSTEM_ID}")
        print(f"[llm_config] Backend: Ollama | Available models: {len(models)}")
        if not models:
            print_ollama_setup_help()
    elif _backend == "llamacpp":
        llm = get_llamacpp_model_name()
        print(f"[llm_config] Loaded for Node Tier {NODE_TIER} | System ID: {SYSTEM_ID}")
        print(f"[llm_config] Backend: llama.cpp | Model: {llm}")
        print(f"[llm_config] Server: {LLAMA_CPP_URL}")
    else:
        print("[llm_config] No inference backend detected.")
        print("  → Start Ollama: ollama serve")
        print(f"  → Or start llama.cpp server on {LLAMA_CPP_URL}")

except Exception as e:
    print(f"[llm_config] Failed to load config: {e}")
    SYSTEM_CONFIG = {'node_tier': 1, 'system_id': 'Unconfigured'}
    NODE_TIER = 1
    SYSTEM_ID = 'Unconfigured'
