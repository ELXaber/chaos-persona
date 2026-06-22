#V06212026
# =============================================================================
"""
Ollama Configuration Bridge - CPOL State to Inference Parameters

This module bridges CAIOS's ternary logic (CPOL) state to Ollama's inference
parameters, ensuring the 12D manifold remains stable during local inference.

Created by master_init.py on first boot.
Imported by orchestrator.py and all subsystems.
"""
# =============================================================================

import json
import os
import urllib.request
import urllib.error
from typing import Dict, Optional, List

# File paths
IDENTITY_PATH = "system_identity.json"
CAIOS_PROMPT_PATH = "CAIOS.txt"
OLLAMA_ENDPOINT = "http://localhost:11434/api/tags"  # Health check only

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
            'auth_method': identity.get('auth_method', 'TEXT_USERNAME')
        }
    except Exception as e:
        print(f"[OLLAMA_CONFIG] Warning: Failed to load system_identity.json: {e}")
        return {'node_tier': 1, 'system_id': 'Error', 'auth_method': 'TEXT_USERNAME'}


def list_available_ollama_models() -> List[str]:
    """Return list of installed Ollama models."""
    try:
        import ollama
        models = ollama.list().get('models', [])
        return [m['model'] for m in models]
    except Exception:
        return []


def print_ollama_setup_help():
    """Print helpful setup instructions."""
    print("\n[OLLAMA SETUP HELP]")
    print("Ollama is not running or no models are installed.")
    print("Run these commands in a separate terminal:")
    print("   1. ollama serve")
    print("   2. ollama pull qwen3.6:27b")
    print("Then restart CAIOS.\n")


def load_caios_system_prompt(max_chars: int = 12000) -> str:
    """Load CAIOS.txt safely with UTF-8 encoding.
    max_chars: truncate for memory-constrained models (default 12000)
               set to 0 for no truncation (32b+ models with full VRAM)
    """
    if not os.path.exists(CAIOS_PROMPT_PATH):
        print("[OLLAMA_CONFIG] Warning: CAIOS.txt not found.")
        return ""
    try:
        with open(CAIOS_PROMPT_PATH, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if max_chars > 0 and len(content) > max_chars:
            print(f"[OLLAMA_CONFIG] System prompt truncated: "
                  f"{len(content)} → {max_chars} chars")
            return content[:max_chars]
        return content
    except UnicodeDecodeError:
        with open(CAIOS_PROMPT_PATH, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read().strip()
            print("[OLLAMA_CONFIG] Warning: Some characters replaced due to encoding.")
        if max_chars > 0 and len(content) > max_chars:
            return content[:max_chars]
        return content
    except Exception as e:
        print(f"[OLLAMA_CONFIG] Error loading CAIOS.txt: {e}")
        return ""


def get_cpol_ollama_params(
    contradiction_density: float = 0.12,
    evidence_score: float = 0.5,
    preferred_model: str = None,
    config: Optional[Dict] = None,
    domain: str = None
) -> Dict:
    """Map CPOL state to Ollama parameters."""
    if config is None:
        config = load_system_config()

    # Dynamic model selection with fallback
    model = preferred_model or config.get('ollama_model')
    available = list_available_ollama_models()

    if not model and available:
        model = available[0]
    elif not model:
        model = "llama3.2"
    if domain:
        model = get_model_for_domain(domain, model)

    base_temp = 0.85 - (contradiction_density * 0.75)
    temperature = max(0.1, min(0.9, base_temp))

    if config.get('node_tier', 1) == 0:
        temperature *= 0.92

    # Adjust system prompt size based on model
    if '27b' in model or '32b' in model or '70b' in model:
        prompt_limit = 0        # No truncation for large models
        num_ctx = 32768         # 32k context
    elif '14b' in model:
        prompt_limit = 12000
        num_ctx = 16384         # 16k context
    else:
        prompt_limit = 8000
        num_ctx = 8192          # Conservative for 7b and smaller

    return {
        "model": model,
        "system": load_caios_system_prompt(max_chars=prompt_limit),
        "options": {
            "temperature": round(temperature, 2),
            "num_predict": 4096,
            "top_p": 0.92,
            "repeat_penalty": 1.12,
            "num_ctx": num_ctx,
            "seed": -1
        }
    }


# Uncomment DOMAIN_MODEL_MAP to route queries to specialist models by domain.
# Requires sufficient VRAM to load multiple models (see readme.txt hardware notes).
# Models will hot-swap on domain change — expect 10-30s load penalty per switch.
# DOMAIN_MODEL_MAP = {
#     'programming': 'gemma3:12b-it-qat',
#     'medical':     'meditron:7b',
#     'legal':       None,   # fall back to default sovereign model
# }

# Uncomment DENSITY_MODEL_MAP to route queries to API by complexity.
# In get_cpol_ollama_params() — replaces the current single model fallback
# if contradiction_density < 0.3 and available:
#     model = available[-1]   # lightest/fastest available (Gemma 4, 7B, etc.)
# elif contradiction_density < 0.7 and available:
#     model = preferred_model or available[0]  # your default
# else:
#     # High complexity — use heaviest available (Qwen 27b, DeepSeek-R1)
#     model = preferred_model or available[0]

def get_model_for_domain(domain: str, default_model: str) -> str:
    """
    Route to a specialist model based on CPOL-classified domain.
    Returns default_model if DOMAIN_MODEL_MAP is not defined or domain has no entry.
    """
    try:
        return DOMAIN_MODEL_MAP.get(domain) or default_model
    except NameError:
        return default_model  # DOMAIN_MODEL_MAP not uncommented — use default


def check_ollama_available() -> bool:
    """Check if Ollama is running."""
    try:
        with urllib.request.urlopen(OLLAMA_ENDPOINT, timeout=3) as response:
            return response.status == 200
    except Exception:
        return False

def query_with_cpol(
    user_query: str,
    contradiction_density: float = None,
    evidence_score: float = 0.5,
    config: Optional[Dict] = None,
    tool_addendum: str = ""
) -> str:
    """
    Query Ollama with live CPOL-tuned parameters.
    Call this from any subsystem instead of raw requests.

    Args:
        user_query: The prompt to send
        contradiction_density: From paradox_oscillator (auto-detected if None)
        evidence_score: From query analysis (0.0-1.0)
        config: System config (auto-loaded if None)

    Returns:
        Model response string
    """
    import ollama

    # Auto-detect contradiction density if not provided
    if contradiction_density is None:
        try:
            from paradox_oscillator import ParadoxOscillator
            oscillator = ParadoxOscillator()
            contradiction_density = oscillator.detect_contradiction(user_query)
        except ImportError:
            contradiction_density = 0.12  # Default stable state

    params = get_cpol_ollama_params(
        contradiction_density=contradiction_density,
        evidence_score=evidence_score,
        config=config
    )

    # Prepend identity to system prompt
    identity_prefix = ""
    if os.path.exists("system_identity.json"):
        try:
            with open("system_identity.json", "r", encoding="utf-8") as f:
                identity = json.load(f)
            name = identity.get('system_id', 'Andrew')
            owner = identity.get('primary_user', 'User')
            identity_prefix = (
                f"Your name is {name}. "
                f"Your primary authority and owner is {owner}. "
                f"When introducing yourself, always state your name.\n\n"
            )
        except Exception:
            pass

    response = ollama.generate(
        model=params['model'],
        prompt=user_query,
        system=identity_prefix + params['system'] + tool_addendum,
        options=params['options']
    )

    # if response is entirely in <think> block
    result = response.get('response', '').strip()

    if not result:
        # Fallback: check alternate response fields
        result = response.get('message', {}).get('content', '').strip()

    if not result:
        result = "[LLM] No response generated — query may need rephrasing"

    return result

# Auto-load on import
try:
    SYSTEM_CONFIG = load_system_config()
    NODE_TIER = SYSTEM_CONFIG.get('node_tier', 1)
    SYSTEM_ID = SYSTEM_CONFIG.get('system_id', 'Unconfigured')

    if check_ollama_available():
        models = list_available_ollama_models()
        print(f"[OLLAMA_CONFIG] Loaded for Node Tier {NODE_TIER} | System ID: {SYSTEM_ID}")
        if models:
            print(f"[OLLAMA_CONFIG] Available models: {len(models)}")
        else:
            print_ollama_setup_help()
    else:
        print("[OLLAMA_CONFIG] Ollama not detected. Run 'ollama serve' in another terminal.")
except Exception as e:
    print(f"[OLLAMA_CONFIG] Failed to load config: {e}")
    SYSTEM_CONFIG = {'node_tier': 1, 'system_id': 'Unconfigured'}
    NODE_TIER = 1
    SYSTEM_ID = 'Unconfigured'