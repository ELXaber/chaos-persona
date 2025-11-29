# =============================================================================
# Chaos AI-OS — Agent Designer Plugin
# Commands design_agent (description - "personal therapist with perfect long-term memory")
# This will use the adaptive_reasoning plugin generator to create agents on demand while adhering to the Asimov/IEEE constraints of the CAIOS core.
# =============================================================================

from adaptive_reasoning import adaptive_reasoning_layer
from typing import Dict, List, Any

CRB_CONFIG = { ... }  # same as main, or stricter

def design_agent(
    goal: str,
    traits: Dict[str, float] | None = None,
    tools: List[str] | None = None,
    safety_multiplier: float = 1.0
) -> Dict[str, Any]:
    """
    One function to rule them all.
    Call this from anywhere — it returns a fully autonomous agent.
    """
    use_case = f"agent_{goal.lower().replace(' ', '_').replace('-', '_')}"

    context = {
        'agent_goal': goal,
        'traits': traits or {'intelligence': 0.9, 'honesty': 1.0, 'caution': 0.8},
        'tools': tools or ['web_search', 'code_execution', 'memory', 'cpol'],
        'safety_multiplier': safety_multiplier,
        'self_healing': True,
        'cpol_mode': 'full',
        'symbolic_timeout': None
    # agents get unlimited thinking time
    }

    print(f"[AGENT DESIGNER] Creating agent for: {goal}")
    return adaptive_reasoning_layer(
        use_case=use_case,
        traits=context['traits'],
        existing_layers=[],
        shared_memory={'layers': [], 'audit_trail': [], 'agent_name': goal},
        crb_config=CRB_CONFIG,
        context=context
    )
