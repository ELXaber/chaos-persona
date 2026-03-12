"""
Ollama Configuration Bridge - CPOL State to Inference Parameters

This module bridges CAIOS's ternary logic (CPOL) state to Ollama's inference
parameters, ensuring the 12D manifold remains stable during local inference.

Created by master_init.py on first boot.
Imported by orchestrator.py and all subsystems.
"""

import json
import os
from typing import Dict, Optional

# Load system identity (created by master_init)
IDENTITY_PATH = "system_identity.json"
CAIOS_PROMPT_PATH = "CAIOS.txt"
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"


def load_system_config() -> Dict:
    """Load system identity and configuration."""
    if not os.path.exists(IDENTITY_PATH):
        raise FileNotFoundError(
            "system_identity.json not found. Run master_init.py first."
        )

    with open(IDENTITY_PATH, 'r') as f:
        identity = json.load(f)

    return {
        'node_tier': identity.get('node_tier', 1),
        'system_id': identity.get('system_id', 'Unknown'),
        'auth_method': identity.get('auth_method', 'TEXT_USERNAME')
    }


def load_caios_system_prompt() -> str:
    """Load CAIOS.txt as Ollama system prompt."""
    if not os.path.exists(CAIOS_PROMPT_PATH):
        return ""  # Fallback to no system prompt

    with open(CAIOS_PROMPT_PATH, 'r') as f:
        return f.read()


def get_cpol_ollama_params(
    contradiction_density: float = 0.12,
    evidence_score: float = 0.5,
    config: Optional[Dict] = None
) -> Dict:
    """
    Calculate Ollama parameters based on live CPOL state.

    This function is called by subsystems BEFORE making Ollama requests
    to ensure inference parameters match current paradox oscillator state.

    Args:
        contradiction_density: From paradox_oscillator (0.0-1.0)
            High = paradox/conflict, lower temperature needed
            Low = clear reasoning, higher temperature for exploration
        evidence_score: From query analysis (0.0-1.0)
            High = strong evidence, larger context
            Low = weak evidence, smaller context
        config: System config (auto-loaded if None)

    Returns:
        Dict with Ollama generation parameters
    """
    if config is None:
        config = load_system_config()

    # Calculate temperature inversely to contradiction
    # High contradiction -> lower temp (stabilize)
    # Low contradiction -> higher temp (explore)
    base_temp = 0.8 - contradiction_density

    # Sovereign nodes (tier 0) get 10% stability boost
    if config['node_tier'] == 0:
        base_temp *= 0.9

    # Evidence affects context window
    context_size = 8192 if evidence_score > 0.5 else 4096

    return {
        "model": "deepseek-r1:14b",
        "system": load_caios_system_prompt(),  # CAIOS.txt loaded here
        "options": {
            "temperature": max(0.1, min(0.9, base_temp)),
            "num_predict": 4096,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "num_ctx": context_size
        }
    }


def check_ollama_available() -> bool:
    """Check if Ollama is running."""
    try:
        import requests
        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=2
        )
        return response.status_code == 200
    except:
        return False


# Auto-load config on import
try:
    SYSTEM_CONFIG = load_system_config()
    NODE_TIER = SYSTEM_CONFIG['node_tier']
    SYSTEM_ID = SYSTEM_CONFIG['system_id']
except:
    # Fallback if running before master_init
    SYSTEM_CONFIG = {'node_tier': 1, 'system_id': 'Unconfigured'}
    NODE_TIER = 1
    SYSTEM_ID = 'Unconfigured'