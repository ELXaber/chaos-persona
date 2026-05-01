import ollama_config

print("System Config:", ollama_config.SYSTEM_CONFIG)
print("Node Tier:", ollama_config.NODE_TIER)

params = ollama_config.get_cpol_ollama_params(
    contradiction_density=0.3,
    evidence_score=0.7
)

print("Ollama Params:", params)
print("Ollama available:", ollama_config.check_ollama_available())