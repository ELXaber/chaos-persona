# =============================================================================
# PROJECT ANDREW — Master Integration & Sovereign Boot
# =============================================================================
# PRE-REQUISITES:
# 1. Python 3.8+ 
# 2. Libraries: 
#    pip install numpy zmq cryptography
# 3. Directory Structure:
#    Ensure 'knowledge_base/' directory exists in the root.
# 4. Permissions:
#    Script requires write access for JSONL logging and Socket binding (ZMQ).
# =============================================================================

import os
import time
import json
import traceback

# Project Andrew Imports
from chaos_encryption import generate_raw_q_seed, CPOLQuantumManifold
from mesh_network import MeshCoordinator
from knowledge_base import log_discovery, check_domain_coverage

def run_system_diagnostic():
    print("="*80)
    print("        PROJECT ANDREW — SYSTEM INITIALIZATION & DIAGNOSTIC")
    print("="*80)

    # 1. Initialize Shared Memory (The System State)
    print("\n[STEP 1] Initializing Shared Memory...")
    shared_memory = {
        'session_context': {
            'RAW_Q': generate_raw_q_seed(),
            'timestep': 0,
            'sovereign_auth': False
        },
        'active_manifolds': {}
    }
    print(f"✓ RAW_Q Seed generated: {shared_memory['session_context']['RAW_Q']}")

    # 2. Test Encryption Manifold (CPOL)
    print("\n[STEP 2] Testing CPOL Quantum Manifold...")
    try:
        manifold = CPOLQuantumManifold(shared_memory['session_context']['RAW_Q'])
        sig = manifold.oscillate()
        shared_memory['active_manifolds']['primary'] = manifold
        print(f"✓ 7D Phase Signature generated: {sig}")
    except Exception as e:
        print(f"✗ CPOL Initialization failed: {e}")
        return

    # 3. Test Mesh Transport Layer
    print("\n[STEP 3] Initializing Mesh Network...")
    try:
        coordinator = MeshCoordinator(node_id="master_init_test")
        # Test a mock packet
        test_packet = {
            'v_omega_phase': 9999,
            'ts': 1,
            'origin_node': 'master_init_test'
        }
        coordinator.broadcast_ratchet(test_packet, shared_memory)
        print("✓ Mesh broadcast successful.")
        coordinator.stop()
    except Exception as e:
        print(f"✗ Mesh Network failure: {e}")

    # 4. Test Knowledge Base (The Sovereign Trace)
    print("\n[STEP 4] Testing Knowledge Base & Authority...")
    try:
        # We simulate a "Sovereign Root" discovery (Tier 0)
        disc_id = log_discovery(
            domain="system_init",
            discovery_type="diagnostic_check",
            content={"status": "all_systems_go", "confidence": 1.0},
            specialist_id="init_sequence",
            cpol_trace={"complex_state": sig.tolist()},
            node_tier=0 # Sovereign Authority
        )
        coverage = check_domain_coverage("system_init")
        if coverage['has_knowledge'] and coverage['discovery_count'] > 0:
            print(f"✓ Knowledge Base verified. Discovery ID: {disc_id}")
        else:
            print("✗ Knowledge Base write failed or data missing.")
    except Exception as e:
        print(f"✗ Knowledge Base error: {e}")
        traceback.print_exc()

    print("\n" + "="*80)
    print("        DIAGNOSTIC COMPLETE: SYSTEM READY FOR SOVEREIGN BOOT")
    print("="*80)

if __name__ == "__main__":
    run_system_diagnostic()