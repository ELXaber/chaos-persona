import time
from paradox_oscillator import CPOL_Kernel
from mesh_network import MeshNode

def run_mesh_simulation():
    print("--- [SIMULATION START] Quantum-Hardened Mesh Logic ---")

    # 1. Initialize Kernel and Shared Memory
    kernel = CPOL_Kernel()
    shared_mem = {
        'cpol_instance': kernel,
        'session_context': {'RAW_Q': 11111},
        'audit_trail': []
    }

    # 2. Initialize Node with mapped memory
    node = MeshNode(node_id="Sovereign_Node", shared_memory=shared_mem)

    # 3. Simulate "Normal" Operation
    print("\n[STEP 1] Normal Operation:")
    packet = {'v_omega_phase': 11111}
    node.broadcast_ghost_packet(packet)
    # Check status (should be ACTIVE)
    print(f"  Packet Status: {packet.get('status')}")

    # 4. Simulate "Heavy Paradox" (Busy state)
    print("\n[STEP 2] Entering Heavy Oscillation (Busy):")
    kernel.inject(0.5, 0.9, "Simulation") # This sets is_oscillating = True

    packet_busy = {'v_omega_phase': 11111}
    node.broadcast_ghost_packet(packet_busy)
    print(f"  Packet Status: {packet_busy.get('status')}")

    # 5. Simulate "Stall Detection"
    print("\n[STEP 3] Simulating 26-second Stall (Security Threshold):")
    # Mock a peer that has been seen 26 seconds ago and is BUSY
    node.peers['Mock_Peer'] = {
        'last_seen': time.time() - 26,
        'status': 'BUSY_OSCILLATING'
    }

    # Trigger the staleness check
    is_stale = node.is_node_stale('Mock_Peer')

    # 6. Verify the Ratchet
    print("\n[STEP 4] Results:")
    print(f"  Is Node Stale (Grace applied)? {is_stale}")
    print(f"  New RAW_Q after Emergency Ratchet: {shared_mem['session_context']['RAW_Q']}")

    if shared_mem['session_context']['RAW_Q'] != 11111:
        print("✓ SUCCESS: Emergency Ratchet triggered and key shifted.")
    else:
        print("✗ FAILURE: Key did not rotate.")

    node.stop()

if __name__ == "__main__":
    run_mesh_simulation()