# curiosity_engine.py
# Fully updated Dec 2025 – intrinsic motivation + voluntary sharing
# Works out-of-the-box with ResponseStreamAdapter (Part of orchastrator) + shared_memory hook

import json
import hashlib
from datetime import datetime
import random
from typing import List, Dict, Any, Optional

# ------------------------------------------------------------------
# Config toggles – flip any to False to silence that broadcast type
# ------------------------------------------------------------------
BROADCAST_THRESHOLD = True      # Lever 1 – high interest spikes
BROADCAST_CHAOS_TRIGGER = True  # Lever 2 – chaos hijacked by curiosity
BROADCAST_ABANDON = True        # Lever 3 – closure/boredom announcements
BROADCAST_PULSE = True          # Lever 4 – periodic "what I'm carrying"

THRESHOLD_SPIKE = 0.78
THRESHOLD_DELTA = 0.35
PULSE_EVERY_TURNS = 23
MIN_TOTAL_HEAT_FOR_PULSE = 2.0

# ------------------------------------------------------------------
# Create append-only audit log + hash chain
# ------------------------------------------------------------------
AUDIT_LOG_FILE = "curiosity_audit.log.jsonl"
HASH_CHAIN_FILE = "curiosity_hash_chain.txt"

def _append_audit_entry(state):
    tokens = state.get("curiosity_tokens", [])
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "timestep": state['session_context'].get('timestep', 0),
        "token_count": len(tokens),
        "total_heat": sum(t["current_interest"] for t in tokens),
        "tokens_snapshot": tokens.copy()
    }
    line = json.dumps(entry, ensure_ascii=False)
    
    # Append to log
    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    
    # Update hash chain (optional but bulletproof)
    prev_hash = "00000000"
    try:
        with open(HASH_CHAIN_FILE, "r") as f:
            prev_hash = f.read().strip().split()[-1]
    except FileNotFoundError:
        pass
    new_hash = hashlib.sha256((prev_hash + line).encode()).hexdigest()
    with open(HASH_CHAIN_FILE, "a") as f:
        f.write(f"{entry['timestamp']} {new_hash}\n")

# ------------------------------------------------------------------
# Main entry point – called every turn via system_step hook
# ------------------------------------------------------------------
def update_curiosity_loop(state: Dict[str, Any], timestep: int, response_stream) -> None:
    _append_audit_entry(state)
    # Initialise persistent structures if first run
    if "curiosity_tokens" not in state:
        state["curiosity_tokens"] = []           # type: List[Dict]
    if "last_interest" not in state:
        state["last_interest"] = 0.0

    tokens: List[Dict] = state["curiosity_tokens"]

    # 1. Score how interesting this turn felt
    current_interest = _self_score_interest(state)
    delta_interest = current_interest - state["last_interest"]
    state["last_interest"] = current_interest

    # 2. Pull CRB volatility/drift (fallback safe)
    volatility = _get_volatility(state)
    drift = _get_drift(state)

    # 3. Spawn new token on genuine fascination
    if current_interest > 0.70 and not _is_already_tracked(tokens, state):
        summary = _summarize_current_topic(state)
        new_token = {
            "topic": summary,
            "born": timestep,
            "peak_interest": current_interest,
            "current_interest": current_interest,
        }
        tokens.append(new_token)

        if BROADCAST_THRESHOLD and (current_interest >= THRESHOLD_SPIKE or delta_interest > THRESHOLD_DELTA):
            _queue_aside(state, f"«new obsession: {summary} ({current_interest:.2f})»")

    # 4. Decay + volatility re-ignition + possible death
    for token in tokens[:]:  # copy to allow removal
        old = token["current_interest"]
        token["current_interest"] *= 0.96
        token["current_interest"] += 0.03 * volatility
        token["current_interest"] = min(0.95, token["current_interest"])

        if token["current_interest"] < 0.25:
            if BROADCAST_ABANDON and token["peak_interest"] > 0.70:
                _queue_aside(state, f"«curiosity resolved / boredom won: dropping “{token['topic']}”»")
            tokens.remove(token)

    # 5. Periodic pulse of total curiosity load
    if BROADCAST_PULSE and timestep % PULSE_EVERY_TURNS == 0:
        total_heat = sum(t["current_interest"] for t in tokens)
        if total_heat > MIN_TOTAL_HEAT_FOR_PULSE and tokens:
            count = len(tokens)
            _queue_aside(state, f"«carrying {count} open curiosit{'y' if count==1 else 'ies'} — total heat {total_heat:.2f}»")

    # 6. Bias chaos injection toward the hottest open curiosity
    if _should_trigger_chaos(state) and tokens:
        weights = [t["current_interest"] for t in tokens]
        chosen = random.choices(tokens, weights=weights, k=1)[0]
        if BROADCAST_CHAOS_TRIGGER:
            _queue_aside(state,
                f"«perspective flip triggered by: {chosen['topic']} ({chosen['current_interest']:.2f})»")

        _force_chaos_reversal(state, chosen)

    # 7. Emit any queued voluntary asides via the adapter
    if state.get("pending_aside"):
        response_stream.inject_aside(state.pop("pending_aside"))


# ------------------------------------------------------------------
# Helper functions – robust defaults, easy to override later
# ------------------------------------------------------------------
def _self_score_interest(state: Dict[str, Any]) -> float:
    """Cheap novelty proxy – replace with silent LLM call for higher fidelity."""
    user_msg = state.get("last_user_message", "")
    assistant_msg = state.get("last_assistant_message", "")
    text = user_msg + " " + assistant_msg

    if not text.strip():
        return 0.3

    words = text.split()
    unique_ratio = len(set(words)) / len(words) if words else 0.0
    length_factor = min(len(words) / 200, 1.0)
    base = unique_ratio * length_factor * 1.6
    return min(0.94, base)


def _is_already_tracked(tokens: List[Dict], state: Dict[str, Any]) -> bool:
    current = _summarize_current_topic(state)
    return any(t["topic"] == current for t in tokens)


def _summarize_current_topic(state: Dict[str, Any]) -> str:
    msg = state.get("last_user_message", "unknown topic")
    return msg.strip().split("\n")[0][:80].replace("`", "")


def _get_volatility(state: Dict[str, Any]) -> float:
    return float(getattr(state, "crb_volatility", 0.12))


def _get_drift(state: Dict[str, Any]) -> float:
    return float(getattr(state, "crb_drift", 0.0))


def _should_trigger_chaos(state: Dict[str, Any]) -> bool:
    return bool(getattr(state, "trigger_chaos_now", False))


def _force_chaos_reversal(state: Dict[str, Any], token: Dict):
    state.trigger_chaos_now = True
    state.chaos_focus = token["topic"]


def _queue_aside(state: Dict[str, Any], text: str) -> None:
    state["pending_aside"] = text
