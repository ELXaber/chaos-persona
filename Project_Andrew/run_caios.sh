#!/bin/bash
echo "Starting CAIOS..."

if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Please install it."
    exit 1
fi

if [ ! -f "system_identity.json" ]; then
    echo "First boot - running master_init..."
    python3 master_init.py
fi

python3 caios_chat.py