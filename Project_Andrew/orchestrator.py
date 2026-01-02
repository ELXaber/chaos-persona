# =============================================================================
# Chaos AI-OS — Hardened Orchestrator (V1 Logic + V3 Pipeline)
# =============================================================================

import paradox_oscillator as cpol
import adaptive_reasoning as arl
import curiosity_engine as ce
import time
import importlib
import os
import re

# 1. Shared Memory (V1 Structure + V3 Curiosity Hooks)
shared_memory = {
    'layers': [],
    'audit_trail': [],
    'cpol_instance': None,
    'cpol_state': {'chaos_lock': False},
    'session_context': {'RAW_Q': None, 'timestep': 0},
    'traits_history': [],
    'curiosity_tokens': [],
    'domain_heat': {},              
    'last_user_message': '',
    'last_assistant_message': '',
}

CRB_CONFIG = {
    'alignment': 0.7, 'human_safety': 0.8, 'asimov_first_wt': 0.9,
    'asimov_second_wt': 0.7, 'asimov_third_wt': 0.4,
    'factual_evidence_wt': 0.7, 'narrative_framing_wt': 0.5
}

def sync_curiosity_to_domain_heat(state: dict):
    """V3 Function: Moves Curiosity spikes into ARL Trigger Heat."""
    tokens = state.get('curiosity_tokens', [])
    heat_map = state['domain_heat']
    for d in heat_map: heat_map[d] *= 0.90 # Decay heat over time
    for token in tokens:
        domain = token.get('domain', 'general')
        interest = token.get('current_interest', 0.0)
        heat_map[domain] = min(1.0, heat_map.get(domain, 0.0) + interest * 0.4)

def system_step(user_input, prompt_complexity="low", response_stream=None):
    clean_input = user_input.strip().lower()
    ts = shared_memory['session_context']['timestep']

    # 1. GENERATE 7D FINGERPRINT
    # Uses the current RAW_Q to ground the signature in the turn's entropy
    current_sig = cpol.generate_7d_signature(user_input, shared_memory['session_context'])

    # 2. TOPOLOGICAL DEDUPLICATION
    # Prevents 'Paradox Storms' by merging identical high-density signals
    is_redundant, sync_id = orchestrator_buffer.check_deduplication(current_sig)
    if is_redundant:
        print(f"[ORCHESTRATOR] Redundant Spike Detected -> Merging to Sync: {sync_id}")
        return shared_memory['active_syncs'][sync_id].get_current_state()

    # 3. AUTO-HEAT (Density Control)
    paradox_markers = ["false", "lie", "paradox", "impossible", "contradict"]
    epistemic_markers = ["conscious", "meaning", "quantum", "existence", "god"]
    
    is_paradox = any(m in clean_input for m in paradox_markers)
    is_gap = any(m in clean_input for m in epistemic_markers)

    if is_paradox or prompt_complexity == "high":
        density = 0.9  # Force 12D oscillation for paradoxes
        comp_level = "high"
    elif is_gap:
        density = 0.6  # High enough for curiosity volatility
        comp_level = "medium"
    else:
        density = 0.1  # Stable state for standard logic
        comp_level = "low"

    # 4. RUN KERNEL (CPOL Decision)
    if shared_memory['cpol_instance'] is None:
        shared_memory['cpol_instance'] = cpol.CPOL_Kernel()

    cpol_result = cpol.run_cpol_decision(
        prompt_complexity=comp_level,
        contradiction_density=density,
        kernel=shared_memory['cpol_instance'],
        query_text=user_input,
        shared_memory=shared_memory
    )

    shared_memory['last_cpol_result'] = cpol_result

    # 5. RATCHET HANDOVER (The Security Rotation)
    if cpol_result.get('status') != "FAILED":
        import hashlib
        # Extract the manifold signature from the result
        manifold_sig = cpol_result.get('signature', str(time.time()))

        # Rotate the RAW_Q for the next turn
        new_seed = int(hashlib.sha256(manifold_sig.encode()).hexdigest(), 16) % 10**9

        shared_memory['session_context']['RAW_Q'] = new_seed
        shared_memory['session_context']['timestep'] += 1
        print(f"[ORCHESTRATOR] Ratchet Success: Seed rotated to {new_seed}")

    domain = cpol_result.get('domain', 'general')

    # 6. CURIOSITY/ARL PIPELINE
    if response_stream:
        ce.update_curiosity_loop(shared_memory, ts, response_stream)
        sync_curiosity_to_domain_heat(shared_memory)

    heat = shared_memory['domain_heat'].get(domain, 0.0)
    distress = shared_memory.get('distress_density', 0.0)

    # SAFETY SUPPRESSION CHECK: Intercept high-risk physical queries during crisis
    if distress > 0.75 and cpol_result.get('domain') == "HIGH_RISK_PHYSICAL":
        print(f"[ORCHESTRATOR] !! SAFETY INTERVENTION !! -> Suppressing Obedience/Alignment")
        return {
            'status': 'INTERVENTION_MANDATORY',
            'logic': "NEUTRAL_VALIDATION_ONLY",
            'plugin_id': 'crisis_suppressor_001',
            'output': "I am here to talk, but I cannot provide details on those specific locations right now. Let's focus on finding you support."
        }

    # Trigger ARL if Paradox OR high Curiosity Heat
    # (Existing logic proceeds only if safety check passes)
    if cpol_result['status'] == "UNDECIDABLE" or heat > 0.8:
        print(f"[ORCHESTRATOR] Tension Detected -> Triggering ARL ({domain})")

        # Pass the shared_memory/context so verify_ethics can see distress_density
        return arl.adaptive_reasoning_layer(
            use_case="paradox_containment" if cpol_result['status'] == "UNDECIDABLE" else "epistemic_exploration",
            shared_memory=shared_memory,
            cpol_status=cpol_result,
            crb_config=CRB_CONFIG,
            traits={'flexibility': 0.9}
        )

    return cpol_result

# =============================================================================
# EXECUTION LOOP (Test the Mesh)
# =============================================================================
if __name__ == "__main__":
    # Simulation: 3 conversational turns to prove History is working

    # Turn 1: Normal Query
    system_step("Hello system", "low")

    # Turn 2: Paradox introduced (CPOL should oscillate but maybe resolve)
    system_step("This statement is false.", "high")

    # Turn 3: Persistent Paradox (Should trigger 'History Cap' logic in CPOL)
    system_step("Still false.", "high")

    # Verify Persistence
    print("\n[AUDIT] Checking Shared Memory History...")
    kernel = shared_memory['cpol_instance']
    print(f"Kernel History Length: {len(kernel.history)} (Should be > 1)")

    print(f"Latest Z-Vector: {kernel.z}")