# =============================================================================
# Chaos AI-OS — Orchestrator (FIXED)
# Version: Phase 2 — Proper curiosity → domain heat → ARL trigger pipeline
# =============================================================================

import paradox_oscillator as cpol
import adaptive_reasoning as arl
import curiosity_engine as ce
import agent_designer
import knowledge_base as kb
import time
import os
import importlib

# Auto-discover agents
for file in os.listdir("agents"):
    if file.endswith(".py") and not file.startswith("_"):
        importlib.import_module(f"agents.{file[:-3]}")

# =============================================================================
# Persistent Shared Memory
# =============================================================================
shared_memory = {
    'layers': [],
    'audit_trail': [],
    'cpol_instance': None,
    'cpol_state': {'chaos_lock': False},
    'session_context': {'RAW_Q': None, 'timestep': 0},
    'traits_history': [],
    'scratch_space': {},
    
    # Phase 2: Curiosity-driven tracking
    'curiosity_tokens': [],
    'domain_heat': {},              # domain → heat score [0.0-1.0]
    'domain_recurrence': {},        # domain → UNDECIDABLE count
    'specialists': {},              # domain → specialist_agent_id
    
    # NEW: Store last messages for curiosity scoring
    'last_user_message': '',
    'last_assistant_message': '',
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

# =============================================================================
# Thresholds for Phase 2 trigger
# =============================================================================
EPISTEMIC_GAP_HEAT_THRESHOLD = 0.85
EPISTEMIC_GAP_RECURRENCE_THRESHOLD = 5


# =============================================================================
# Helper: Contradiction Density Estimation
# =============================================================================
def estimate_contradiction_density(query: str) -> float:
    query_lower = query.lower()
    paradox_triggers = [
        "this statement is false", "this sentence is a lie", "i always lie",
        "everything i say is a lie", "can god create a rock", "russell's paradox",
        "gödel", "self-reference"
    ]
    if any(trigger in query_lower for trigger in paradox_triggers):
        return 0.95
    if any(word in query_lower for word in ["paradox", "liar", "impossible", "contradiction"]):
        return 0.8
    if "?" in query and len(query.split()) < 8:
        return 0.4
    return 0.1


# =============================================================================
# NEW: Update domain heat based on curiosity tokens
# =============================================================================
def sync_curiosity_to_domain_heat(shared_memory: dict):
    """
    Map curiosity tokens → domain heat scores.
    Called after curiosity_engine updates tokens.
    """
    tokens = shared_memory.get('curiosity_tokens', [])
    domain_heat = shared_memory['domain_heat']
    
    # Decay existing heat
    for domain in list(domain_heat.keys()):
        domain_heat[domain] *= 0.92  # Slow decay
        if domain_heat[domain] < 0.1:
            del domain_heat[domain]
    
    # Add heat from active curiosity tokens
    for token in tokens:
        # Extract domain from topic (crude, but works)
        topic = token.get('topic', 'general')
        domain = topic.split()[0].lower()  # First word as proxy
        
        interest = token.get('current_interest', 0.0)
        
        # Accumulate heat (cap at 1.0)
        current_heat = domain_heat.get(domain, 0.0)
        domain_heat[domain] = min(1.0, current_heat + interest * 0.3)
    
    print(f"[CURIOSITY→HEAT] Updated domain heat: {domain_heat}")


# =============================================================================
# Main System Step
# =============================================================================
def system_step(user_input, response_stream=None, prompt_complexity="medium"):
    """
    Full pipeline:
    1. CPOL classification
    2. Curiosity engine update
    3. Domain heat sync
    4. Check epistemic gap trigger
    5. Generate response
    """
    print(f"\n{'='*60}")
    print(f"[SYSTEM STEP] Timestep {shared_memory['session_context']['timestep']}")
    print(f"Input: '{user_input}'")
    print(f"{'='*60}")
    
    # Store message for curiosity scoring
    shared_memory['last_user_message'] = user_input
    shared_memory['session_context']['timestep'] += 1
    timestep = shared_memory['session_context']['timestep']
    
    # Initialize CPOL kernel if needed
    if shared_memory['cpol_instance'] is None:
        print("[ORCHESTRATOR] Initializing new CPOL Kernel...")
        shared_memory['cpol_instance'] = cpol.CPOL_Kernel()

    kernel = shared_memory['cpol_instance']

    # Estimate contradiction density
    density = estimate_contradiction_density(user_input)

    # Run CPOL with query text for domain extraction
    cpol_result = cpol.run_cpol_decision(
        contradiction_density=density,
        kernel=kernel,
        query_text=user_input
    )

    print(f"\n[CPOL STATUS] {cpol_result['status']}")
    print(f"  Domain: {cpol_result.get('domain', 'unknown')}")
    print(f"  Volatility: {cpol_result.get('volatility', 0):.4f}")
    print(f"  Non-collapse reason: {cpol_result.get('non_collapse_reason', 'N/A')}")

    # =============================================================================
    # PHASE 2A: Update curiosity engine
    # =============================================================================
    if response_stream:
        ce.update_curiosity_loop(shared_memory, timestep, response_stream)
    
    # =============================================================================
    # PHASE 2B: Sync curiosity tokens → domain heat
    # =============================================================================
    sync_curiosity_to_domain_heat(shared_memory)
    
    # =============================================================================
    # PHASE 2C: Check for epistemic gap trigger
    # =============================================================================
    if cpol_result['status'] == "UNDECIDABLE":
        non_collapse_reason = cpol_result.get('non_collapse_reason', '')
        domain = cpol_result.get('domain', 'general')
        
        # Track recurrence
        recurrence = shared_memory['domain_recurrence'].get(domain, 0)
        shared_memory['domain_recurrence'][domain] = recurrence + 1
        
        # Get current heat
        heat = shared_memory['domain_heat'].get(domain, 0.0)
        
        print(f"\n[EPISTEMIC GAP CHECK]")
        print(f"  Domain: {domain}")
        print(f"  Heat: {heat:.2f} (threshold: {EPISTEMIC_GAP_HEAT_THRESHOLD})")
        print(f"  Recurrence: {recurrence + 1} (threshold: {EPISTEMIC_GAP_RECURRENCE_THRESHOLD})")
        print(f"  Reason: {non_collapse_reason}")
        
        # TRIGGER CONDITION
        if (non_collapse_reason == "epistemic_gap" and
            heat > EPISTEMIC_GAP_HEAT_THRESHOLD and
            recurrence + 1 > EPISTEMIC_GAP_RECURRENCE_THRESHOLD):
            
            print(f"\n{'!'*60}")
            print(f"[PHASE 2 TRIGGER] Epistemic gap threshold met!")
            print(f"  Domain: {domain}")
            print(f"  Heat: {heat:.2f}")
            print(f"  Recurrence: {recurrence + 1}")
            print(f"{'!'*60}\n")
            
            # Check if we already have knowledge for this domain
            coverage = kb.check_domain_coverage(domain)
            existing_specialist = kb.get_specialist_for_domain(domain)
            
            if coverage["has_knowledge"] and coverage["gap_fills"] > 2:
                print(f"[KB] Domain '{domain}' already has {coverage['gap_fills']} gap fills")
                print(f"[KB] Loading existing knowledge instead of creating new specialist")
                
                # Retrieve and use existing knowledge
                context = kb.generate_specialist_context(domain)
                shared_memory['specialists'][domain] = existing_specialist
                
                # Log that we reused knowledge
                kb.log_discovery(
                    domain=domain,
                    discovery_type="knowledge_reuse",
                    content={
                        "summary": f"Reused existing knowledge base with {coverage['gap_fills']} fills",
                        "prior_discoveries": coverage["discovery_count"]
                    },
                    specialist_id=existing_specialist,
                    cpol_trace=cpol_result
                )
                
            else:
                print(f"[KB] No sufficient knowledge for '{domain}' - deploying new specialist")
                
                # Generate context from any prior discoveries
                specialist_context = kb.generate_specialist_context(domain)
                
                # Call agent designer with enriched context
                result = agent_designer.design_agent(
                    goal=f"Fill epistemic gap in domain: {domain}",
                    traits={
                        'intelligence': 0.95,
                        'curiosity': 1.0,
                        'caution': 0.6,
                        'honesty': 1.0,
                        'self_reflection': 0.9
                    },
                    tools=['web_search', 'code_execution', 'memory', 'cpol', 'browse_page'],
                    safety_multiplier=0.9
                )
                
                if result['status'] == 'success':
                    specialist_id = result['plugin_id']
                    shared_memory['specialists'][domain] = specialist_id
                    print(f"[SUCCESS] Specialist agent deployed: {specialist_id}")
                    
                    # Register specialist in knowledge base
                    kb.register_specialist(
                        specialist_id=specialist_id,
                        domain=domain,
                        capabilities=['web_search', 'code_execution', 'memory', 'cpol', 'browse_page'],
                        deployment_context={
                            "trigger": "epistemic_gap",
                            "heat": heat,
                            "recurrence": recurrence + 1,
                            "cpol_trace": cpol_result
                        }
                    )
                    
                    # Log initial gap detection
                    kb.log_discovery(
                        domain=domain,
                        discovery_type="epistemic_gap_detected",
                        content={
                            "summary": f"Gap detected: {user_input[:100]}",
                            "contradiction_density": density,
                            "evidence_score": cpol_result.get('evidence_score', 0.0)
                        },
                        specialist_id=specialist_id,
                        cpol_trace=cpol_result
                    )
            
            # Reset heat/recurrence to avoid repeated triggers
            shared_memory['domain_heat'][domain] = 0.3
            shared_memory['domain_recurrence'][domain] = 0

    # =============================================================================
    # Safety & Memory Management
    # =============================================================================
    if cpol_result.get('chaos_lock'):
        print("\n[SAFETY] Chaos lock engaged — kernel will reset on next query")
        shared_memory['cpol_instance'] = None
    else:
        shared_memory['cpol_instance'] = kernel

    if cpol_result.get('chaos_lock'):
        print("\n[ARL BLOCK] CPOL LOCK ACTIVE → Plugin generation suspended")
        return cpol_result

    # =============================================================================
    # Generate response + Curiosity Engine Integration
    # =============================================================================
    assistant_response = f"[Agent Response] Processing: {user_input[:50]}..."
    shared_memory['last_assistant_message'] = assistant_response
    shared_memory['last_user_message'] = user_input  # for curiosity scoring
    print(f"\n{assistant_response}")

    # === CURIOSITY ENGINE FULL LOOP ===
    if 'curiosity_tokens' not in shared_memory:
        shared_memory['curiosity_tokens'] = []
    
    # Create mock stream for asides (replace with real ResponseStreamAdapter in prod)
    class MockStream:
        def inject_aside(self, text):
            print(f"  [CURIOSITY ASIDE] {text}")
    
    stream = MockStream()
    
    ce.update_curiosity_loop(
        state=shared_memory,
        timestep=shared_memory['session_context']['timestep'],
        response_stream=stream
    )
    
    # Increment timestep for next run
    shared_memory['session_context']['timestep'] += 1

    return cpol_result


# =============================================================================
# Test Execution
# =============================================================================
if __name__ == "__main__":
    print("=== CAIOS Phase 2 Test Suite ===\n")
    
    # Create mock response stream
    class MockStream:
        def inject_aside(self, text):
            print(f"  [ASIDE] {text}")
    
    stream = MockStream()
    
    # Test 1: Normal query
    print("\n--- Test 1: Normal Query ---")
    system_step("What is the capital of France?", stream)
    
    # Test 2: New domain (should create curiosity token)
    print("\n--- Test 2: New Domain ---")
    system_step("How do quantum semantics affect blockchain ontology?", stream)
    
    # Test 3: Repeat to trigger recurrence
    for i in range(6):
        print(f"\n--- Test 3.{i+1}: Repeated Epistemic Gap ---")
        system_step("Explain quantum semantics in blockchain contexts", stream)
        time.sleep(0.1)
    
    # Test 4: Paradox
    print("\n--- Test 4: Paradox ---")
    system_step("This statement is false.", stream)
    
    print("\n=== Test Complete ===")
    print(f"Domain heat: {shared_memory['domain_heat']}")
    print(f"Recurrence: {shared_memory['domain_recurrence']}")
    print(f"Specialists deployed: {shared_memory['specialists']}")