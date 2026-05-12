#V05112026
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
import requests
from typing import Dict, Optional, List

IDENTITY_PATH = "system_identity.json"
CAIOS_PROMPT_PATH = "CAIOS.txt"
OLLAMA_ENDPOINT = "http://localhost:11434/api/tags"


def load_system_config() -> Dict:
    if not os.path.exists(IDENTITY_PATH):
        return {'node_tier': 1, 'system_id': 'Unconfigured', 'ollama_model': None}

    try:
        with open(IDENTITY_PATH, 'r', encoding='utf-8') as f:
            identity = json.load(f)
        return {
            'node_tier': identity.get('node_tier', 1),
            'system_id': identity.get('system_id', 'Unconfigured'),
            'ollama_model': identity.get('ollama_model')
        }
    except Exception:
        print(f"[OLLAMA_CONFIG] Warning: Failed to load system_identity.json: {e}")
        return {'node_tier': 1, 'system_id': 'Error', 'ollama_model': None}


def list_available_ollama_models() -> List[str]:
    try:
        import ollama
        models = ollama.list().get('models', [])
        return [m['model'] for m in models]
    except Exception:
        return []


def print_ollama_setup_help():
    print("\n[OLLAMA SETUP HELP]")
    print("Ollama is not running or no models found.")
    print("Please run in another terminal:")
    print("   ollama serve")
    print("   ollama pull llama3.2")
    print("Then restart CAIOS.\n")


def load_caios_system_prompt() -> str:
    if not os.path.exists(CAIOS_PROMPT_PATH):
        return "You are a helpful, truthful assistant."
    try:
        with open(CAIOS_PROMPT_PATH, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception:
        return "You are a helpful, truthful assistant."


def get_cpol_ollama_params(
    contradiction_density: float = 0.12,
    evidence_score: float = 0.5,
    preferred_model: str = None
) -> Dict:
    """Main function: returns ready-to-use params for ollama.chat()"""
    config = load_system_config()

    # Model priority: preferred > saved > first available > safe default
    model = preferred_model or config.get('ollama_model')
    available = list_available_ollama_models()

    if not model and available:
        model = available[0]
    elif not model:
        model = "llama3.2"

    # CPOL-aware temperature
    base_temp = 0.85 - (contradiction_density * 0.75)
    temperature = max(0.1, min(0.9, base_temp))

    if config.get('node_tier', 1) == 0:
        temperature *= 0.92

    return {
        "model": model,
        "system": load_caios_system_prompt(),
        "options": {
            "temperature": round(temperature, 2),
            "num_predict": 4096,
            "top_p": 0.92,
            "repeat_penalty": 1.12,
            "num_ctx": 8192 if evidence_score > 0.5 else 4096,
            "seed": -1
        }
    }


# Auto-init message
try:
    config = load_system_config()
    print(f"[OLLAMA_CONFIG] Loaded for Node Tier {config.get('node_tier')} | System ID: {config.get('system_id')}")
    if not check_ollama_available():
        print_ollama_setup_help()
except Exception as e:
    print(f"[OLLAMA_CONFIG] Warning: {e}")