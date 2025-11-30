# interface.py — your personal OS dashboard
import json
import os
from typing import Dict, Any
from agents import *  # auto-imports everything in /agents/

# Global personality matrix (shared or per-agent — your choice)
PERSONALITY = {
    "professional": 8,
    "snarky":       0,
    "empathetic":   5,
    "concise":      7,
    "creative":     3,
    "cautious":     9
}

# Available agents — auto-discovered
AGENTS = {
    "day":      day_planner.day_planner_agent,
    "fitness":  fitness_coach.fitness_agent,
    "math":     math_researcher.math_agent,
    # ... all others appear automatically
}

def caios(
    message: str,
    agent: str = "day",
    show_reasoning: bool = False,
    show_cot: bool = False,
    personality_override: Dict[str, int] = None
) -> str:
    """
    One function to rule your entire mind OS.
    """
    if agent not in AGENTS:
        return f"Agent '{agent}' not found. Try: {', '.join(AGENTS)}"

    # Apply personality (global or override)
    current_persona = PERSONALITY.copy()
    if personality_override:
        current_persona.update(personality_override)

    # Special CAIOS commands (always available)
    msg = message.lower()
    if msg.startswith("set "):
        key, val = msg[4:].split()[0], int(msg.split()[1])
        PERSONALITY[key] = val
        return f"Personality '{key}' → {val}"

    if msg == "show personality":
        return "\n".join(f"{k}: {v}/10" for k, v in PERSONALITY.items())

    if msg == "show agents":
        return f"Available agents: {', '.join(AGENTS)}"

    if msg == "show reasoning":
        show_reasoning = True
    if msg == "show cot":
        show_cot = True

    # Normal agent call
    response = AGENTS[agent](
        message,
        personality=current_persona,
        show_reasoning=show_reasoning,
        show_cot=show_cot
    )
    return response
