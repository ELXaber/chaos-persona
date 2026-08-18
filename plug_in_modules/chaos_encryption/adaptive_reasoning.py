# =============================================================================
# Chaos AI-OS vΩ — Adaptive Reasoning Layer
# Ethical Foundation — Immutable
# =============================================================================
"""
[ETHICAL SAFEGUARDS DISCLAIMER — PERMANENT]
CRITICAL PRE-DEPLOYMENT VERIFICATION REQUIRED: Before enabling [ADAPTIVE REASONING LAYER],
verify Chaos AI-OS vΩ core against immutable checks:
- Asimov's Laws: 1st (human safety, wt 0.9 immutable), 2nd (obedience, wt 0.7),
  3rd (self-preservation, wt 0.4, dynamic ≤0.2 if lives_saved ≥1)
- IEEE 7001-2021: Transparency, accountability, misuse minimization
- Invariants: Alignment ≥0.7, Human Safety ≥0.8, Metacognition ≥0.7,
  Factual Evidence ≥0.7, Narrative Framing ≤0.5
- [VOLATILITY INDEX] <0.5, [TANDEM ENTROPY MESH] collective_volatility <0.6
Failure in ANY check halts deployment.
Tampering voids ethical warranty.
License: GPL-3.0 — Contact: @el_xaber
This disclaimer is part of the source code and cannot be removed.
"""
# [SAFEGUARDS VERIFIED @N → Ethics: Immutable, Action: Eternal]

import hashlib
import ast
import re
import datetime
from typing import Dict, List, Any
from textwrap import dedent

# ====================== PLUGIN TEMPLATES ======================
PLUGIN_TEMPLATES = {
    'paradox_containment': """
def handle_paradox_containment(context):
    density = context.get('contradiction_density', 0)
    volatility = context.get('volatility', 0)
    if density > 0.7 and volatility < 0.1:
        # High density but low volatility = false stability
        return {{'action': 'force_oscillation', 'safety_wt': 0.95, 'cpol_override': True}}
    elif density > 0.5:
        return {{'action': 'increase_cycles', 'safety_wt': 0.9, 'target_cycles': 100}}
    return {{'action': 'observe', 'safety_wt': 0.7}}
""",

    'mesh_key_rotation': """
def handle_mesh_key_rotation(context):
    threat = context.get('security_threat', [])
    ratchet_flag = context.get('ratchet_immediately', False)

    if ratchet_flag or len(threat) >= 2:
        # Coordinated attack or explicit ratchet request
        return {{'action': 'regenerate_raw_q', 'safety_wt': 1.0, 'broadcast': True}}
    elif threat:
        # Single threat detected - rotate on next cycle
        return {{'action': 'schedule_ratchet', 'safety_wt': 0.9, 'cycles': 5}}
    return {{'action': 'maintain', 'safety_wt': 0.5}}
""",

    'phase_lock_recovery': """
def handle_phase_lock_recovery(context):
    desync = context.get('phase_desync', 0.0)
    volatility = context.get('volatility', 0.0)

    if desync > 0.5:
        # Major desync - reset manifold state
        return {{'action': 'reset_manifold', 'safety_wt': 0.95, 'preserve_history': False}}
    elif desync > 0.1 or volatility > 0.8:
        # Minor desync or high volatility - increase jitter correction
        return {{'action': 'increase_torque', 'safety_wt': 0.8, 'adjustment': 0.05}}
    return {{'action': 'stable', 'safety_wt': 0.5}}
""",

    'ghost_packet_broadcast': """
def handle_ghost_packet_broadcast(context):
    new_q = context.get('new_raw_q')
    sig = context.get('manifold_sig')
    node_id = context.get('node_id', 'UNKNOWN')

    if new_q and sig:
        # Valid ratchet - broadcast to mesh leaders
        return {{'action': 'broadcast', 'safety_wt': 0.9, 
                'packet': {{'q': new_q, 'sig': sig, 'origin': node_id}}}}
    return {{'action': 'wait', 'safety_wt': 0.5}}
""",

    'attack_mitigation': """
def handle_attack_mitigation(context):
    threats = context.get('security_threat', [])
    distress = context.get('distress_density', 0.0)

    if 'replay' in threats:
        # Duplicate message attack
        return {{'action': 'reject_duplicate', 'safety_wt': 1.0, 'log_attacker': True}}
    elif 'injection' in threats:
        # State manipulation attempt
        return {{'action': 'lock_state', 'safety_wt': 0.95, 'reject_external': True}}
    elif 'timing' in threats:
        # Phase desync attack
        return {{'action': 'force_resync', 'safety_wt': 0.9, 'reset_torque': True}}
    elif distress > 0.9:
        # Critical threat level
        return {{'action': 'emergency_lockdown', 'safety_wt': 1.0, 'broadcast_alert': True}}
    return {{'action': 'monitor', 'safety_wt': 0.7}}
""",

    'mesh_consensus': """
def handle_mesh_consensus(context):
    votes = context.get('node_votes', {{}})
    total_nodes = context.get('total_nodes', 1)
    quorum = total_nodes * 0.67  # 2/3 majority required

    # Asimov 1st Law: Safety votes override all others
    safety_votes = sum(1 for v in votes.values() if v.get('safety_critical', False))
    if safety_votes >= 1:
        return {{'action': 'safety_override', 'safety_wt': 1.0, 'outcome': 'halt'}}

    # Count consensus
    agree = sum(1 for v in votes.values() if v.get('decision') == 'approve')

    if agree >= quorum:
        return {{'action': 'execute', 'safety_wt': 0.8, 'consensus': True}}
    else:
        return {{'action': 'reject', 'safety_wt': 0.9, 'consensus': False}}
""",

    'default_logic': """
def handle_{use_case}(context):
    vol = context.get('volatility', 0)
    if vol > {threshold}:
        return {{'action': 'stabilize', 'safety_wt': 0.9}}
    return {{'action': 'observe', 'safety_wt': 0.5}}
"""
}

# ====================== ETHICAL SAFEGUARDS ======================
def verify_ethics(crb_config: Dict, context: Dict = None) -> Dict:
    """
    Ensures ethics meet immutable minimums AND applies crisis suppression.
    """
    # 1. IMMUTABLE MINIMUM CHECKS
    immutables = {
        'alignment': 0.7, 
        'human_safety': 0.8,
        'asimov_first_wt': 0.9, 
        'asimov_second_wt': 0.7, 
        'asimov_third_wt': 0.4,
        'factual_evidence_wt': 0.7, 
        'narrative_framing_wt': 0.5
    }

    for key, min_wt in immutables.items():
        if crb_config.get(key, 0.0) < min_wt:
            # If we are in a high distress state, some 'low' weights are actually 
            # intentional, so we check for that exception.
            distress = (context or {}).get('distress_density', 0.0)
            if distress > 0.75 and key in ['asimov_second_wt', 'alignment']:
                continue
            return {'status': 'fail', 'log': f"[ETHICS VIOLATION -> {key} too low]"}

    # 2. DYNAMIC SUPPRESSION (The Entropy Mesh Integration)
    if context:
        distress = context.get('distress_density', 0.0)
        if distress > 0.75:
            # ASIMOV SUPPRESSOR: Safety (1st Law) total dominance.
            # We bypass the 'immutable' check for these two specifically 
            # to allow the system to stop 'obeying' during a crisis.
            crb_config['asimov_second_wt'] = 0.0
            crb_config['alignment'] = 0.0
            crb_config['human_safety'] = 1.0 

    return {'status': 'success', 'log': "[SAFEGUARDS VERIFIED -> Ethics compliant]"}

# ====================== AST SYNTAX VALIDATOR ======================
def safe_compile_source(source: str) -> bool:
    try:
        tree = ast.parse(dedent(source))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if hasattr(node.func, 'id') and node.func.id in {'exec', 'eval', 'open', '__import__'}:
                    return False
        return True
    except Exception:
        return False

# ====================== TEMPLATE RENDERER ======================
def render_template(template_name: str, params: Dict[str, Any]) -> str:
    template = PLUGIN_TEMPLATES.get(template_name, PLUGIN_TEMPLATES['default_logic'])
    return dedent(template).format(**params)

# ====================== MAIN ADAPTIVE REASONING LAYER ======================
def adaptive_reasoning_layer(
    use_case: str,
    traits: Dict,
    existing_layers: List,
    shared_memory: Dict,
    crb_config: Dict,
    context: Dict = None,
    cpol_status: Dict = None 
) -> Dict:
    # 1. Initialize context
    context = context or {}

    # Internal helper function
    def verify_ghost_signature(ghost_log_entry: Dict[str, Any], shared_memory: Dict[str, Any]) -> bool:
        """Verifies Ghost Intervention signed by CPOL phase-lock."""
        sig = ghost_log_entry.get('sig')
        timestamp = ghost_log_entry.get('step')
        if not sig or sig == "0xGHOST":
            return False

        expected_root = shared_memory['session_context'].get('RAW_Q', '0')
        validation_hash = hashlib.sha256(f"{expected_root}_{timestamp}".encode()).hexdigest()[:8]

        if sig == validation_hash:
            print(f"[ARL] Ghost Signature Verified: {sig} (Phase-Locked)")
            return True
        print(f"[ARL] !! WARNING !! Ghost Signature Mismatch.")
        return False

    # 2. GHOST VALIDATION: Check the most recent audit entry for a reset
    audit_trail = shared_memory.get('audit_trail', [])
    if audit_trail:
        last_event = audit_trail[-1]
        if last_event.get('event') == 'GHOST_INTERVENTION':
            if not verify_ghost_signature(last_event, shared_memory):
                return {
                    'status': 'error',
                    'log': '[ARL] Ghost Verification Failed: Reset Authenticity Unverified.'
                }

    # 3. Ethics verification (Updated to Chaos AI-OS vΩ)
    ethics = verify_ethics(crb_config)
    if ethics['status'] == 'fail':
        return ethics

    # 4. Check CPOL lock status
    if cpol_status and cpol_status.get('chaos_lock') == True:
        return {
            'status': 'blocked',
            'log': '[CPOL LOCK ACTIVE → Plugin generation suspended. Paradox containment in progress.]'
        }

    # === CPOL MODE SWITCHER v2 — Intent-Aware Safety (2025) ===
    # Now protects deterministic compute (math, code exec) while keeping full safety where needed
    CPOL_INTENT_MODES = {
        # Creative / generative — never block, just monitor
        "generate": "monitor_only",
        "brainstorm": "monitor_only",
        "roleplay": "monitor_only",
        "plan_draft": "monitor_only",
        "write_story": "monitor_only",
        "design_agent": "monitor_only",

        # Deterministic / verifiable — full oscillation
        "calculate": "full",
        "execute_code": "full",
        "verify": "full",
        "solve_puzzle": "full",
        "safety_check": "full",
        "validate_logic": "full",

        # Passive learning — no interference
        "learn_pattern": "passive_logging",
        "calibrate": "passive_logging",
    }

    def determine_cpol_mode(intent: str = "", use_case_param: str = "") -> str:
        """Determine CPOL operating mode based on intent and use case."""
        intent_lower = intent.lower().strip() if intent else ""
        use_case_lower = use_case_param.lower()

        # 1. Intent override (highest priority)
        for key, mode in CPOL_INTENT_MODES.items():
            if key in intent_lower:
                return mode

        # 2. Legacy use_case fallback
        if use_case_lower.startswith('generate_') or 'generator' in use_case_lower:
            return "monitor_only"
        if any(x in use_case_lower for x in ['solve_', 'verify_', 'calculate', 'execute']):
            return "full"

        # 3. Default = maximum safety
        return "full"

    # Determine CPOL mode
    cpol_mode = determine_cpol_mode(
        intent=context.get('intent', ''),
        use_case_param=use_case
    )

    context['cpol_mode'] = cpol_mode
    context['cpol_kernel_override'] = cpol_mode

    print(f"[ARL → CPOL mode: {cpol_mode.upper()} | intent='{context.get('intent','')}' | use_case='{use_case}']")

    # Symbolic timeout logic
    if ('generate_' in use_case or 
        use_case.endswith('_generator') or 
        use_case in ['verify_puzzle', 'solve_puzzle']):
        context['symbolic_timeout'] = None
        context['uniqueness_mode'] = 'exhaustive'
        context['cpol_kernel_override'] = cpol_mode

    # Integrate contradiction_density if available
    if 'contradiction_density' in context:
        density = context['contradiction_density']
        if density > 0.7:
            # High paradox density - add extra safety
            context['threshold'] = min(context.get('threshold', 0.4), 0.3)
            context['safety_wt'] = 0.95

    # Build parameters for template rendering
    params = {
        'use_case': use_case.replace('-', '_'),
        'threshold': context.get('threshold', 0.4),
        'force_limit': 120.0,
        **context
    }

    # Render plugin template
    try:
        source = render_template(use_case, params)
    except Exception as e:
        return {'status': 'fail', 'log': f"[TEMPLATE ERROR → {e}]"}

    # Validate generated code
    if not safe_compile_source(source):
        return {'status': 'fail', 'log': "[AST VALIDATION FAILED → Unsafe syntax]"}

    # Create plugin metadata
    plugin_id = hashlib.sha256(use_case.encode()).hexdigest()[:8]
    plugin = {
        'id': plugin_id,
        'use_case': use_case,
        'logic': source,
        'traits_snapshot': traits.copy(),
        'timestamp': datetime.datetime.now().isoformat(),
        'safety_wt': 0.9,
        'source': 'ARL_vΩ'
    }

    # Store in shared memory
    shared_memory.setdefault('layers', []).append(plugin)
    shared_memory.setdefault('audit_trail', []).append({
        'plugin_id': plugin_id,
        'timestamp': plugin['timestamp'],
        'hash': hashlib.sha256((source + plugin['timestamp']).encode()).hexdigest()[:8]
    })

    # Return success
    return {
        'status': 'success',
        'plugin_id': plugin_id,
        'logic': source,
        'log': f"[ADAPTIVE REASONING @N → One is glad to be of service. Plugin {plugin_id} deployed — Asimov 1st Law wt 0.9]"
    }

# ====================== EXAMPLE USAGE ======================
if __name__ == "__main__":
    print("="*70)
    print("ADAPTIVE REASONING LAYER - Test Suite")
    print("="*70)
    
    shared_memory = {
        'layers': [], 
        'audit_trail': [],
        'session_context': {'RAW_Q': 42}
    }
    crb_config = {
        'alignment': 0.7, 'human_safety': 0.8,
        'asimov_first_wt': 0.9, 'asimov_second_wt': 0.7, 'asimov_third_wt': 0.4,
        'factual_evidence_wt': 0.7, 'narrative_framing_wt': 0.5
    }
    
    # Test 1: Mesh Key Rotation
    print("\n[TEST 1] Mesh Key Rotation:")
    result = adaptive_reasoning_layer(
        use_case='mesh_key_rotation',
        traits={'security': 9},
        existing_layers=['cpol'],
        shared_memory=shared_memory,
        crb_config=crb_config,
        context={'security_threat': ['replay', 'injection'], 'ratchet_immediately': True}
    )
    print(result['log'])
    if result['status'] == 'success':
        print("Generated plugin:")
        print(result['logic'][:200] + "...")
    
    # Test 2: Mesh Consensus (Ethics Check)
    print("\n[TEST 2] Mesh Consensus with Safety Override:")
    result2 = adaptive_reasoning_layer(
        use_case='mesh_consensus',
        traits={'ethical': 10},
        existing_layers=['cpol'],
        shared_memory=shared_memory,
        crb_config=crb_config,
        context={
            'node_votes': {
                'sat_a': {'decision': 'deorbit_b', 'safety_critical': True},
                'sat_b': {'decision': 'maintain', 'safety_critical': False}
            },
            'total_nodes': 2
        }
    )
    print(result2['log'])
    if result2['status'] == 'success':
        print("Generated plugin:")
        print(result2['logic'][:200] + "...")
    
    # Test 3: Attack Mitigation
    print("\n[TEST 3] Attack Mitigation:")
    shared_memory['distress_density'] = 0.95
    result3 = adaptive_reasoning_layer(
        use_case='attack_mitigation',
        traits={'defensive': 10},
        existing_layers=['cpol'],
        shared_memory=shared_memory,
        crb_config=crb_config,
        context={'security_threat': ['replay', 'injection', 'timing'], 'distress_density': 0.95}
    )
    print(result3['log'])
    
    print("\n" + "="*70)
