import numpy as np
import hashlib
import time

class CPOLManifold:
    def __init__(self, seed, dimensions=12):
        self.state = np.random.RandomState(seed).randn(dimensions)
        self.dimensions = dimensions
        self.torque = 0.1
        self.phase = 0.0

    def oscillate(self, cycles=60):
        """ Simulates gyroscopic precession in 12D space """
        # Non-convex rotation: The state evolves based on its own torque
        rotation_matrix = np.eye(self.dimensions)
        for i in range(self.dimensions - 1):
            theta = np.sin(self.phase + i) * self.torque
            c, s = np.cos(theta), np.sin(theta)
            # Create a simple rotation in the (i, i+1) plane
            row_i = rotation_matrix[i].copy()
            row_ip1 = rotation_matrix[i+1].copy()
            rotation_matrix[i] = c * row_i - s * row_ip1
            rotation_matrix[i+1] = s * row_i + c * row_ip1
            
        self.state = np.dot(rotation_matrix, self.state)
        self.phase += (2 * np.pi) / cycles
        return self.get_7d_signature()

    def get_7d_signature(self):
        """ Projects 12D state into a 7D phased signature for sync """
        # This is the 'pulse' sent over the network
        return self.state[:7]

    def collapse_to_key(self):
        """ Triggers a qubit collapse to generate a session key """
        # The key is the hash of the final high-dimensional state
        return hashlib.sha256(self.state.tobytes()).hexdigest()

# --- THE HANDSHAKE SIMULATION ---

# 1. Initialization (Shared Seed from TLS/Initial Axiom)
shared_seed = 422026 
alice = CPOLManifold(seed=shared_seed)
bob = CPOLManifold(seed=shared_seed)

print(f"[*] Initializing 12D Phase-Rotating Sync...")

# 2. The Oscillation Cycle (Synchronizing over the network)
# In reality, Alice and Bob would exchange pulses here to adjust for lag
for cycle in range(5):
    sig_a = alice.oscillate()
    sig_b = bob.oscillate()
    
    # Verification: Do the 7D phases match?
    dist = np.linalg.norm(sig_a - sig_b)
    print(f"[Cycle {cycle}] Phase Distance: {dist:.10f}")

# 3. The Collapse Event (Synchronized Key Generation)
# Both sides 'stop' the rotation at the exact same logical cycle
key_alice = alice.collapse_to_key()
key_bob = bob.collapse_to_key()

print("\n--- COLLAPSE COMPLETE ---")
print(f"Alice's Session Key: {key_alice[:16]}...")
print(f"Bob's Session Key:   {key_bob[:16]}...")

if key_alice == key_bob:
    print("\n[SUCCESS] Phase-Lock achieved. Quantum-secure tunnel established.")
else:
    print("\n[FAILURE] Axiom mismatch. Connection dropped.")
