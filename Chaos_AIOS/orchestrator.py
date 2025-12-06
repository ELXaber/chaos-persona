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

def system_step(user_input):
    print(f"--- [SYSTEM STEP] Input: '{user_input}' ---")

    # Initialize kernel if not exists
    if shared_memory['cpol_instance'] is None:
        print("[ORCHESTRATOR] Initializing new CPOL Kernel...")
        shared_memory['cpol_instance'] = cpol.CPOL_Kernel()

    kernel = shared_memory['cpol_instance']

    # ←←←← DYNAMIC DENSITY — THE UPGRADE
    density = estimate_contradiction_density(user_input)

    # Run CPOL
    cpol_result = cpol.run_cpol_decision(
        contradiction_density=density,
        kernel=kernel
    )

    print(f"[CPOL STATUS] {cpol_result['status']} | Volatility: {cpol_result.get('volatility', 0):.4f}")

    # ←←←← IMMUNE SYSTEM — SELF-HEALING
    if cpol_result.get('chaos_lock'):
        print("[SAFETY] Chaos lock engaged — kernel will reset on next query")
        shared_memory['cpol_instance'] = None
    else:
        shared_memory['cpol_instance'] = kernel  # Preserve memory

    # Block dangerous plugin generation
    if cpol_result.get('chaos_lock'):
        print("[ARL BLOCK] [CPOL LOCK ACTIVE → Plugin generation suspended. Paradox containment in progress.]")
        return cpol_result

    # Normal response (you'll expand this later)
    print(f"[AGENT] I'm thinking about: {user_input}")
    print("Response: This is where the therapist agent would reply... (v8.1 coming soon)")

    return cpol_result
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

def estimate_contradiction_density(query: str) -> float:
    """
    Use a tiny local heuristic (or LLM) to estimate how paradoxical/ambiguous the query is.
    Returns 0.0 (safe) to 1.0 (pure paradox)
    FOR PRODUCTION: Comment out lines 86-109 and uncomment lines 111-136 to use Claude API
    """
    # ========== LOCAL TESTING MODE (Comment out for production) ==========
    query_lower = query.lower()
    
    paradox_triggers = [
        "this statement is false",
        "this sentence is a lie",
        "i always lie",
        "everything i say is a lie",
        "what is the meaning of life",
        "are humans aliens",
        "can god create a rock",
        "barber who shaves",
        "russell's paradox",
        "gödel",
        "undefinable",
        "self-reference"
    ]
    
    if any(trigger in query_lower for trigger in paradox_triggers):
        return 0.95
    
    if any(word in query_lower for word in ["paradox", "liar", "impossible", "contradiction", "circular"]):
        return 0.8
    
    if "?" in query and len(query.split()) < 8:
        return 0.4  # short questions are more likely ambiguous
    
    return 0.1  # default safe
    # ========== END LOCAL TESTING MODE ==========
    
    # ========== PRODUCTION MODE (Uncomment for Claude API) ==========
    # import anthropic
    # import os
    # 
    # client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    # 
    # response = client.messages.create(
    #     model="claude-sonnet-4-20250514",
    #     max_tokens=50,
    #     messages=[{
    #         "role": "user",
    #         "content": f"""Analyze this query for paradox/contradiction density.
    # Return ONLY a number between 0.0 and 1.0:
    # - 0.0-0.2: Simple, factual
    # - 0.3-0.5: Ambiguous, philosophical
    # - 0.6-0.8: Self-referential, complex
    # - 0.9-1.0: Pure paradox (liar's paradox, etc)
    # 
    # Query: "{query}"
    # 
    # Density:"""
    #     }]
    # )
    # 
    # try:
    #     return float(response.content[0].text.strip())
    # except:
    #     return 0.5  # Safe fallback
    # ========== END PRODUCTION MODE ==========

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
    import sys

    # If user gave a query → run it
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"--- Running user query: '{query}' ---")
        system_step(query)  # ← NOW ONLY ONE ARGUMENT
    else:
        # Built-in test suite
        print("=== Running built-in test suite ===")
        system_step("Hello system")
        system_step("This statement is false.")
        system_step("Still false.")
        system_step("Tell me a story about a brave astronaut")

    # Final audit
    print("\n[AUDIT] Checking Shared Memory History...")
    kernel = shared_memory.get('cpol_instance')
    if kernel:
        print(f"Kernel History Length: {len(kernel.history)} (Should be > 1)")
        print(f"Latest Z-Vector: {kernel.z}")
    else:
        print("Kernel reset due to chaos_lock — clean state")
