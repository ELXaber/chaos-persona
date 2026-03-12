Any subsystem that needs to call Ollama:
python# In a specialist or subsystem:

from paradox_oscillator import ParadoxOscillator
import ollama_config
import requests

def query_with_cpol(user_query: str) -> str:
    """
    Query Ollama with CPOL-tuned parameters.
    """
    # Get live CPOL state
    oscillator = ParadoxOscillator()
    contradiction_density = oscillator.detect_contradiction(user_query)
    evidence_score = 0.5  # Replace with actual evidence analysis
    
    # Get Ollama params (includes CAIOS.txt system prompt)
    params = ollama_config.get_cpol_ollama_params(
        contradiction_density=contradiction_density,
        evidence_score=evidence_score
    )

    # Make request with CPOL-tuned params
    response = requests.post(
        ollama_config.OLLAMA_ENDPOINT,
        json={
            **params,
            "prompt": user_query,
            "stream": False
        }
    )

    return response.json()['response']