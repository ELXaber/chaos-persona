# curiosity_engine.py
# Drop-in intrinsic motivation + voluntary sharing module
# Dec 2025 – minimal, no external deps

import random
from typing import List, Dict, Any

# ------------------------------------------------------------------
# Config toggles (flip any to False to disable that broadcast mode)
# ------------------------------------------------------------------
BROADCAST_THRESHOLD = True      # Lever 1 – high interest spikes
BROADCAST_CHAOS_TRIGGER = True  # Lever 2 – when curiosity hijacks chaos
BROADCAST_ABANDON = True        # Lever 3 – closure announcements
BROADCAST_PULSE = True          # Lever 4 – periodic "what I'm carrying"

THRESHOLD_SPIKE = 0.78
THRESHOLD_DELTA = 0.35
PULSE_EVERY_TURNS = 23
MIN_TOTAL_HEAT_FOR_PULSE = 2.0

# ------------------------------------------------------------------
# Core curiosity loop – called once per turn (post_turn hook)
# ------------------------------------------------------------------
def update_curiosity_loop(state: Dict[str, Any], timestep: int, response_stream) -> None:
    if not hasattr(state, "curiosity_tokens"):
        state.curiosity_tokens: List[Dict] = []
    if not hasattr(state, "last_interest"):
        state.last_interest = 0.0

    tokens: List[Dict] = state.curiosity_tokens

    # 1. Score how interesting this turn felt to the system
    current_interest = _self_score_interest(state, response_stream)
    state.last_interest = current_interest

    # 2. Volatility & drift from CRB (assume these functions exist somewhere)
    volatility = _get_volatility(state)
    drift = _get_drift(state)

    # 3. Create new token if something is genuinely fascinating
    if current_interest > 0.70 and not _is_already_tracked(tokens, state):
        summary = _summarize_current_topic(state)
        new_token = {
            "topic": summary,
            "born": timestep,
            "peak_interest": current_interest,
            "current_interest": current_interest,
        }
        tokens.append(new_token)

        if BROADCAST_THRESHOLD and (current_interest >= THRESHOLD_SPIKE or
                                    current_interest - state.last_interest > THRESHOLD_DELTA):
            _queue_aside(state, f"«new obsession: {summary} ({current_interest:.2f})»")

    # 4. Decay + volatility re-ignition + possible death
    for token in tokens[:]:  # copy because we may remove
        token["current_interest"] *= 0.96
        token["current_interest"] += 0.03 * volatility
        token["current_interest"] = min(0.95, token["current_interest"])  # cap

        if token["current_interest"] < 0.25:
            if BROADCAST_ABANDON and token["peak_interest"] > 0.7:
                _queue_aside(state, f"«curiosity resolved / boredom won: dropping “{token['topic']}”»")
            tokens.remove(token)

    # 5. Periodic pulse of total load
    if BROADCAST_PULSE and timestep % PULSE_EVERY_TURNS == 0:
        total_heat = sum(t["current_interest"] for t in tokens)
        if total_heat > MIN_TOTAL_HEAT_FOR_PULSE:
            _queue_aside(state, f"«carrying {len(tokens)} open curiosities — total heat {total_heat:.2f}»")

    # 6. Bias chaos injection toward open curiosities
    if _should_trigger_chaos(state) and tokens:
        weights = [t["current_interest"] for t in tokens]
        chosen = random.choices(tokens, weights=weights, k=1)[0]
        _queue_aside(state, f"«perspective flip triggered by: {chosen['topic']} ({chosen['current_interest']:.2f})»") if BROADCAST_CHAOS_TRIGGER else None

        # Actually force the reversal / goal spawn (orchestrator-specific call)
        _force_chaos_reversal(state, chosen)

    # 7. Finally inject any queued asides into the outgoing response
    if state.get("pending_aside"):
        response_stream.inject_aside(state.pop("pending_aside"))


# ------------------------------------------------------------------
# Tiny helpers (replace with your real implementations if needed)
# ------------------------------------------------------------------
def _self_score_interest(state, response_stream) -> float:
    # Very cheap proxy – replace with silent LLM call if you want higher fidelity
    last_user = state.get("last_user_message", "")
    last_response = state.get("last_assistant_message", "")
    novelty_proxy = len(set(last_response.split())) / max(len(last_response.split()), 1)
    return min(0.92, novelty_proxy * 1.4)

def _is_already_tracked(tokens, state) -> bool:
    current_summary = _summarize_current_topic(state)
    return any(t["topic"] == current_summary for t in tokens)

def _summarize_current_topic(state) -> str:
    # Simple fallback – grab last user message title or first 40 chars
    msg = state.get("last_user_message", "unknown topic")
    return msg.strip().split("\n")[0][:60]

def _get_volatility(state) -> float:
    return getattr(state, "crb_volatility", 0.1)

def _get_drift(state) -> float:
    return getattr(state, "crb_drift", 0.0)

def _should_trigger_chaos(state) -> bool:
    # Hook into your existing chaos triggers
    return getattr(state, "trigger_chaos_now", False)

def _force_chaos_reversal(state, token):
    # Example – whatever your orchestrator uses to flip idx_p or spawn goal
    state.trigger_chaos_now = True
    state.chaos_focus = token["topic"]

def _queue_aside(state, text: str):
    state.pending_aside = text
