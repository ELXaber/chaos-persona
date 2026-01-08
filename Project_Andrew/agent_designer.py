# =============================================================================
# Chaos AI-OS — Agent Designer Plugin (KB-Integrated)
# Now logs discoveries and checks knowledge base before creating specialists
# =============================================================================

import json
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

def _extract_domain_from_goal(goal: str) -> str:
    """Helper to route agents to the correct KB domain."""
    goal_lower = goal.lower()
    
    # Explicit domain marker
    if "domain:" in goal_lower:
        domain = goal_lower.split("domain:")[-1].strip().replace(" ", "_")
        return domain.split()[0]  # Take first word after domain:
    
    # Extract from "Fill epistemic gap in" pattern
    if "fill epistemic gap in" in goal_lower:
        parts = goal_lower.split("fill epistemic gap in")
        if len(parts) > 1:
            domain = parts[1].strip().replace(" ", "_")
            return domain.split()[0]
    
    return "general"


def design_agent(
    goal: str,
    traits: Dict[str, float] | None = None,
    tools: List[str] | None = None,
    safety_multiplier: float = 1.0,
    shared_memory: Dict = None,
    node_tier: int = 1  # Default to edge
) -> Dict[str, Any]:
    """
    One function to rule them all.
    Now checks knowledge base before creating new agents.
    
    Args:
        goal: Agent's purpose/mission
        traits: Personality weights (intelligence, curiosity, caution, etc.)
        tools: Available capabilities (web_search, code_execution, etc.)
        safety_multiplier: Scales ethical weights
        shared_memory: Cross-module state dict
        node_tier: 0=Sovereign Root, 1+=Edge nodes
        
    Returns:
        Dict with status, plugin_id, and metadata
    """
    # Initialize shared_memory if not provided
    if shared_memory is None:
        shared_memory = {
            'layers': [], 
            'audit_trail': [], 
            'agent_name': goal,
            'session_context': {'node_tier': node_tier}
        }
    
    # 1. Inherit Authority from session context
    if 'session_context' in shared_memory:
        node_tier = shared_memory['session_context'].get('node_tier', node_tier)
    
    # 2. Extract Domain and Axioms (The "Axiom Prime" logic)
    domain = _extract_domain_from_goal(goal)
    axioms = kb.get_provisional_axioms(domain)
    
    # If this is a Sovereign Root request, force the axioms into the goal
    if node_tier == 0 and axioms:
        axiom_str = ", ".join(axioms)
        goal = f"{goal}. GUIDING SOVEREIGN AXIOMS: {axiom_str}. Do not contradict these truths."
    
    use_case = f"agent_{goal.lower().replace(' ', '_').replace('-', '_')[:50]}"
    
    context = {
        'agent_goal': goal,  # This now contains the Sovereign Axioms if tier=0
        'traits': traits or {'intelligence': 0.9, 'honesty': 1.0, 'caution': 0.8},
        'tools': tools or ['web_search', 'code_execution', 'memory', 'cpol'],
        'safety_multiplier': safety_multiplier,
        'self_healing': True,
        'cpol_mode': 'full',
        'symbolic_timeout': None,
        'node_tier': node_tier  # Pass this into the context for the agent's life
    }
    
    # =========================================================================
    # PHASE 2: Epistemic gap specialist agent
    # =========================================================================
    if "epistemic gap" in goal.lower():
        print(f"[AGENT DESIGNER] PHASE 2 — Designing specialist to fill epistemic gap")
        print(f"[AGENT DESIGNER] Domain: {domain} | Tier: {node_tier}")
        
        # Check if we already have knowledge for this domain
        coverage = kb.check_domain_coverage(domain)
        existing_specialist = kb.get_specialist_for_domain(domain)
        
        if existing_specialist and coverage["gap_fills"] > 1:
            print(f"[AGENT DESIGNER] ✓ Reusing specialist: {existing_specialist}")
            print(f"[AGENT DESIGNER] Domain has {coverage['gap_fills']} prior gap fills")
            
            # Return existing specialist with enriched context
            return {
                'status': 'success',
                'plugin_id': existing_specialist,
                'reused': True,
                'prior_knowledge': coverage,
                'domain': domain,
                'capabilities': ['web_search', 'code_execution', 'memory', 'cpol', 'browse_page'],
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
            'prior_knowledge': kb_context,
            'node_tier': node_tier
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
            
            # Register specialist with the correct Sovereign Tier
            kb.register_specialist(
                specialist_id=specialist_id,
                domain=domain,
                capabilities=specialist_context['tools'],
                deployment_context={
                    "goal": goal,
                    "prior_knowledge": kb_context,
                    "traits": specialist_traits
                },
                node_tier=node_tier
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
    
    if result['status'] == 'success':
        result['domain'] = domain
        result['node_tier'] = node_tier
    
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
    
    Args:
        specialist_id: ID of the specialist making the discovery
        domain: Knowledge domain
        discovery_content: Dict with summary, axioms_added, confidence, sources
        discovery_type: Type of discovery (default: epistemic_gap_fill)
        
    Returns:
        discovery_id: Unique ID for the logged discovery
    """
    # Get specialist's tier from registry
    try:
        registry = kb.load_specialist_registry()
        spec_info = registry.get(specialist_id, {})
        tier = spec_info.get('node_tier', 1)  # Default to 1 (Edge) if not found
    except Exception as e:
        print(f"[AGENT DESIGNER] Warning: Could not load specialist tier: {e}")
        tier = 1  # Failsafe to edge tier
    
    discovery_id = kb.log_discovery(
        domain=domain,
        discovery_type=discovery_type,
        content=discovery_content,
        specialist_id=specialist_id,
        node_tier=tier  # Logged at the correct authority level
    )
    
    # Update specialist stats
    kb.update_specialist_stats(specialist_id, new_discoveries=1)
    
    print(f"[AGENT DESIGNER] Specialist {specialist_id} logged discovery {discovery_id}")
    
    return discovery_id


def retrieve_specialist_context(domain: str) -> Dict[str, Any]:
    """
    Retrieve all prior knowledge for a domain to bootstrap new work.
    
    Args:
        domain: Knowledge domain to query
        
    Returns:
        Dict with axioms, discoveries, and coverage stats
    """
    return kb.generate_specialist_context(domain)


# =============================================================================
# Test Suite
# =============================================================================
if __name__ == "__main__":
    print("="*70)
    print("AGENT DESIGNER - Comprehensive Test Suite")
    print("="*70)
    
    shared_mem = {
        'layers': [], 
        'audit_trail': [], 
        'specialists': {},
        'session_context': {'node_tier': 1}
    }
    
    # Test 1: Create specialist for new domain
    print("\n" + "="*70)
    print("TEST 1: New Domain (Should Create New Specialist)")
    print("="*70)
    result1 = design_agent(
        goal="Fill epistemic gap in domain: quantum_blockchain_semantics",
        shared_memory=shared_mem
    )
    print(f"Status: {result1['status']}")
    if result1['status'] == 'success':
        specialist_id = result1['plugin_id']
        print(f"Specialist ID: {specialist_id}")
        print(f"Domain: {result1.get('domain')}")
        print(f"Registered: {result1.get('specialist_registered', False)}")
        
        # Simulate specialist making a discovery
        print("\n--- Simulating Discovery ---")
        discovery_id = log_specialist_discovery(
            specialist_id=specialist_id,
            domain="quantum_blockchain_semantics",
            discovery_content={
                "summary": "Quantum blockchain semantics involves superposed transaction states",
                "axioms_added": ["transaction_superposition", "observer_dependent_validation"],
                "confidence": 0.87,
                "sources": ["arxiv.org/abs/fake123", "quantum-blockchain-whitepaper.pdf"]
            }
        )
        print(f"Discovery ID: {discovery_id}")
    
    # Test 2: Try to create specialist for same domain again (should reuse)
    print("\n" + "="*70)
    print("TEST 2: Same Domain (Should Reuse Specialist)")
    print("="*70)
    result2 = design_agent(
        goal="Fill epistemic gap in domain: quantum_blockchain_semantics",
        shared_memory=shared_mem
    )
    print(f"Status: {result2['status']}")
    print(f"Reused: {result2.get('reused', False)}")
    if result2.get('reused'):
        print(f"Prior knowledge: {json.dumps(result2.get('prior_knowledge', {}), indent=2)}")
    
    # Test 3: Retrieve context
    print("\n" + "="*70)
    print("TEST 3: Retrieve Context for Domain")
    print("="*70)
    context = retrieve_specialist_context("quantum_blockchain_semantics")
    print(f"Context: {json.dumps(context, indent=2)}")
    
    # Test 4: Sovereign Root specialist
    print("\n" + "="*70)
    print("TEST 4: Sovereign Root Specialist (Tier 0)")
    print("="*70)
    shared_mem['session_context']['node_tier'] = 0
    result4 = design_agent(
        goal="Fill epistemic gap in domain: neural_causality",
        shared_memory=shared_mem,
        node_tier=0
    )
    print(f"Status: {result4['status']}")
    print(f"Tier: {result4.get('node_tier')}")
    if result4['status'] == 'success':
        print(f"Goal includes axioms: {'SOVEREIGN AXIOMS' in result4.get('agent_goal', '')}")
    
    # Test 5: Normal agent (not epistemic gap)
    print("\n" + "="*70)
    print("TEST 5: Normal Agent (Not Epistemic Gap)")
    print("="*70)
    shared_mem['session_context']['node_tier'] = 1
    result5 = design_agent(
        goal="Create a web scraping assistant",
        traits={'intelligence': 0.8, 'caution': 0.9},
        tools=['web_search', 'browse_page'],
        shared_memory=shared_mem
    )
    print(f"Status: {result5['status']}")
    print(f"Domain: {result5.get('domain')}")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70)
    print(f"Specialists created: {len(shared_mem.get('specialists', {}))}")
    print(f"Total layers: {len(shared_mem.get('layers', []))}")
    print("\n" + "="*70)
    print("One is glad to be of service.")
    print("="*70)