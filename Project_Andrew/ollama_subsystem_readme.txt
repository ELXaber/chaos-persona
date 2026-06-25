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