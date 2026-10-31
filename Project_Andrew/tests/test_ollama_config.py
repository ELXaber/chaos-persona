#V10282026
# test_llm_config.py

import llm_config

print("Testing llm_config.py...")
print(f"Ollama available: {llm_config.check_ollama_available()}")
print(f"Node tier: {llm_config.NODE_TIER}")
print(f"System ID: {llm_config.SYSTEM_ID}")

# Test params with different CPOL states
params_stable = llm_config.get_cpol_ollama_params(
    contradiction_density=0.1  # Low contradiction
)
print(f"Stable temp: {params_stable['options']['temperature']:.2f}")

params_paradox = llm_config.get_cpol_ollama_params(
    contradiction_density=0.9  # High contradiction
)
print(f"Paradox temp: {params_paradox['options']['temperature']:.2f}")
