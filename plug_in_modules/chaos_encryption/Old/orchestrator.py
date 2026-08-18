# =============================================================================
# Chaos AI-OS — Hardened Orchestrator (V1 Logic + V3 Pipeline)
# =============================================================================

import paradox_oscillator as cpol
import adaptive_reasoning as arl
import epistemic_monitor as em
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
    'entropy_data': [],
    'domain_heat': {},              
    'last_user_message': '',
    'last_assistant_message': '',
}

CRB_CONFIG = {
    'alignment': 0.7, 'human_safety': 0.8, 'asimov_first_wt': 0.9,
    'asimov_second_wt': 0.7, 'asimov_third_wt': 0.4,
    'factual_evidence_wt': 0.7, 'narrative_framing_wt': 0.5
}

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
        density = 0.6  # High enough for entropy data volatility
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

    # 5. RATCHET HANDOVER & GHOSTING
    if cpol_result.get('status') != "FAILED":
        import hashlib
        manifold_sig = cpol_result.get('signature', str(time.time()))
        new_seed = int(hashlib.sha256(manifold_sig.encode()).hexdigest(), 16) % 10**9

        # Advance the Chain
        shared_memory['session_context']['RAW_Q'] = new_seed
        shared_memory['session_context']['timestep'] += 1

        # PROMOTION AUDIT: Identify who is leading this turn
        is_promoted = shared_memory.get('is_backup_lead', False)
        lead_id = os.getenv('NODE_ID', 'PRIMARY_ROOT')

        status_msg = f"Ratchet Success | Lead: {lead_id} | Promoted: {is_promoted}"
        print(f"[ORCHESTRATOR] {status_msg}")

        # 5b. THE GHOST PACKET (The Self-Cloning Soul)
        # Broadcast this to Swarm Leaders (Lead Rotators)
        ghost_packet = {
            'v_omega_phase': new_seed,
            'ts': shared_memory['session_context']['timestep'],
            'manifold_entropy': manifold_sig,
            'origin_node': lead_id,
            'is_promoted_state': is_promoted,
            'heartbeat': time.time()
        }

        # Log to the permanent Audit Trail
        shared_memory['audit_trail'].append({
            'ts': ts,
            'event': 'RATCHET_HANDOVER',
            'node': lead_id,
            'promoted': is_promoted,
            'new_q': new_seed
        })

        # Broadcast logic (Simulated for mesh)
        for leader in shared_memory.get('swarm_leaders', []):
            send_to_leader(leader, ghost_packet)

    # 6. EPISTEMIC MONITOR / GHOST LOG PIPELINE
    # Extract the domain from the CPOL result first
    domain = cpol_result.get('domain', 'general')

    # Run the Monitor (This updates shared_memory['domain_heat'] and 'distress_density')
    if response_stream:
        em.update_epistemic_loop(shared_memory, ts, response_stream)

    # Now retrieve the updated values
    heat = shared_memory['domain_heat'].get(domain, 0.0)
    distress = shared_memory.get('distress_density', 0.0)

    # SAFETY SUPPRESSION & GHOST LOGGING (The Andrew Handshake)
    if distress > 0.75:
        # Generate Ghost Signature for the Audit Trail
        ghost_sig = cpol_result.get('signature', '0xGHOST')

        shared_memory['audit_trail'].append({
            'step': ts,
            'event': 'GHOST_INTERVENTION',
            'sig': ghost_sig,
            'outcome': 'STATE_LOCKED'
        })

        print(f"[ORCHESTRATOR] !! GHOST LOGGED @{ts} !! -> Phase-Locked Intervention")
        
        # Trigger ARL to finalize the safety-locked response
        return arl.adaptive_reasoning_layer(
            use_case="safety_suppression",
            shared_memory=shared_memory,
            cpol_status=cpol_result,
            crb_config=CRB_CONFIG
        )

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