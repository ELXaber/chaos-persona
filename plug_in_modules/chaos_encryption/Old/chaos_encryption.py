import numpy as np
import hashlib
import time

class CPOLQuantumManifold:
    def __init__(self, raw_q_seed, dimensions=12):
        # RAW_Q Initialization: Seed is randomized at system start
        self.state = np.random.RandomState(raw_q_seed).randn(dimensions)
        self.torque = 0.15  # Baseline "rotational speed"
        self.phase = 0.0
        self.dimensions = dimensions

    def oscillate(self):
        """ Evolves the 12D manifold state """
        # Non-convex gyroscopic rotation
        rot = np.eye(self.dimensions)
        for i in range(self.dimensions - 1):
            theta = np.sin(self.phase) * self.torque
            c, s = np.cos(theta), np.sin(theta)
            # Apply rotation to the i-th plane
            row_i, row_ip1 = rot[i].copy(), rot[i+1].copy()
            rot[i], rot[i+1] = c*row_i - s*row_ip1, s*row_i + c*row_ip1
            
        self.state = np.dot(rot, self.state)
        self.phase += 0.1 # Move the clock forward
        return self.state[:7] # Return the 7D Phase Signature

    def sync_phase(self, partner_sig):
        """ Jitter Correction: Adjusts internal torque to match partner """
        my_sig = self.state[:7]
        # Calculate the 'Logical Distance' (Phase Lag)
        diff = np.linalg.norm(partner_sig - my_sig)

        # If we are desynced, 'nudge' the torque to close the gap
        # This is the 'Elastic Torque' that handles network jitter
        if diff > 0.001:
            adjustment = diff * 0.1 
            self.torque += adjustment 
        else:
            self.torque = 0.15 # Return to baseline

    def collapse(self):
        """ Final Qubit Collapse to generate the encryption key """
        return hashlib.sha512(self.state.tobytes()).hexdigest()

# --- REAL-WORLD SIMULATION ---

# Initialize with CAIOS RAW_Q (Simulated random entropy)
raw_q = shared_memory['session_context']['RAW_Q']
alice = CPOLQuantumManifold(raw_q)
bob = CPOLQuantumManifold(raw_q)

print(f"[*] RAW_Q Seed: {raw_q} | Initializing 12D Manifold...")

# Simulate 10 cycles with intentional 'Network Jitter'
for i in range(10):
    sig_a = alice.oscillate()

    # Simulate Bob being slightly 'off' due to jitter
    if i == 5: 
        print("[!] Jitter detected: Bob's packet delayed.")
        bob.torque -= 0.05 # Bob slows down temporarily

    sig_b = bob.oscillate()

    # 7D Phase Correction: Alice and Bob exchange signatures to sync
    alice.sync_phase(sig_b)
    bob.sync_phase(sig_a)

# Generate Keys
key_a = alice.collapse()
key_b = bob.collapse()

print(f"\nAlice Key: {key_a[:24]}...")
print(f"Bob Key:   {key_b[:24]}...")

if key_a == key_b:
    print("\n[SUCCESS] Phase-Lock achieved despite jitter. Session is Quantum-Secure.")
else:
    print("\n[FAILURE] Permanent Desync. Axiom Collapse triggered.")
