#V06252026

Multi-LLM setup:
CAIOS retains context, memory, system identity, and coherance while changing LLMs by default; it uses the LLM as a CPU.
No changes are needed, but for the domain or density mapping or API fallback see below.

This bridges CAIOS's ternary logic (CPOL) state to Ollama's inference parameters, ensuring the 12D manifold remains stable during local inference.

- API FALLBACK: If Ollama is unavailable, _call_api_client() routes to
  OpenAI/Anthropic/xAI/Google. CPOL remains local; only LLM generation is
  cloud-based. Network latency adds 1-3s per query.
  Default: Enabled (graceful degradation).
  
- DENSITY_MODEL_MAP: Routes queries to lighter/faster models when contradiction
  density is low. Same VRAM requirements as DOMAIN_MODEL_MAP.
  Default: Disabled (single model only).
  in _call_api_client, you can adjust max_tokens to match your local model's speed: max_tokens = 4096 if contradiction_density < 0.5 else 2048

- DOMAIN_MODEL_MAP: Routes queries to specialist models by domain.
  Requires sufficient VRAM to load multiple models simultaneously: See below for additions to ollama_config.
  On DGX/A6000 (48GB+), you can preload models with preload_models().
  On 24GB cards (3090/4090), swapping models will cause 10-30s delays.
  Default: Disabled (single model start only).
  If you intend to use the domain mapping with multiple LLMs and have the VRAM to support, there's some additions.
  You need to pre-load the models and add a keep-alive in ollama_config.

- llama.cpp instead of Ollama setup instructions:

# =============================================================================
# Multi-Model Preload (Optional for DGX / high-VRAM setups)
# =============================================================================

# Uncomment and customize this block in ollama_config if you have 48GB+ VRAM
ACTIVE_MODELS = [
    "qwen3.6:27b",
    "meditron:7b"
]

# Preload models on import (optional — uncomment to enable)
# try:
#     preload_models(ACTIVE_MODELS)
#     _keep_alive_models(ACTIVE_MODELS)
# except Exception as e:
#     print(f"[OLLAMA_CONFIG] Multi-model preload failed: {e}")

# Include two defs for preload and keep alive.

def preload_models(model_list: List[str]) -> None:
    """
    Preload multiple models into VRAM at startup.
    Call this once after Ollama is running.
    """
    for model in model_list:
        try:
            # Send a minimal prompt to force the model into VRAM
            import ollama
            ollama.generate(
                model=model,
                prompt=".",
                options={"num_predict": 1, "seed": 42}
            )
            print(f"[OLLAMA_CONFIG] Preloaded model: {model}")
        except Exception as e:
            print(f"[OLLAMA_CONFIG] Failed to preload {model}: {e}")


def _keep_alive_models(model_list: List[str]) -> None:
    """
    Keep models resident in VRAM by sending tiny keep-alive prompts.
    Call this in a background thread every 10–20 seconds.
    """
    import ollama
    import threading
    import time

    def _keep_alive_loop():
        while True:
            for model in model_list:
                try:
                    ollama.generate(
                        model=model,
                        prompt=" ",
                        options={"num_predict": 0}
                    )
                except Exception:
                    pass
            time.sleep(15)  # Adjust based on Ollama's eviction timeout

    thread = threading.Thread(target=_keep_alive_loop, daemon=True)
    thread.start()
    print("[OLLAMA_CONFIG] Keep-alive thread started for models:", model_list)

# =============================================================================
# llama.cpp config changes:

The main practical differences to be aware of:
- Model names: Ollama uses names like qwen3:27b, llama.cpp uses whatever filename you loaded, often something like qwen3-27b-q4_k_m.gguf. You'd want to expose a LLAMA_CPP_MODEL config variable or read it from the /v1/models endpoint.
- Context window: llama.cpp sets n_ctx at server startup, not per-request, so num_ctx in the params has no effect. The server caps it. Make sure you start llama.cpp with --ctx-size 32768 to match.
- Stop tokens: llama.cpp handles them slightly differently for some models. If you see runaway output, the stop list may need model-specific tuning.
- check_ollama_available: update the boot printout in ollama_config.py to also report which backend is active, so you can see at startup which one won.
# =============================================================================

# In query_with_cpol in ollama_config.py.
# Add a backend selector at the top of the function:
# pythonLLAMA_CPP_URL = "http://localhost:8080/v1"  # llama.cpp default

def _detect_backend() -> str:
    """Check which inference backend is available."""
    if check_ollama_available():
        return 'ollama'
    try:
        urllib.request.urlopen(f"{LLAMA_CPP_URL}/models", timeout=2)
        return 'llamacpp'
    except Exception:
        return 'none'
Then in query_with_cpol, branch on backend:
pythonbackend = _detect_backend()

if backend == 'ollama':
    import ollama
    response = ollama.generate(
        model=params['model'],
        prompt=user_query,
        system=identity_prefix + params['system'] + tool_addendum,
        options=params['options']
    )
    result = response.response.strip() if hasattr(response, 'response') else ''

elif backend == 'llamacpp':
    import urllib.request, json
    payload = {
        "model": params['model'],
        "messages": [
            {"role": "system", "content": identity_prefix + params['system'] + tool_addendum},
            {"role": "user", "content": user_query}
        ],
        "temperature": params['options']['temperature'],
        "max_tokens": params['options']['num_predict'],
        "top_p": params['options']['top_p'],
        "repeat_penalty": params['options']['repeat_penalty'],
        "stop": params['options']['stop'],
    }
    req = urllib.request.Request(
        f"{LLAMA_CPP_URL}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    result = data['choices'][0]['message']['content'].strip()

else:
    result = "[LLM] No inference backend available"