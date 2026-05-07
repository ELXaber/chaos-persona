#!/usr/bin/env python3
"""
CAIOS Chat - Simple & Direct Version
"""

import ollama
import os
from typing import List, Dict

# Load the full CAIOS system prompt
def load_caios_prompt() -> str:
    try:
        with open("CAIOS.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Error: CAIOS.txt not found!")
        return "You are a helpful assistant."
    except Exception as e:
        print(f"Error reading CAIOS.txt: {e}")
        return "You are a helpful assistant."


def get_personalized_prompt() -> str:
    base = load_caios_prompt()
    return f"You are Andrew One.\n\n{base}"


def main():
    print("CAIOS Interactive Chat (Direct Ollama)")
    print("=" * 50)

    system_prompt = get_personalized_prompt()
    conversation = [{"role": "system", "content": system_prompt}]

    print("Andrew One is ready. Type 'exit' or 'quit' to end.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit", "q"):
            print("Goodbye.")
            break
        if not user_input:
            continue

        conversation.append({"role": "user", "content": user_input})

        print("Thinking...", end="", flush=True)

        try:
            response = ollama.chat(
                model="llama3.2:3b",          # Change to your bigger model later
                messages=conversation,
                options={
                    "temperature": 0.7,
                    "num_ctx": 8192
                }
            )
            reply = response['message']['content'].strip()
        except Exception as e:
            reply = f"[ERROR] {e}"

        print("\r" + " " * 20 + "\r", end="")   # Clear "Thinking..."
        print(f"Andrew: {reply}")

        conversation.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()