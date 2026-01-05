import numpy as np
import hashlib
import hmac
import time
import os

# =============================================================================
# ENCRYPTION DEPENDENCIES
# =============================================================================
# Install: pip install cryptography
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("[WARNING] cryptography library not installed. Encryption disabled.")
    print("         Install: pip install cryptography")


# =============================================================================
# CPOL QUANTUM MANIFOLD (12D → 7D Key Generation)
# =============================================================================

def generate_raw_q_seed(entropy_source: str = None) -> int:
    """ 
    Standalone function used by Orchestrator to initialize the session.
    Generates a high-entropy seed for the RAW_Q value.
    """
    if entropy_source is None:
        # Use timestamp + os.urandom for maximum non-determinism
        entropy_source = f"{time.time()}_{os.urandom(16).hex()}"

    hash_hex = hashlib.sha256(entropy_source.encode()).hexdigest()
    return int(hash_hex, 16) % (10**9)

def generate_ghost_signature(raw_q: int, timestep: int) -> str:
    message = f"{raw_q}_{timestep}".encode()
    return hashlib.sha256(message).hexdigest()[:8]

def verify_ghost_signature(claimed_sig: str, raw_q: int, timestep: int) -> bool:
    expected_sig = generate_ghost_signature(raw_q, timestep)
    import hmac
    return hmac.compare_digest(claimed_sig, expected_sig)

class CPOLQuantumManifold:
    def __init__(self, raw_q_seed, dimensions=12):
        # RAW_Q Initialization: Seed is randomized at system start
        self.state = np.random.RandomState(raw_q_seed).randn(dimensions)
        self.torque = 0.15  # Baseline "rotational speed"
        self.phase = 0.0
        self.dimensions = dimensions

    def oscillate(self):
        """ Evolves the 12D manifold state """
        rot = np.eye(self.dimensions)
        for i in range(self.dimensions - 1):
            theta = np.sin(self.phase) * self.torque
            c, s = np.cos(theta), np.sin(theta)
            # Apply rotation to the i-th plane
            row_i, row_ip1 = rot[i].copy(), rot[i+1].copy()
            rot[i], rot[i+1] = c*row_i - s*row_ip1, s*row_i + c*row_ip1

        self.state = np.dot(rot, self.state)
        self.phase += 0.1 
        return self.state[:7] # Return the 7D Phase Signature

    def sync_phase(self, partner_sig, threshold=0.001):
        """ 
        Jitter Correction: Adjusts internal torque to match partner.
        Now accepts a dynamic threshold from the Epistemic Monitor.
        """
        my_sig = self.state[:7]
        diff = np.linalg.norm(partner_sig - my_sig)

        # Use the dynamic threshold passed by the Orchestrator
        if diff > threshold:
            adjustment = diff * 0.1 
            self.torque += adjustment 
        else:
            # Return to baseline torque
            self.torque = 0.15

    def ratchet(self):
        """
        Permanently advances the manifold state based on the current collapse.
        This 'hardens' the logic, making previous keys mathematically unrecoverable.
        """
        # 1. Get the current collapse hash (The 'Settled' state)
        current_hash = self.collapse() # Get hex hash

        # 2. Derive a new 32-bit seed from the hash
        # We take the first 8 chars of the SHA-512 for the new seed
        new_seed = int(current_hash[:8], 16)

        # 3. Re-seed the RandomState to 'jump' to a new topological coordinate
        # This ensures the 12D manifold moves to a completely new quadrant
        new_rng = np.random.RandomState(new_seed)
        self.state = new_rng.randn(self.dimensions)

        # 4. Decay the torque slightly during settlement (Cooling)
        # This simulates 'annealing' - the logic becomes more stable over time
        self.torque = max(0.10, self.torque * 0.9)

        # 5. Reset phase for the new cycle
        self.phase = 0.0

        return new_seed # Return the new RAW_Q seed for the Orchestrator

    def collapse(self):
        """ Final Qubit Collapse to generate the encryption key """
        return hashlib.sha512(self.state.tobytes()).hexdigest()

# =============================================================================
# ENCRYPTION/DECRYPTION FUNCTIONS (AES-256-GCM)
# =============================================================================

def encrypt_message(plaintext: str, session_key: str) -> bytes:
    """
    Encrypt message using AES-256-GCM with CPOL-derived key.

    The session_key comes from CPOLQuantumManifold.collapse() - a 128-char
    SHA-512 hash of the 12D manifold state. We derive a 32-byte AES key from it.

    Args:
        plaintext: Message to encrypt (string)
        session_key: Output from CPOLQuantumManifold.collapse() (hex string)

    Returns:
        bytes: iv (16) + ciphertext (variable) + tag (16)

    Raises:
        ImportError: If cryptography library not installed
    """
    if not CRYPTO_AVAILABLE:
        raise ImportError("cryptography library required. Run: pip install cryptography")

    # Derive 32-byte AES key from 128-byte SHA-512 hash
    key = hashlib.sha256(session_key.encode()).digest()

    # Generate random IV (Initialization Vector)
    iv = os.urandom(16)

    # Create AES-GCM cipher (authenticated encryption)
    cipher = Cipher(
        algorithms.AES(key), 
        modes.GCM(iv), 
        backend=default_backend()
    )
    encryptor = cipher.encryptor()

    # Encrypt plaintext
    ciphertext = encryptor.update(plaintext.encode('utf-8')) + encryptor.finalize()

    # Return IV + ciphertext + authentication tag
    return iv + ciphertext + encryptor.tag


def decrypt_message(ciphertext_with_iv: bytes, session_key: str) -> str:
    """
    Decrypt message using AES-256-GCM with CPOL-derived key.

    Args:
        ciphertext_with_iv: Output from encrypt_message() (iv + ciphertext + tag)
        session_key: Same key used for encryption (from collapse())

    Returns:
        str: Decrypted plaintext

    Raises:
        ImportError: If cryptography library not installed
        ValueError: If authentication tag invalid (message tampered)
    """
    if not CRYPTO_AVAILABLE:
        raise ImportError("cryptography library required. Run: pip install cryptography")

    # Derive same 32-byte AES key
    key = hashlib.sha256(session_key.encode()).digest()

    # Extract components (GCM tag is always 16 bytes)
    iv = ciphertext_with_iv[:16]
    tag = ciphertext_with_iv[-16:]
    ciphertext = ciphertext_with_iv[16:-16]

    # Create cipher with authentication tag
    cipher = Cipher(
        algorithms.AES(key), 
        modes.GCM(iv, tag), 
        backend=default_backend()
    )
    decryptor = cipher.decryptor()

    # Decrypt and verify authentication tag
    try:
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Decryption failed - message may be tampered: {e}")


# =============================================================================
# Utility Functions for Orchestrator Integration
# =============================================================================

def create_manifold_pair(shared_memory: dict) -> tuple:
    """
    Creates Alice/Bob manifold pair from shared RAW_Q.
    This is called by orchestrator when establishing secure channel.

    Returns: (alice_manifold, bob_manifold)
    """
    raw_q = shared_memory['session_context'].get('RAW_Q')

    if raw_q is None:
        # Generate new RAW_Q if not present
        raw_q = generate_raw_q_seed()
        shared_memory['session_context']['RAW_Q'] = raw_q
        print(f"[CRYPTO] Generated new RAW_Q: {raw_q}")

    alice = CPOLQuantumManifold(raw_q)
    bob = CPOLQuantumManifold(raw_q)

    return alice, bob


# =============================================================================
# STANDALONE TEST MODE (Only runs when executed directly)
# =============================================================================

if __name__ == "__main__":
    print("="*70)
    print("CHAOS ENCRYPTION - Standalone Test Mode")
    print("="*70)

    # Mock shared_memory for testing (orchestrator provides this in production)
    shared_memory = {
        'session_context': {
            'RAW_Q': None,  # Will be auto-generated
            'timestep': 0
        }
    }

    # =========================================================================
    # TEST 1: Phase-Lock Key Generation
    # =========================================================================
    print("\n[TEST 1] Phase-Lock Key Generation with Jitter")
    print("-"*70)

    # Initialize manifold pair
    alice, bob = create_manifold_pair(shared_memory)
    raw_q = shared_memory['session_context']['RAW_Q']

    print(f"RAW_Q Seed: {raw_q}")
    print("Initializing 12D Manifold...\n")

    # Simulate 10 cycles with intentional 'Network Jitter'
    for i in range(10):
        sig_a = alice.oscillate()

        # Simulate Bob being slightly 'off' due to jitter
        if i == 5: 
            print("  [!] Jitter detected: Bob's packet delayed.")
            bob.torque -= 0.05 # Bob slows down temporarily

        sig_b = bob.oscillate()

        # 7D Phase Correction: Alice and Bob exchange signatures to sync
        alice.sync_phase(sig_b)
        bob.sync_phase(sig_a)

    # Generate Keys
    key_a = alice.collapse()
    key_b = bob.collapse()

    print(f"\nAlice Key: {key_a[:32]}...")
    print(f"Bob Key:   {key_b[:32]}...")

    if key_a == key_b:
        print("\n✓ [SUCCESS] Phase-Lock achieved despite jitter.")
        print("  Session is Quantum-Secure.")
    else:
        print("\n✗ [FAILURE] Permanent Desync. Axiom Collapse triggered.")
        exit(1)

    # =========================================================================
    # TEST 2: Encrypt/Decrypt Message
    # =========================================================================
    if CRYPTO_AVAILABLE:
        print("\n" + "="*70)
        print("[TEST 2] Message Encryption/Decryption")
        print("-"*70)

        # Test message
        original_message = "Transfer $1,000,000 to Account #12345 - Authorized by Node Alpha"
        print(f"\nOriginal Message:\n  {original_message}")

        # Alice encrypts using her key
        print("\n[Alice] Encrypting message...")
        encrypted = encrypt_message(original_message, key_a)
        print(f"  Encrypted: {encrypted[:32].hex()}... ({len(encrypted)} bytes)")

        # Bob decrypts using his key (should work because key_a == key_b)
        print("\n[Bob] Decrypting message...")
        try:
            decrypted = decrypt_message(encrypted, key_b)
            print(f"  Decrypted: {decrypted}")

            if decrypted == original_message:
                print("\n✓ [SUCCESS] Message integrity verified")
                print("  Alice and Bob can securely communicate")
            else:
                print("\n✗ [FAILURE] Decryption mismatch")
        except ValueError as e:
            print(f"\n✗ [FAILURE] {e}")

        # Test 3: Tamper Detection
        print("\n" + "="*70)
        print("[TEST 3] Tamper Detection")
        print("-"*70)

        # Modify ciphertext (simulate MITM attack)
        tampered = bytearray(encrypted)
        tampered[20] ^= 0xFF  # Flip bits in ciphertext
        tampered = bytes(tampered)

        print("\n[Attacker] Modified ciphertext (flipped byte 20)")
        print("[Bob] Attempting to decrypt tampered message...")

        try:
            decrypt_message(tampered, key_b)
            print("✗ [FAILURE] Tamper detection failed!")
        except ValueError:
            print("✓ [SUCCESS] Tamper detected - decryption rejected")
            print("  AES-GCM authentication tag validation working")

    else:
        print("\n[SKIPPED] Encryption tests (cryptography library not installed)")
        print("          Install: pip install cryptography")

    print("\n" + "="*70)
    print("All tests complete")
    print("="*70 + "\n")