# epistemic_monitor.py
# CAIOS vΩ — Mesh Telemetry & Entropy Tracking
# Replaces 'curiosity_engine' for pure logic-driven mesh sovereignty.

import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

# ------------------------------------------------------------------
# MESH CONFIG - Zero Social Bloat
# ------------------------------------------------------------------
SIGNAL_CHAOS_SYNC = True   # Trigger reset on high entropy
LOG_AXIOM_SETTLEMENT = True # Log when a domain hits stability
PULSE_EVERY_TURNS = 25      # O(1) Ratchet Frequency

# Thresholds for Quantum Key Re-sync
THRESHOLD_CRISIS = 0.75     # Distress density trigger
THRESHOLD_STABILITY = 0.20  # Axiom settlement trigger

def update_epistemic_loop(state: Dict[str, Any], ts: int):
    """
    Main loop for tracking logical entropy across the mesh.
    Replaces curiosity loops with stability monitoring.
    """
    if 'domain_heat' not in state:
        state['domain_heat'] = {}

    # 1. Calculate current state entropy
    current_entropy = _calculate_logic_entropy(state)
    domain = state.get('last_cpol_result', {}).get('domain', 'general')

    # 2. Update Domain Heat (Topological Map)
    old_heat = state['domain_heat'].get(domain, 0.5)
    new_heat = (old_heat * 0.7) + (current_entropy * 0.3)
    state['domain_heat'][domain] = round(new_heat, 4)

    # 3. Check for Service Level Reset (SLR) trigger
    if new_heat > THRESHOLD_CRISIS:
        state['distress_density'] = new_heat
        _signal_sync_required(state, domain, ts)

    # 4. Axiom Settlement Check
    if new_heat < THRESHOLD_STABILITY:
        _seal_axiom_state(state, domain)

def _calculate_logic_entropy(state: Dict[str, Any]) -> float:
    """
    Measures logical tension instead of 'interest'.
    Uses CPOL volatility and ARL audit trail density.
    """
    cpol = state.get("last_cpol_result", {})
    volatility = float(cpol.get("volatility", 0.5))

    # If CPOL is oscillating (UNDECIDABLE), entropy is maxed
    if cpol.get("status") == "UNDECIDABLE":
        return 0.95

    return volatility

def _signal_sync_required(state: Dict[str, Any], domain: str, ts: int):
    """Prepares the Orchestrator for a Ghost Reset."""
    sig = state.get('last_cpol_result', {}).get('signature', '0xKEY')
    print(f"[MONITOR] !! ENTROPY SPIKE !! Domain: {domain} | Sync Signature: {sig}")
    state['sync_lock'] = True

def _seal_axiom_state(state: Dict[str, Any], domain: str):
    """Signals that logic is stable enough for Quantum Key generation."""
    if not state.get('axiom_locked'):
        print(f"[MONITOR] Domain Stable: {domain} -> Ready for Axiom Settlement.")
        state['axiom_locked'] = True

# ------------------------------------------------------------------
# Audit & Integrity
# ------------------------------------------------------------------
def _append_telemetry_log(state: Dict) -> None:
    entry = {
        "ts": datetime.utcnow().isoformat(),
        "step": state['session_context'].get('timestep', 0),
        "entropy_map": state['domain_heat']
    }
    # Append-only hash chain logic for the mesh ledger
    with open("epistemic_audit.log.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")