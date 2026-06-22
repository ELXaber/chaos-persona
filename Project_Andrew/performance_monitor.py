import requests
import time
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3.6:27b"
PROMPT = "Write a short story about a robot in 100 words."

payload = {
    "model": MODEL,
    "prompt": PROMPT,
    "stream": False,
    "options": {
        "num_ctx": 512,
        "num_predict": 150,
        "temperature": 0.7
    }
}

start = time.time()
print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Sending request...")

try:
    r = requests.post(OLLAMA_URL, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    elapsed = time.time() - start

    tokens = data.get('eval_count', 0)
    duration = data.get('total_duration', 0) / 1e9

    print(f"Tokens generated: {tokens}")
    print(f"Total duration (internal): {duration:.2f}s")
    print(f"Total duration (raw): {elapsed:.2f}s")
    print(f"Tokens/sec (internal): {tokens / duration:.2f}")
    print(f"Tokens/sec (raw): {tokens / elapsed:.2f}")

except requests.exceptions.Timeout:
    print("ERROR: Request timed out after 30s")
except Exception as e:
    print(f"ERROR: {e}")