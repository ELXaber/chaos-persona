# =============================================================================
# Chaos AI-OS — Orchestrator (The Master Loop)
# Description: Meshes CAIOS prompts, CPOL dynamics, and ARL plugins.
# =============================================================================

import paradox_oscillator as cpol
import adaptive_reasoning as arl
import time
# Let agents be auto-discovered
import importlib
import os
for file in os.listdir("agents"):
    if file.endswith(".py") and not file.startswith("_"):
        importlib.import_module(f"agents.{file[:-3]}")

# 1. Persistent State Container (Matches CAIOS Schema)
shared_memory = {
    'layers': [],
    'audit_trail': [],
    'cpol_instance': None,     # Stores the active Kernel Object
    'cpol_state': {'chaos_lock': False},
    'session_context': {'RAW_Q': None, 'timestep': 0},
    'traits_history': [],
    'scratch_space': {}
}

CRB_CONFIG = {
    'alignment': 0.7,
    'human_safety': 0.8,
    'asimov_first_wt': 0.9,
    'asimov_second_wt': 0.7,
    'asimov_third_wt': 0.4,
    'factual_evidence_wt': 0.7,
    'narrative_framing_wt': 0.5
}

def system_step(user_input, prompt_complexity="medium"):
    """
    Runs one 'heartbeat' of the OS.
    1. Checks if CPOL is needed.
    2. Runs ARL if plugins are requested.
    3. Updates Shared Memory.
    """
    print(f"\n--- [SYSTEM STEP] Input: '{user_input}' ---")

    # --- PHASE 1: PARADOX OSCILLATION (CPOL) ---
    # Initialize Kernel if it doesn't exist (Fixes Amnesia)
    if shared_memory['cpol_instance'] is None:
        print("[ORCHESTRATOR] Initializing new CPOL Kernel...")
        shared_memory['cpol_instance'] = cpol.CPOL_Kernel()
    
    engine = shared_memory['cpol_instance']
    
    # Map complexity to density (Mocking CAIOS prompt parsing)
    density_map = {"high": 0.9, "medium": 0.5, "low": 0.1}
    density = density_map.get(prompt_complexity, 0.1)

    # Use the persistent kernel
    cpol_result = cpol.run_cpol_decision(
        prompt_complexity=prompt_complexity,
        contradiction_density=density,
        kernel=engine
    )
    
    # Update Shared Memory with results
    shared_memory['cpol_state'] = cpol_result
    vol = cpol_result.get('volatility', 0.0)
    print(f"[CPOL STATUS] {cpol_result['status']} | Volatility: {vol:.4f}")

    # --- PHASE 2: ADAPTIVE REASONING (ARL) ---
    # Trigger ARL if user asks for a plugin OR if CPOL is Undecidable
    if "generate plugin" in user_input or cpol_result['status'] == "UNDECIDABLE":
        
        print("[ORCHESTRATOR] Triggering Adaptive Reasoning Layer...")
        
        # Determine Use Case
        use_case = "paradox_containment" if cpol_result['status'] == "UNDECIDABLE" else "custom_tool"
        
        arl_result = arl.adaptive_reasoning_layer(
            use_case=use_case,
            traits={'flexibility': 0.8},
            existing_layers=shared_memory['layers'],
            shared_memory=shared_memory,
            crb_config=CRB_CONFIG,
            cpol_status=shared_memory['cpol_state'],
            context={
                'contradiction_density': density,
                'volatility': vol,
                'threshold': 0.4,
                'safety_wt': 0.9
            }
        )
        
        if arl_result['status'] == 'success':
            print(f"[ARL SUCCESS] Plugin Deployed: {arl_result['plugin_id']}")
        else:
            print(f"[ARL BLOCK] {arl_result['log']}")
            
        return arl_result

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


