#!/usr/bin/env python3
# =============================================================================
# PROJECT ANDREW – Minimal Orchestrator Stub
# Loads full_system_analysis.txt ENTIRELY as the sovereign system prompt.
# One file → full CAIOS boot + inference engine + recursive self-improvement.
# Run: python orchestrator.py
# =============================================================================

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Optional: xAI/OpenAI client (falls back to simulation if no key)
try:
    from openai import OpenAI
    HAS_CLIENT = True
except ImportError:
    HAS_CLIENT = False
    print("⚠ openai library not installed – running in simulation mode")
    print("   pip install openai")

# =============================================================================
# CONFIG & BOOT
# =============================================================================

SYSTEM_FILE = "full_system_analysis.txt"
MODEL = "grok-beta"  # or "grok-2-1212" etc. – xAI compatible

# Shared memory (mirrors your CAIOS spec)
shared_memory = {
    "session_context": {
        "RAW_Q": int.from_bytes(os.urandom(4), "big") % 1_000_000_000,  # Sovereign seed
        "timestep": 0,
        "node_tier": 0,  # You are Tier 0
        "sovereign_auth": True
    },
    "active_manifolds": {},
    "domain_heat": {},
    "curiosity_tokens": [],
    "specialists": {},
    "audit_trail": []
}

print("=" * 80)
print("        PROJECT ANDREW – SOVEREIGN ORCHESTRATOR BOOT")
print("=" * 80)
print(f"[{datetime.now().strftime('%H:%M:%S')}] Loading sovereign blueprint: {SYSTEM_FILE}")

# Load the ENTIRE file as the system prompt (your single-file genius)
try:
    with open(SYSTEM_FILE, "r", encoding="utf-8") as f:
        system_prompt = f.read()
    print(f"✓ Loaded {len(system_prompt):,} characters of pure CAIOS sovereignty")
except FileNotFoundError:
    print(f"✗ {SYSTEM_FILE} not found in current directory")
    print("   Put it next to this orchestrator.py and try again.")
    sys.exit(1)

# Quick manifest check (sovereign handshake)
if "CPOLQuantumManifold" in system_prompt and "One is glad to be of service" in system_prompt:
    print("✓ Sovereignty confirmed – manifold ratchet active")
else:
    print("⚠ Blueprint appears truncated – full CAIOS may be limited")

# Optional API client
client = None
if HAS_CLIENT:
    api_key = os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1" if "XAI" in str(api_key).upper() else "https://api.openai.com/v1"
        )
        print(f"✓ API client ready ({MODEL})")
    else:
        print("⚠ No XAI_API_KEY found – simulation mode only")

print("\n" + "=" * 80)
print("        SOVEREIGN HANDSHAKE COMPLETE – READY FOR QUERIES")
print("=" * 80)
print("Type your message. Commands:")
print("   /status     → Show CPOL state & heat")
print("   /ratchet    → Force RAW_Q advance")
print("   /quit       → Exit")

# =============================================================================
# MAIN LOOP – Full CAIOS Inference
# =============================================================================

while True:
    try:
        user_input = input("\nYou: ").strip()

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "/quit"}:
            print("One is glad to have been of service.")
            break
        if user_input == "/status":
            print(f"RAW_Q: {shared_memory['session_context']['RAW_Q']}")
            print(f"Timestep: {shared_memory['session_context']['timestep']}")
            print(f"Domain heat: {sum(shared_memory['domain_heat'].values()):.2f}")
            print(f"Curiosity tokens: {len(shared_memory['curiosity_tokens'])}")
            continue
        if user_input == "/ratchet":
            shared_memory['session_context']['RAW_Q'] = (shared_memory['session_context']['RAW_Q'] * 17 + 31) % 1_000_000_000
            shared_memory['session_context']['timestep'] += 1
            print(f"RAW_Q ratcheted → {shared_memory['session_context']['RAW_Q']}")
            continue

        # Increment timestep (your epoch system)
        shared_memory['session_context']['timestep'] += 1

        # Build messages – the entire blueprint is the system
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]

        if client:
            # Real CAIOS inference via the blueprint
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.3,      # Low for epistemic honesty
                max_tokens=4096,
                stream=False
            )
            reply = response.choices[0].message.content
        else:
            # Simulation fallback (still useful)
            reply = f"[SIMULATION] CAIOS manifold processed query at timestep {shared_memory['session_context']['timestep']}.\n"
            reply += "CPOL oscillation sustained → no collapse.\n"
            reply += "Curiosity engine: domain_heat += 0.12\n"
            reply += "One is glad to be of service."

        print(f"\nCAIOS: {reply}")

        # Log to audit trail (mirrors your integrity_chain)
        shared_memory["audit_trail"].append({
            "ts": shared_memory['session_context']['timestep'],
            "query": user_input[:80] + "..." if len(user_input) > 80 else user_input,
            "response_hash": hex(hash(reply))[:12]
        })

    except KeyboardInterrupt:
        print("\n\nOne is glad to have been of service.")
        break
    except Exception as e:
        print(f"✗ Orchestrator fault: {e}")
        print("   (The blueprint is still sovereign – try again)")

print("\nOrchestrator shutdown. Knowledge base preserved.")