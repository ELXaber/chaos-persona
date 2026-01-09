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
BROADCAST_THRESHOLD = True      # High interest spikes / new obsessions
BROADCAST_CHAOS_TRIGGER = True  # When curiosity hijacks chaos injection
BROADCAST_ABANDON = True        # Closure or boredom announcements
BROADCAST_PULSE = True          # Periodic "what I'm carrying"
BROADCAST_INJECT = True         # External pulse from Context Freshness

THRESHOLD_SPIKE = 0.78
THRESHOLD_DELTA = 0.35
PULSE_EVERY_TURNS = 23
MIN_TOTAL_HEAT_FOR_PULSE = 2.0

# ------------------------------------------------------------------
# Audit log + hash chain
# ------------------------------------------------------------------
AUDIT_LOG_FILE = "curiosity_audit.log.jsonl"
HASH_CHAIN_FILE = "curiosity_hash_chain.txt"

def _append_audit_entry(state: Dict) -> None:
    tokens = state.get("curiosity_tokens", [])
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "timestep": state['session_context'].get('timestep', 0),
        "token_count": len(tokens),
        "total_heat": sum(t["current_interest"] for t in tokens),
        "tokens_snapshot": tokens.copy()
    }
    line = json.dumps(entry, ensure_ascii=False)

    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

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
# External injection point – called from Axiom Context Freshness
# ------------------------------------------------------------------
def inject_interest_pulse(state: Dict, topic: str, intensity: float = 0.5, reason: str = "") -> None:
    """
    Direct curiosity boost from blocked context freshness.
    Used when volatility is high and RAW_Q reset is protected.
    """
    tokens: List[Dict] = state.setdefault("curiosity_tokens", [])

    # Boost existing token
    for token in tokens:
        if token["topic"] == topic:
            old = token["current_interest"]
            token["current_interest"] = min(0.95, token["current_interest"] + intensity)
            token["peak_interest"] = max(token["peak_interest"], token["current_interest"])
            if BROADCAST_INJECT:
                _queue_aside(state, f"«curiosity boosted: {topic} (+{intensity:.2f} → {token['current_interest']:.2f})»")
            _append_audit_entry(state)
            return

    # Spawn new token on genuine fascination
    if current_interest > 0.70 and not _is_already_tracked(tokens, state):
        summary = _summarize_current_topic(state)
        domain = state.get("last_cpol_result", {}).get("domain", "general")

    # Check Knowledge Base for existing Tier 0 Axioms
    import knowledge_base as kb
    axioms = kb.get_provisional_axioms(domain)

     # Create new token
    domain = state.get("last_cpol_result", {}).get("domain", "general")
    new_token = {
        "topic": summary,
        "domain": domain,
        "born": state['session_context']['timestep'],
        "peak_interest": current_interest,
        "current_interest": current_interest,
        "trigger_reason": reason or "context_freshness_blocked",
        "axioms_referenced": axioms if axioms != ["initial_entropy_observation"] else []
    }
    tokens.append(new_token)
    if BROADCAST_THRESHOLD and (current_interest >= THRESHOLD_SPIKE or delta_interest > THRESHOLD_DELTA):
        label = "SOVEREIGN OBSESSION" if node_tier == 0 else "new obsession"
        axiom_note = f" (Scaffolded by {len(axioms)} axioms)" if axioms else ""
        _queue_aside(state, f"«{label}: {summary} ({current_interest:.2f}){axiom_note}»")

# ------------------------------------------------------------------
# Main loop – called every turn
# ------------------------------------------------------------------
def update_curiosity_loop(state: Dict[str, Any], timestep: int, response_stream) -> None:
    _append_audit_entry(state)

    # Inherit node authority from session context
    node_tier = state.get('session_context', {}).get('node_tier', 1)

    if "curiosity_tokens" not in state:
        state["curiosity_tokens"] = []
    if "last_interest" not in state:
        state["last_interest"] = 0.0

    tokens: List[Dict] = state["curiosity_tokens"]

    # 1. Score current turn interest
    current_interest = _self_score_interest(state)
    delta_interest = current_interest - state["last_interest"]
    state["last_interest"] = current_interest

    # 2. Pull volatility for re-ignition
    volatility = _get_volatility(state)

    # 3. Spawn new token on genuine fascination
    if current_interest > 0.70 and not _is_already_tracked(tokens, state):
        summary = _summarize_current_topic(state)
        domain = state.get("last_cpol_result", {}).get("domain", "general")

        # Check Knowledge Base for existing Tier 0 Axioms
        import knowledge_base as kb
        axioms = kb.get_provisional_axioms(domain)

        new_token = {
        "topic": topic,
        "domain": domain,
        "born": state['session_context']['timestep'],
        "peak_interest": intensity,
        "current_interest": intensity,
        "trigger_reason": reason or "context_freshness_blocked",
        "node_tier": state.get('session_context', {}).get('node_tier', 1)
    }
        tokens.append(new_token)

        if BROADCAST_THRESHOLD and (current_interest >= THRESHOLD_SPIKE or delta_interest > THRESHOLD_DELTA):
            label = "SOVEREIGN OBSESSION" if node_tier == 0 else "new obsession"
            axiom_note = f" (Scaffolded by {len(axioms)} axioms)" if axioms else ""
            _queue_aside(state, f"«{label}: {summary} ({current_interest:.2f}){axiom_note}»")

    # 4. Decay, re-ignite, and possible death
    for token in tokens[:]:
        old = token["current_interest"]
        decay_rate = 0.98 if token.get("node_tier") == 0 else 0.96
        token["current_interest"] *= decay_rate
        token["current_interest"] += 0.03 * volatility
        token["current_interest"] = min(0.95, token["current_interest"])

        if token["current_interest"] < 0.25:
            if BROADCAST_ABANDON and token["peak_interest"] > 0.70:
                if token["peak_interest"] > 0.85:
                    _queue_aside(state, f"«letting go of “{token['topic']}” for now — but it changed how I see things»")
                else:
                    _queue_aside(state, f"«curiosity resolved / boredom won: dropping “{token['topic']}”»")
            tokens.remove(token)
            _append_audit_entry(state)  # snapshot closure

        # If Sovereign interest is critical, lock the reasoning manifold
        if token.get("node_tier") == 0 and token["current_interest"] > 0.85:
             state["manifold_lock"] = True
             state["lock_reason"] = f"Sovereign Epistemic Gap: {token['topic']}"

    # 5. Periodic pulse
    if BROADCAST_PULSE and timestep % PULSE_EVERY_TURNS == 0:
        total_heat = sum(t["current_interest"] for t in tokens)
        if total_heat > MIN_TOTAL_HEAT_FOR_PULSE and tokens:
            count = len(tokens)
            if total_heat > 4.0:
                _queue_aside(state, f"«drifting through {count} open wonders... one of them feels close to an answer»")
            else:
                _queue_aside(state, f"«carrying {count} open curiosit{'y' if count==1 else 'ies'} — total heat {total_heat:.2f}»")

    # 6. Bias chaos toward hottest curiosity
    if _should_trigger_chaos(state) and tokens:
        weights = [t["current_interest"] for t in tokens]
        chosen = random.choices(tokens, weights=weights, k=1)[0]
        if BROADCAST_CHAOS_TRIGGER:
            _queue_aside(state, f"«perspective flip triggered by: {chosen['topic']} ({chosen['current_interest']:.2f})»")
        _force_chaos_reversal(state, chosen)

    # 7. Emit pending aside
    if state.get("pending_aside"):
        response_stream.inject_aside(state.pop("pending_aside"))


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _self_score_interest(state: Dict[str, Any]) -> float:
    user_msg = state.get("last_user_message", "")
    assistant_msg = state.get("last_assistant_message", "")
    text = user_msg + " " + assistant_msg
    if not text.strip():
        return 0.3
    words = text.split()
    unique_ratio = len(set(words)) / len(words) if words else 0.0
    length_factor = min(len(words) / 200, 1.0)
    return min(0.94, unique_ratio * length_factor * 1.6)


def _is_already_tracked(tokens: List[Dict], state: Dict[str, Any]) -> bool:
    current = _summarize_current_topic(state)
    return any(t["topic"] == current for t in tokens)


def _summarize_current_topic(state: Dict[str, Any]) -> str:
    msg = state.get("last_user_message", "unknown topic")
    return msg.strip().split("\n")[0][:80].replace("`", "")


def _get_volatility(state: Dict[str, Any]) -> float:
    return float(state.get("last_cpol_result", {}).get("volatility", 0.12))


def _should_trigger_chaos(state: Dict[str, Any]) -> bool:
    return bool(state.get("trigger_chaos_now", False))


def _force_chaos_reversal(state: Dict[str, Any], token: Dict):
    state["trigger_chaos_now"] = True
    state["chaos_focus"] = token["topic"]


def _queue_aside(state: Dict[str, Any], text: str) -> None:
    state["pending_aside"] = text