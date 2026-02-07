#!/usr/bin/env python3
"""
CAIOS Inference Wrapper
Simple interactive chat that uses CAIOS.txt as the system prompt and any model client initialized by master_init.py
"""

import os
import json
import sys
from typing import Dict, Any, List

# =============================================================================
# Load shared memory (created by master_init.py)
# =============================================================================

SHARED_MEMORY_FILE = "shared_memory.json"  # optional - if you want to save/load

def load_shared_memory() -> Dict[str, Any]:
    """Load shared memory from file or return empty dict."""
    if os.path.exists(SHARED_MEMORY_FILE):
        try:
            with open(SHARED_MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load shared_memory.json: {e}")
    return {}

shared_memory = load_shared_memory()

# =============================================================================
# Load CAIOS system prompt
# =============================================================================

def load_caios_prompt() -> str:
    """Read CAIOS.txt as the system prompt."""
    try:
        with open("CAIOS.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Error: CAIOS.txt not found in current directory.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CAIOS.txt: {e}")
        sys.exit(1)

system_prompt = load_caios_prompt()

# =============================================================================
# Client selection & chat function
# =============================================================================

def select_client(clients: Dict[str, Any]) -> tuple:
    """Let user choose a model from available clients."""
    if not clients:
        print("No API clients available. Run master_init.py first.")
        sys.exit(1)

    print("\nAvailable models:")
    options = list(clients.keys())
    for i, provider in enumerate(options, 1):
        print(f"  {i}. {provider.upper()}")

    while True:
        try:
            choice = int(input("\nSelect model (number): "))
            if 1 <= choice <= len(options):
                provider = options[choice - 1]
                return provider, clients[provider]
            else:
                print(f"Please enter a number between 1 and {len(options)}.")
        except ValueError:
            print("Please enter a valid number.")


def chat_with_model(provider: str, client: Any, messages: List[Dict[str, str]]) -> str:
    """Send chat request to selected model."""
    try:
        if provider == "openai":
            response = client.chat.completions.create(
                model="gpt-4o",  # change to your preferred model
                messages=messages,
                temperature=0.7,
                max_tokens=2048
            )
            return response.choices[0].message.content.strip()

        elif provider == "anthropic":
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",  # or haiku/opus
                max_tokens=2048,
                messages=messages,
                temperature=0.7
            )
            return response.content[0].text.strip()

        elif provider == "xai":
            response = client.chat.completions.create(
                model="grok-beta",
                messages=messages,
                temperature=0.7,
                max_tokens=2048
            )
            return response.choices[0].message.content.strip()

        elif provider == "google":
            model = client.GenerativeModel("gemini-1.5-pro")  # or gemini-pro
            response = model.generate_content(messages[-1]["content"])  # Gemini API is different
            return response.text.strip()

        else:
            return f"Unsupported provider: {provider}"

    except Exception as e:
        return f"Error during API call: {str(e)}"


# =============================================================================
# Main interactive loop
# =============================================================================

def main():
    print("CAIOS Interactive Chat")
    print("=====================")
    print("Type your message and press Enter. Type 'exit' or 'quit' to end.\n")

    clients = shared_memory.get("api_clients", {})
    if not clients:
        print("No API clients found in shared memory.")
        print("Run 'python master_init.py' first to initialize clients.")
        return

    provider, client = select_client(clients)
    print(f"\nUsing: {provider.upper()}")

    # Initialize conversation with CAIOS system prompt
    conversation = [{"role": "system", "content": system_prompt}]

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("exit", "quit", "q"):
            print("Goodbye.")
            break

        if not user_input:
            continue

        # Add user message
        conversation.append({"role": "user", "content": user_input})

        print("\nThinking...", end="", flush=True)

        # Get response from model
        response_text = chat_with_model(provider, client, conversation)

        print("\r" + " " * 20 + "\r", end="")  # clear "Thinking..."
        print(f"CAIOS: {response_text}")

        # Add assistant response to history
        conversation.append({"role": "assistant", "content": response_text})


if __name__ == "__main__":
    main()
