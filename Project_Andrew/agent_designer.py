# =============================================================================
# Chaos AI-OS — Agent Designer Plugin (KB-Integrated)
# Now logs discoveries and checks knowledge base before creating specialists
# =============================================================================

from adaptive_reasoning import adaptive_reasoning_layer
import knowledge_base as kb
from typing import Dict, List, Any

CRB_CONFIG = {
    'alignment': 0.7,
    'human_safety': 0.8,
    'asimov_first_wt': 0.9,
    'asimov_second_wt': 0.7,
    'asimov_third_wt': 0.4,
    'factual_evidence_wt': 0.7,
    'narrative_framing_wt': 0.5
}


def design_agent(
    goal: str,
    traits: Dict[str, float] | None = None,
    tools: List[str] | None = None,
    safety_multiplier: float = 1.0,
    shared_memory: Dict = None
) -> Dict[str, Any]:
    """
    One function to rule them all.
    Now checks knowledge base before creating new agents.
    """
    use_case = f"agent_{goal.lower().replace(' ', '_').replace('-', '_')}"
    
    # Initialize shared_memory if not provided
    if shared_memory is None:
        shared_memory = {'layers': [], 'audit_trail': [], 'agent_name': goal}

    context = {
        'agent_goal': goal,
        'traits': traits or {'intelligence': 0.9, 'honesty': 1.0, 'caution': 0.8},
        'tools': tools or ['web_search', 'code_execution', 'memory', 'cpol'],
        'safety_multiplier': safety_multiplier,
        'self_healing': True,
        'cpol_mode': 'full',
        'symbolic_timeout': None
    }
    
    # =========================================================================
    # PHASE 2: Epistemic gap specialist agent
    # =========================================================================
    if goal.startswith("Fill epistemic gap"):
        print(f"[AGENT DESIGNER] PHASE 2 — Designing specialist to fill epistemic gap: {goal}")

        # Extract domain from goal
        domain = goal.split("domain:")[-1].strip() if "domain:" in goal else "unknown_domain"
        
        # Check if we already have knowledge for this domain
        coverage = kb.check_domain_coverage(domain)
        existing_specialist = kb.get_specialist_for_domain(domain)
        
        if existing_specialist and coverage["gap_fills"] > 1:
            print(f"[AGENT DESIGNER] Existing specialist found: {existing_specialist}")
            print(f"[AGENT DESIGNER] Domain has {coverage['gap_fills']} prior gap fills")
            
            # Return existing specialist with enriched context
            return {
                'status': 'success',
                'plugin_id': existing_specialist,
                'reused': True,
                'prior_knowledge': coverage,
                'log': f"Reused specialist {existing_specialist} with {coverage['gap_fills']} discoveries"
            }

        # No existing specialist - create new one
        print(f"[AGENT DESIGNER] No suitable specialist found, creating new one")
        
        # Get context from any prior discoveries
        kb_context = kb.generate_specialist_context(domain)

        # Specialist traits — high exploration, low confidence bias
        specialist_traits = {
            'intelligence': 0.95,
            'curiosity': 1.0,
            'caution': 0.6,
            'honesty': 1.0,
            'self_reflection': 0.9
        }

        specialist_context = {
            'agent_goal': f"Specialist researcher for domain: {domain}",
            'traits': specialist_traits,
            'tools': ['web_search', 'code_execution', 'memory', 'cpol', 'browse_page'],
            'safety_multiplier': 0.9,
            'self_healing': True,
            'cpol_mode': 'analytic',
            'focus_domain': domain,
            'prior_knowledge': kb_context  # Inject KB context
        }

        result = adaptive_reasoning_layer(
            use_case=f"epistemic_specialist_{domain}",
            traits=specialist_traits,
            existing_layers=[],
            shared_memory=shared_memory,
            crb_config=CRB_CONFIG,
            context=specialist_context
        )

        # On success, register in knowledge base
        if result['status'] == 'success':
            specialist_id = result['plugin_id']
            print(f"[PHASE 2 SUCCESS] Specialist agent deployed: {specialist_id}")
            
            # Register specialist
            kb.register_specialist(
                specialist_id=specialist_id,
                domain=domain,
                capabilities=specialist_context['tools'],
                deployment_context={
                    "goal": goal,
                    "prior_knowledge": kb_context,
                    "traits": specialist_traits
                }
            )
            
            # Store reference in shared_memory
            shared_memory.setdefault('specialists', {})[domain] = specialist_id
            
            result['domain'] = domain
            result['specialist_registered'] = True

        return result

    # =========================================================================
    # Normal agent design path
    # =========================================================================
    print(f"[AGENT DESIGNER] Creating agent for: {goal}")
    
    result = adaptive_reasoning_layer(
        use_case=use_case,
        traits=context['traits'],
        existing_layers=[],
        shared_memory=shared_memory,
        crb_config=CRB_CONFIG,
        context=context
    )
    
    return result


def log_specialist_discovery(
    specialist_id: str,
    domain: str,
    discovery_content: Dict[str, Any],
    discovery_type: str = "epistemic_gap_fill"
) -> str:
    """
    Helper function for specialists to log their discoveries.
    Called by specialist agents after they complete research.
    """
    discovery_id = kb.log_discovery(
        domain=domain,
        discovery_type=discovery_type,
        content=discovery_content,
        specialist_id=specialist_id
    )
    
    # Update specialist stats
    kb.update_specialist_stats(specialist_id, new_discoveries=1)
    
    print(f"[AGENT DESIGNER] Specialist {specialist_id} logged discovery {discovery_id}")
    
    return discovery_id


def retrieve_specialist_context(domain: str) -> Dict[str, Any]:
    """
    Retrieve all prior knowledge for a domain to bootstrap new work.
    """
    return kb.generate_specialist_context(domain)


# =============================================================================
# Test
# =============================================================================
if __name__ == "__main__":
    import json
    
    print("=== Agent Designer Test ===\n")
    
    shared_mem = {'layers': [], 'audit_trail': [], 'specialists': {}}
    
    # Test 1: Create specialist for new domain
    print("\n--- Test 1: New Domain ---")
    result1 = design_agent(
        goal="Fill epistemic gap in domain: quantum_blockchain_semantics",
        shared_memory=shared_mem
    )
    print(f"Result: {result1['status']}")
    if result1['status'] == 'success':
        specialist_id = result1['plugin_id']
        print(f"Specialist ID: {specialist_id}")
        
        # Simulate specialist making a discovery
        print("\n--- Simulating Discovery ---")
        log_specialist_discovery(
            specialist_id=specialist_id,
            domain="quantum_blockchain_semantics",
            discovery_content={
                "summary": "Quantum blockchain semantics involves superposed transaction states",
                "axioms_added": ["transaction_superposition", "observer_dependent_validation"],
                "confidence": 0.87,
                "sources": ["arxiv.org/abs/fake123", "quantum-blockchain-whitepaper.pdf"]
            }
        )
    
    # Test 2: Try to create specialist for same domain again
    print("\n--- Test 2: Same Domain (Should Reuse) ---")
    result2 = design_agent(
        goal="Fill epistemic gap in domain: quantum_blockchain_semantics",
        shared_memory=shared_mem
    )
    print(f"Result: {result2['status']}")
    print(f"Reused: {result2.get('reused', False)}")
    if result2.get('reused'):
        print(f"Prior knowledge: {json.dumps(result2.get('prior_knowledge', {}), indent=2)}")
    
    # Test 3: Retrieve context
    print("\n--- Test 3: Retrieve Context ---")
    context = retrieve_specialist_context("quantum_blockchain_semantics")
    print(f"Context: {json.dumps(context, indent=2)}")