import ollama
import sys

print(f"Python version: {sys.version}")
print(f"Ollama module location: {ollama.__file__}")

# Check if think is supported by testing the generate call
try:
    response = ollama.generate(
        model="qwen3.6:27b",
        prompt="What is 17 * 23? Show your work.",
        options={
            "num_predict": 512,
            "think": True
        }
    )
    print("\n--- Full Response Object ---")
    print(response)

    print("\n--- Response Text ---")
    print(response.get('response', 'No response'))

    # Check for thinking trace (it might be hidden in the object)
    if hasattr(response, 'thinking'):
        print("\n--- Thinking Trace ---")
        print(response.thinking)
    else:
        print("\nNo 'thinking' attribute found in response object.")
        print(f"Available keys: {list(response.keys()) if isinstance(response, dict) else dir(response)}")

except Exception as e:
    print(f"Error: {e}")