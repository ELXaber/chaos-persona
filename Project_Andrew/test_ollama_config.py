#V03122026
# test_ollama_config.py

import ollama_config

print("Testing ollama_config.py...")
print(f"Ollama available: {ollama_config.check_ollama_available()}")
print(f"Node tier: {ollama_config.NODE_TIER}")
print(f"System ID: {ollama_config.SYSTEM_ID}")

# Test params with different CPOL states
params_stable = ollama_config.get_cpol_ollama_params(
    contradiction_density=0.1  # Low contradiction
)
print(f"Stable temp: {params_stable['options']['temperature']:.2f}")

params_paradox = ollama_config.get_cpol_ollama_params(
    contradiction_density=0.9  # High contradiction
)
print(f"Paradox temp: {params_paradox['options']['temperature']:.2f}")