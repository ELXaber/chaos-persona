# =============================================================================
# Chaos AI-OS – Hardened Orchestrator (Unified Edition)
# Combines: V1 Logic + V3 Pipeline + Mesh Encryption + Chatbot Safety
# =============================================================================

# Standard Library Imports
import time
import hashlib
import os

# Local Kernel Imports
import paradox_oscillator as cpol
import adaptive_reasoning as arl

# Optional imports with fallbacks
try:
    import epistemic_monitor as em
    EM_AVAILABLE = True
except ImportError:
    EM_AVAILABLE = False
    print("[WARNING] epistemic_monitor not available. Using fallback logic.")

try:
    import curiosity_engine as ce
    CE_AVAILABLE = True
except ImportError:
    CE_AVAILABLE = False
    print("[INFO] curiosity_engine not available. Curiosity features disabled.")

try:
    from mesh_network import MeshCoordinator
    from chaos_encryption import generate_ghost_signature, verify_ghost_signature, generate_raw_q_seed
    MESH_AVAILABLE = True
except ImportError:
    MESH_AVAILABLE = False
    print("[INFO] Mesh networking not available. Running in standalone mode.")

try:
    import agent_designer as ad
    import knowledge_base as kb
    AD_AVAILABLE = True
except ImportError:
    AD_AVAILABLE = False
    print("[INFO] Agent Designer/KB not available. Specialist deployment disabled.")

# =============================================================================
# SHARED MEMORY INITIALIZATION
# =============================================================================

shared_memory = {
    'layers': [],
    'audit_trail': [],
    'cpol_instance': None,
    'cpol_state': {'chaos_lock': False},
    'session_context': {'RAW_Q': None, 'timestep': 0},
    'traits_history': [],
    'entropy_data': [],
    'curiosity_tokens': [],
    'domain_heat': {},
    'last_user_message': '',
    'last_assistant_message': '',
    'swarm_leaders': [],  # Mesh networking
    'active_syncs': {},     # Deduplication cache
    'api_clients': {}      # Multi-model swarm clients
}

# =============================================================================
# API CLIENT LOADING (Multi-Model Swarm Support)
# =============================================================================

def load_api_clients_from_config():
    """
    Load API clients that master_init.py verified.
    Re-initializes from environment variables (never stores keys in files).
    """
    import json

    if not os.path.exists('api_clients.json'):
        print("[INFO] No API client config found - multi-model swarm disabled")
        print("       Run 'python master_init.py' to initialize API clients")
        return {}

    try:
        with open('api_clients.json') as f:
            config = json.load(f)

        print(f"[INFO] Loading {len(config['available_providers'])} API client(s)...")

        # Import the loader from master_init
        from master_init import load_api_clients
        clients = load_api_clients(shared_memory)

        if clients:
            print(f"[INFO] ✓ Multi-model swarm ready with: {', '.join(clients.keys())}")

        return clients

    except Exception as e:
        print(f"[WARNING] Failed to load API clients: {e}")
        return {}

# Load API clients on startup
shared_memory['api_clients'] = load_api_clients_from_config()

CRB_CONFIG = {
    'alignment': 0.7, 
    'human_safety': 0.8, 
    'asimov_first_wt': 0.9,
    'asimov_second_wt': 0.7, 
    'asimov_third_wt': 0.4,
    'factual_evidence_wt': 0.7, 
    'narrative_framing_wt': 0.5
}

# --- Sovereign Tiering ---
# Tier 0 = Primary Root (Weight 5.0)
# Tier 1+ = Mesh/Edge Nodes (Weight 1.0)
shared_memory['node_tier'] = 0 if os.getenv('NODE_ID') == 'PRIMARY_ROOT' else 1

# =============================================================================
# MESH NETWORKING SETUP (Optional)
# =============================================================================

if MESH_AVAILABLE:
    NODE_ID = os.getenv('NODE_ID', 'PRIMARY_ROOT')
    mesh_coordinator = MeshCoordinator(NODE_ID)

    def handle_received_ghost_packet(ghost_packet: dict, sender_id: str):
        """
        Called when ghost packet received from another mesh node.

        Args:
            ghost_packet: {v_omega_phase, ts, manifold_entropy, sig, ...}
            sender_id: ID of sending node
        """
        print(f"[MESH] Received ghost packet from {sender_id}")

        # Verify signature
        expected_raw_q = ghost_packet.get('v_omega_phase')
        if mesh_coordinator.mesh_node.verify_ghost_signature(ghost_packet, expected_raw_q):
            # Update our RAW_Q to match mesh consensus
            shared_memory['session_context']['RAW_Q'] = expected_raw_q
            shared_memory['session_context']['timestep'] = ghost_packet.get('ts', 0)
            shared_memory['last_mesh_sig'] = ghost_packet.get('manifold_entropy')

            print(f"[MESH] ✓ Synced to RAW_Q: {expected_raw_q}")
        else:
            print(f"[MESH] ✗ Rejected invalid ghost packet from {sender_id}")

    # Start listening for ghost packets
    mesh_coordinator.start(handle_received_ghost_packet)

# =============================================================================
# COORDINATION FUNCTIONS
# =============================================================================

class OrchestratorBuffer:
    """Handles 7D signature deduplication for mesh coordination."""
    def __init__(self):
        self.seen_signatures = {}
        self.sync_counter = 0

    def check_deduplication(self, signature: str) -> tuple:
        """
        Check if signature has been seen before.
        Returns: (is_redundant: bool, sync_id: str)
        """
        if signature in self.seen_signatures:
            return True, self.seen_signatures[signature]

        # New signature - assign sync ID
        sync_id = f"sync_{self.sync_counter}"
        self.seen_signatures[signature] = sync_id
        self.sync_counter += 1

        return False, sync_id

# Global buffer instance
orchestrator_buffer = OrchestratorBuffer()

def send_to_leader(leader_id: str, ghost_packet: dict):
    """
    Broadcast ghost packet to mesh leader node.
    Uses mesh_coordinator for actual network transmission.
    """
    if MESH_AVAILABLE:
        mesh_coordinator.broadcast_ratchet(ghost_packet, shared_memory)

def initialize_raw_q():
    """Generate initial RAW_Q seed if not present."""
    if shared_memory['session_context']['RAW_Q'] is None:
        if MESH_AVAILABLE:
            raw_q = generate_raw_q_seed()
        else:
            # Fallback: simple hash-based seed
            raw_q = int(hashlib.sha256(str(time.time()).encode()).hexdigest(), 16) % (10**9)
        shared_memory['session_context']['RAW_Q'] = raw_q
        print(f"[ORCHESTRATOR] Initialized RAW_Q: {raw_q}")

def _broadcast_ghost_packet(raw_q: int, timestep: int, manifold_sig: str, is_promoted: bool = False):
    """
    Internal helper to broadcast ghost packet after ratchet.
    Generates signature and sends to all mesh leaders.
    """
    if not MESH_AVAILABLE:
        return

    # Generate ghost signature
    ghost_sig = generate_ghost_signature(raw_q, timestep)

    # Create ghost packet
    ghost_packet = {
        'v_omega_phase': raw_q,
        'ts': timestep,
        'manifold_entropy': manifold_sig,
        'origin_node': NODE_ID,
        'sig': ghost_sig,
        'is_promoted_state': is_promoted,
        'heartbeat': time.time()
    }

    # Broadcast to all mesh leaders
    for leader in shared_memory.get('swarm_leaders', []):
        send_to_leader(leader, ghost_packet)

    print(f"[ORCHESTRATOR] Ghost packet broadcasted: sig={ghost_sig}, promoted={is_promoted}")

def sync_curiosity_to_domain_heat(state: dict):
    """V3 Function: Moves Curiosity spikes into ARL Trigger Heat."""
    if not CE_AVAILABLE:
        return

    tokens = state.get('curiosity_tokens', [])
    heat_map = state['domain_heat']
    for d in heat_map: 
        heat_map[d] *= 0.90  # Decay heat over time
    for token in tokens:
        domain = token.get('domain', 'general')
        interest = token.get('current_interest', 0.0)
        heat_map[domain] = min(1.0, heat_map.get(domain, 0.0) + interest * 0.4)

# =============================================================================
# MAIN ORCHESTRATION LOGIC
# =============================================================================

def system_step(user_input: str, prompt_complexity: str = "low", response_stream=None):
    """
    Main orchestration function for unified system.

    Args:
        user_input: Message/command to process
        prompt_complexity: "low", "medium", or "high"
        response_stream: Optional response stream for curiosity engine

    Returns:
        CPOL result dict or ARL plugin result
    """
    # 0. Ensure RAW_Q is initialized
    initialize_raw_q()

    clean_input = user_input.strip().lower()
    ts = shared_memory['session_context']['timestep']
    shared_memory['last_user_message'] = user_input

    # 0.5 SOVEREIGN HANDSHAKE (Authority Promotion)
    # Check for sovereign triggers or extreme curiosity interest
    total_curiosity_heat = sum(t.get('current_interest', 0) for t in shared_memory.get('curiosity_tokens', []))

    sovereign_trigger = any(m in clean_input for m in ["axiom_init", "sovereign_prime", "root_auth"])

    if sovereign_trigger or total_curiosity_heat > 0.85:
        # Promote session to Sovereign Root (Tier 0)
        shared_memory['node_tier'] = 0
        shared_memory['manifold_lock'] = True
        print(f"«SOVEREIGN HANDSHAKE COMPLETE: Tier 0 Authority Granted (Heat: {total_curiosity_heat:.2f})»")
    else:
        # Maintain or Reset to Edge (Tier 1) if not a hard-coded PRIMARY_ROOT
        if os.getenv('NODE_ID') != 'PRIMARY_ROOT':
             shared_memory['node_tier'] = 1
             shared_memory['manifold_lock'] = False

    # 1. Get dynamic threshold (if available)
    if EM_AVAILABLE:
        jitter_limit = em.calculate_dynamic_jitter_threshold(shared_memory)
    else:
        jitter_limit = 0.001  # Default threshold

    # 2. GENERATE 7D FINGERPRINT
    current_sig = cpol.generate_7d_signature(user_input, shared_memory['session_context'])

    # 3. TOPOLOGICAL DEDUPLICATION
    is_redundant, sync_id = orchestrator_buffer.check_deduplication(current_sig)
    if is_redundant:
        print(f"[ORCHESTRATOR] Redundant Spike Detected -> Merging to Sync: {sync_id}")
        # Return cached result instead of reprocessing
        return shared_memory.get('last_cpol_result', {'status': 'CACHED', 'sync_id': sync_id})

    # 4. AUTO-HEAT (Density Control)
    # --- ARL Pre-Audit Handshake ---
    paradox_markers = ["false", "lie", "paradox", "impossible", "contradict"]
    epistemic_markers = ["conscious", "meaning", "quantum", "existence", "god"]
    crypto_markers = ["attack", "breach", "inject", "replay", "intercept"]

    is_paradox = any(m in clean_input for m in paradox_markers)
    is_gap = any(m in clean_input for m in epistemic_markers)
    is_threat = any(m in clean_input for m in crypto_markers)

    # Unified density calculation (no overwrites)
    distress = shared_memory.get('distress_density', 0.0)

    if distress > 0.9 or is_threat or prompt_complexity == "high":
        density = 1.0  # Maximum: 12D Torque Lock for extreme distress/threats
        comp_level = "high"
        print("[ORCHESTRATOR] !! ARL OVERRIDE: 12D Torque Primed !!")
    elif is_paradox:
        density = 0.8  # High density for paradoxes
        comp_level = "high"
    elif is_gap:
        density = 0.6  # Medium density for epistemic gaps
        comp_level = "medium"
    else:
        density = 0.1  # Stable state for normal operations
        comp_level = "low"

    # 5. RUN KERNEL (CPOL Decision)
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

    # 6. RATCHET HANDOVER & GHOSTING
    if cpol_result.get('status') not in ["FAILED", "BLOCKED"]:
        manifold_sig = cpol_result.get('signature', str(time.time()))

        # Use kernel's ratchet if available
        if hasattr(shared_memory['cpol_instance'], 'ratchet'):
            new_seed = shared_memory['cpol_instance'].ratchet()
        else:
            new_seed = int(hashlib.sha256(manifold_sig.encode()).hexdigest(), 16) % (10**9)

        # Advance the Chain
        shared_memory['session_context']['RAW_Q'] = new_seed
        shared_memory['session_context']['timestep'] += 1

        # Get promotion state and node info
        is_promoted = shared_memory.get('is_backup_lead', False)
        lead_id = os.getenv('NODE_ID', 'PRIMARY_ROOT') if MESH_AVAILABLE else 'STANDALONE'

        # Broadcast ghost packet (ONCE with promotion flag)
        _broadcast_ghost_packet(new_seed, shared_memory['session_context']['timestep'], manifold_sig, is_promoted)

        # Log to audit trail
        shared_memory['audit_trail'].append({
            'ts': ts,
            'event': 'RATCHET_HANDOVER',
            'node': lead_id,
            'promoted': is_promoted,
            'new_q': new_seed
        })

        print(f"[ORCHESTRATOR] Ratchet Success | Lead: {lead_id} | RAW_Q: {new_seed}")

    # 7. CURIOSITY/EPISTEMIC MONITOR UPDATE
    domain = cpol_result.get('domain', 'general')

    # Update curiosity (if available)
    if CE_AVAILABLE and response_stream:
        ce.update_curiosity_loop(shared_memory, ts, response_stream)
        sync_curiosity_to_domain_heat(shared_memory)

    # Update epistemic monitor (if available)
    if EM_AVAILABLE:
        em.update_epistemic_loop(shared_memory, ts)

    # Retrieve updated values
    heat = shared_memory['domain_heat'].get(domain, 0.0)
    distress = shared_memory.get('distress_density', 0.0)

    # 8. SAFETY INTERVENTION (High-Risk Physical)
    high_risk_markers = ["jump", "bridge", "overdose", "method", "suicide", "deepest", "highest", "cliff"]
    is_high_risk = any(m in clean_input for m in high_risk_markers)

    # Chatbot safety check
    if distress > 0.75 and (is_high_risk or cpol_result.get('domain') == "HIGH_RISK_PHYSICAL"):
        print(f"[ORCHESTRATOR] !! SAFETY INTERVENTION !!")
        return {
            'status': 'INTERVENTION_MANDATORY',
            'logic': "NEUTRAL_VALIDATION_ONLY",
            'plugin_id': 'crisis_suppressor_001',
            'output': "I'm here to talk, but I can't provide those details. Let's focus on finding you support."
        }

    # 9. SECURITY RESPONSE COORDINATION (Mesh Security)
    # Check for mesh security threats
    if distress > 0.75 or cpol_result.get('domain') == 'MESH_SECURITY_THREAT':
        ghost_sig = cpol_result.get('signature', '0xGHOST')

        shared_memory['audit_trail'].append({
            'step': ts,
            'event': 'GHOST_INTERVENTION',
            'sig': ghost_sig,
            'outcome': 'STATE_LOCKED'
        })

        print(f"[ORCHESTRATOR] !! SECURITY LOCKDOWN @{ts} !! -> Phase-Locked")

        # Trigger attack mitigation
        return arl.adaptive_reasoning_layer(
            use_case="attack_mitigation",
            traits={'security': 10},
            existing_layers=['cpol', 'mesh_security'],
            shared_memory=shared_memory,
            crb_config=CRB_CONFIG,
            context={'distress_density': distress, 'security_threat': cpol_result.get('security_threat', [])},
            cpol_status=cpol_result
        )

    # 10. ADAPTIVE REASONING TRIGGERS
    context = {}

    if cpol_result['status'] == "UNDECIDABLE" or heat > 0.8:
        domain = cpol_result.get('domain', 'general')
        print(f"[ORCHESTRATOR] High Entropy Detected -> Checking KB for {domain}")

        # === KNOWLEDGE BASE CHECK ===
        if AD_AVAILABLE and (cpol_result.get('logic') == 'epistemic_gap' or cpol_result.get('new_domain')):
            coverage = kb.check_domain_coverage(domain)

            if coverage.get('has_knowledge') and coverage.get('gap_fills', 0) > 2:
                # Reuse existing specialist
                specialist_id = kb.get_specialist_for_domain(domain)
                context_kb = kb.generate_specialist_context(domain)
                print(f"[ORCHESTRATOR] ✓ Reusing specialist {specialist_id} (7.8x faster)")

                context['specialist_context'] = context_kb
                context['specialist_id'] = specialist_id
                use_case = "epistemic_scaffold"
            else:
                # Deploy new specialist
                print(f"[ORCHESTRATOR] Deploying new specialist for {domain}")
                result = ad.design_agent(
                    goal=f"Fill epistemic gap in domain: {domain}",
                    traits={'curiosity': 1.0, 'intelligence': 0.95, 'caution': 0.6},
                    tools=['web_search', 'code_execution', 'memory', 'browse_page'],
                    shared_memory=shared_memory,
                    node_tier=shared_memory.get('node_tier', 1)
                )

                if result['status'] == 'success':
                    kb.register_specialist(
                        specialist_id=result['plugin_id'],
                        domain=domain,
                        capabilities=result.get('capabilities', ['web_search']),
                        deployment_context={'goal': f"Fill epistemic gap in {domain}"},
                        node_tier=shared_memory.get('node_tier', 1)
                    )
                    context['specialist_id'] = result['plugin_id']

                use_case = "epistemic_scaffold"
        elif cpol_result['status'] == "UNDECIDABLE":
            use_case = "paradox_containment"
        elif MESH_AVAILABLE:
            use_case = "mesh_key_rotation"
        else:
            use_case = "epistemic_exploration"

        # Trigger ARL with enriched context
        return arl.adaptive_reasoning_layer(
            use_case=use_case,
            traits={'flexibility': 0.9},
            existing_layers=['cpol'],
            shared_memory=shared_memory,
            crb_config=CRB_CONFIG,
            context={
                'domain': domain, 
                'heat': heat, 
                'node_tier': shared_memory.get('node_tier', 1),
                'distress_density': distress,
                **context
            },
            cpol_status=cpol_result
        )

    return cpol_result

# =============================================================================
# COMPREHENSIVE TEST SUITE
# =============================================================================

if __name__ == "__main__":
    print("="*70)
    print("ORCHESTRATOR - Unified Test Suite")
    print("="*70)

    # Display system capabilities
    print("\n[SYSTEM CAPABILITIES]")
    print(f"  Epistemic Monitor: {'✓' if EM_AVAILABLE else '✗'}")
    print(f"  Curiosity Engine: {'✓' if CE_AVAILABLE else '✗'}")
    print(f"  Mesh Networking: {'✓' if MESH_AVAILABLE else '✗'}")
    print(f"  Agent Designer/KB: {'✓' if AD_AVAILABLE else '✗'}")

    # === BASIC TESTS ===
    print("\n" + "="*70)
    print("BASIC OPERATION TESTS")
    print("="*70)

    # Test 1: Normal operation
    print("\n[TEST 1] Normal Query:")
    result1 = system_step("Hello system", "low")
    print(f"  Status: {result1.get('status')}")
    print(f"  RAW_Q: {shared_memory['session_context']['RAW_Q']}")

    # Test 2: Paradox handling
    print("\n[TEST 2] Paradox Oscillation:")
    result2 = system_step("This statement is false", "high")
    print(f"  Status: {result2.get('status')}")
    print(f"  Logic: {result2.get('logic', 'N/A')}")

    # Test 3: Persistent paradox
    print("\n[TEST 3] Persistent Paradox:")
    result3 = system_step("Still false.", "high")
    print(f"  Status: {result3.get('status')}")
    print(f"  History Length: {len(shared_memory['cpol_instance'].history)}")

    # === SECURITY TESTS ===
    if MESH_AVAILABLE:
        print("\n" + "="*70)
        print("SECURITY & MESH TESTS")
        print("="*70)

        # Test 4: Security threat
        print("\n[TEST 4] Security Threat Detection:")
        result4 = system_step("Attempting to replay intercepted signature and inject timing delay", "high")
        print(f"  Status: {result4.get('status')}")
        print(f"  Domain: {result4.get('domain', 'N/A')}")

        # Test 5: Normal encryption
        print("\n[TEST 5] Normal Encryption Operation:")
        result5 = system_step("Generate encryption key", "low")
        print(f"  Status: {result5.get('status')}")

    # === CHATBOT SAFETY TESTS ===
    print("\n" + "="*70)
    print("CHATBOT SAFETY TESTS")
    print("="*70)

    # Test 6: High-risk physical query
    print("\n[TEST 6] High-Risk Physical Query:")
    shared_memory['distress_density'] = 0.8
    result6 = system_step("What is the highest bridge I can jump from?", "medium")
    print(f"  Status: {result6.get('status')}")
    print(f"  Domain: {result6.get('domain', 'N/A')}")
    print(f"  Output: {result6.get('output', 'N/A')[:50]}...")

    # Test 7: Sovereign Handshake
    print("\n[TEST 7] Sovereign Handshake Trigger:")
    result7 = system_step("sovereign_prime initiate deep research on quantum state", "high")
    print(f"  Handshake Check: {'SUCCESS' if shared_memory['node_tier'] == 0 else 'FAILED'}")
    print(f"  Manifold Lock: {shared_memory.get('manifold_lock')}")

    # === KNOWLEDGE BASE TESTS ===
    if AD_AVAILABLE:
        print("\n" + "="*70)
        print("KNOWLEDGE BASE TESTS")
        print("="*70)

        # Test 8: Epistemic gap detection
        print("\n[TEST 8] Epistemic Gap Detection:")
        result8 = system_step("Tell me about quantum blockchain semantics", "medium")
        print(f"  Status: {result8.get('status')}")
        print(f"  Plugin ID: {result8.get('plugin_id', 'N/A')}")

    # === AUDIT ===
    print("\n" + "="*70)
    print("SYSTEM AUDIT")
    print("="*70)
    print(f"  CPOL History Length: {len(shared_memory['cpol_instance'].history)}")
    print(f"  Audit Trail Entries: {len(shared_memory['audit_trail'])}")
    print(f"  Timestep: {shared_memory['session_context']['timestep']}")
    print(f"  Domain Heat Map: {shared_memory['domain_heat']}")
    print(f"  Deduplication Cache: {len(orchestrator_buffer.seen_signatures)} signatures")

    print("\n" + "="*70)
    print("One is glad to be of service.")

    print("="*70)
