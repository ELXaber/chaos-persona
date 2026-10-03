#V09242026
# =============================================================================
# CAIOS PROJECT ANDREW: Tool Loop for agents
# CPOL-gated system operations with Asimov compliance
# Copyright (c) 2025 Jonathan Schack. License: GPL-3.0 -See LICENSE for details- Contact: X @el_xaber or cai-os.com
# =============================================================================

def run_tool_loop(goal: str, os_controller, max_steps: int = 10) -> Dict[str, Any]:
    """
    Bounded internal agent loop. Called as a single [TOOL:...] dispatch
    from tool_dispatcher.py — invisible to orchestrator.py as more than
    one tool call, so CPOL/safety gating (which fire once per outer
    system_step()) naturally cover the whole sequence as one unit.
    """
    plan = _propose_plan(goal)  # lean LLM call, not query_with_cpol
    if _plan_touches_outside_autonomous_zone(plan) and not _get_single_batch_approval(plan):
        return {'status': 'denied', 'reason': 'Batch plan not approved'}

    results = []
    for step in range(max_steps):
        action = _decide_next_action(goal, results)  # lean call, sees prior results
        if action is None:  # model signals done
            break
        results.append(_dispatch_via_os_controller(action, os_controller))
    return {'status': 'success', 'steps': results}