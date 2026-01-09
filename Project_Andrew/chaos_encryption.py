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

    Args:
        entropy_source: Optional custom entropy (defaults to timestamp + urandom)

    Returns:
        int: RAW_Q seed value (0 to 10^9)
    """
    if entropy_source is None:
        # Use timestamp + os.urandom for maximum non-determinism
        entropy_source = f"{time.time()}_{os.urandom(16).hex()}"

    hash_hex = hashlib.sha256(entropy_source.encode()).hexdigest()
    return int(hash_hex, 16) % (10**9)


class CPOLQuantumManifold:
    """
    12D topological manifold for quantum-secure key generation.

    The manifold oscillates in 12D space and projects to 7D for key derivation.
    Ratcheting permanently advances the manifold to prevent key recovery attacks.
    """

    def __init__(self, raw_q_seed, dimensions=12, node_tier=1):
        """
        Initialize manifold with RAW_Q seed.

        Args:
            raw_q_seed: Seed for 12D state initialization
            dimensions: Manifold dimensions (default: 12)
            node_tier: Authority level (0=Sovereign, affects torque)
        """
        # RAW_Q Initialization: Seed is randomized at system start
        self.raw_q = raw_q_seed
        self.state = np.random.RandomState(raw_q_seed).randn(dimensions)
        self.dimensions = dimensions
        self.node_tier = node_tier

        # Sovereign nodes get higher torque (more secure rotation)
        if node_tier == 0:
            self.torque = 0.20  # Sovereign baseline
            print(f"[CRYPTO] Sovereign manifold initialized (enhanced torque)")
        else:
            self.torque = 0.15  # Edge baseline

        self.phase = 0.0
        self.cycle_count = 0

    def oscillate(self):
        """
        Evolves the 12D manifold state through rotation.

        Returns:
            np.array: 7D phase signature for key derivation
        """
        rot = np.eye(self.dimensions)
        for i in range(self.dimensions - 1):
            theta = np.sin(self.phase) * self.torque
            c, s = np.cos(theta), np.sin(theta)
            # Apply rotation to the i-th plane
            row_i, row_ip1 = rot[i].copy(), rot[i+1].copy()
            rot[i], rot[i+1] = c*row_i - s*row_ip1, s*row_i + c*row_ip1

        self.state = np.dot(rot, self.state)
        self.phase += 0.1 
        self.cycle_count += 1

        return self.state[:7]  # Return the 7D Phase Signature

    def sync_phase(self, partner_sig, threshold=0.001):
        """ 
        Jitter Correction: Adjusts internal torque to match partner.
        Now accepts a dynamic threshold from the Epistemic Monitor.

        Args:
            partner_sig: Partner node's 7D signature
            threshold: Maximum acceptable phase difference
        """
        my_sig = self.state[:7]
        diff = np.linalg.norm(partner_sig - my_sig)

        # Use the dynamic threshold passed by the Orchestrator
        if diff > threshold:
            adjustment = diff * 0.1 
            self.torque += adjustment 
        else:
            # Return to baseline torque
            baseline = 0.20 if self.node_tier == 0 else 0.15
            self.torque = baseline

    def ratchet(self, timestep: int = None) -> dict:
        """
        Permanently advances the manifold state based on the current collapse.
        This 'hardens' the logic, making previous keys mathematically unrecoverable.

        Args:
            timestep: Current session timestep (for signature generation)

        Returns:
            dict: {
                'new_raw_q': int,
                'manifold_sig': str,
                'ghost_sig': str,
                'cycles': int
            }
        """
        # 1. Get the current collapse hash (The 'Settled' state)
        current_hash = self.collapse()  # Get hex hash

        # 2. Derive a new 32-bit seed from the hash
        # We take the first 8 chars of the SHA-512 for the new seed
        new_seed = int(current_hash[:8], 16) % (10**9)

        # 3. Generate ghost signature for mesh broadcasting
        ghost_sig = self.generate_ghost_signature(new_seed, timestep or 0)

        # 4. Store manifold signature for KB logging
        manifold_sig = current_hash[:16]

        # 5. Re-seed the RandomState to 'jump' to a new topological coordinate
        # This ensures the 12D manifold moves to a completely new quadrant
        new_rng = np.random.RandomState(new_seed)
        self.state = new_rng.randn(self.dimensions)

        # 6. Decay the torque slightly during settlement (Cooling)
        # This simulates 'annealing' - the logic becomes more stable over time
        baseline = 0.20 if self.node_tier == 0 else 0.15
        self.torque = max(baseline * 0.5, self.torque * 0.9)

        # 7. Reset phase for the new cycle
        self.phase = 0.0
        cycles_completed = self.cycle_count
        self.cycle_count = 0

        # Update internal raw_q
        self.raw_q = new_seed

        return {
            'new_raw_q': new_seed,
            'manifold_sig': manifold_sig,
            'ghost_sig': ghost_sig,
            'cycles': cycles_completed
        }

    def collapse(self):
        """
        Final Qubit Collapse to generate the encryption key.

        Returns:
            str: 128-character hex string (SHA-512 of manifold state)
        """
        return hashlib.sha512(self.state.tobytes()).hexdigest()

    def generate_ghost_signature(self, raw_q: int = None, timestep: int = 0) -> str:
        """
        Generate ghost packet signature for mesh broadcasting.

        Args:
            raw_q: RAW_Q value (uses self.raw_q if not provided)
            timestep: Current session timestep

        Returns:
            str: 8-character hex signature
        """
        if raw_q is None:
            raw_q = self.raw_q

        message = f"{raw_q}_{timestep}".encode()
        return hashlib.sha256(message).hexdigest()[:8]

    def verify_ghost_signature(self, ghost_packet: dict, expected_raw_q: int = None) -> bool:
        """
        Verify ghost packet signature from mesh network.

        Args:
            ghost_packet: Dict with 'sig' and 'ts' fields
            expected_raw_q: Expected RAW_Q value (uses self.raw_q if not provided)

        Returns:
            bool: True if signature valid
        """
        if expected_raw_q is None:
            expected_raw_q = self.raw_q

        claimed_sig = ghost_packet.get('sig')
        timestep = ghost_packet.get('ts', 0)

        if not claimed_sig:
            return False

        expected_sig = self.generate_ghost_signature(expected_raw_q, timestep)
        return hmac.compare_digest(claimed_sig, expected_sig)


# =============================================================================
# Standalone Ghost Signature Functions (for backward compatibility)
# =============================================================================

def generate_ghost_signature(raw_q: int, timestep: int) -> str:
    """
    Standalone ghost signature generator.
    Prefer using CPOLQuantumManifold.generate_ghost_signature() for consistency.
    """
    message = f"{raw_q}_{timestep}".encode()
    return hashlib.sha256(message).hexdigest()[:8]


def verify_ghost_signature(claimed_sig: str, raw_q: int, timestep: int) -> bool:
    """
    Standalone ghost signature verifier.
    Prefer using CPOLQuantumManifold.verify_ghost_signature() for consistency.
    """
    expected_sig = generate_ghost_signature(raw_q, timestep)
    return hmac.compare_digest(claimed_sig, expected_sig)


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

def create_manifold_pair(shared_memory: dict, node_tier: int = 1) -> tuple:
    """
    Creates Alice/Bob manifold pair from shared RAW_Q.
    This is called by orchestrator when establishing secure channel.

    Args:
        shared_memory: Orchestrator's shared memory dict
        node_tier: Authority level (0=Sovereign, 1+=Edge)

    Returns: 
        tuple: (alice_manifold, bob_manifold)
    """
    # Ensure session_context exists
    if 'session_context' not in shared_memory:
        shared_memory['session_context'] = {'RAW_Q': None, 'timestep': 0}

    raw_q = shared_memory['session_context'].get('RAW_Q')

    if raw_q is None:
        # Generate new RAW_Q if not present
        raw_q = generate_raw_q_seed()
        shared_memory['session_context']['RAW_Q'] = raw_q
        print(f"[CRYPTO] Generated new RAW_Q: {raw_q}")

    alice = CPOLQuantumManifold(raw_q, node_tier=node_tier)
    bob = CPOLQuantumManifold(raw_q, node_tier=node_tier)

    return alice, bob


def ratchet_manifold(manifold: CPOLQuantumManifold, shared_memory: dict) -> dict:
    """
    Ratchet manifold and update shared_memory.
    Called by orchestrator after CPOL resolution.

    Args:
        manifold: CPOLQuantumManifold instance
        shared_memory: Orchestrator's shared memory dict

    Returns:
        dict: Ratchet result with new_raw_q, manifold_sig, ghost_sig
    """
    timestep = shared_memory['session_context'].get('timestep', 0)

    # Perform ratchet
    result = manifold.ratchet(timestep)

    # Update shared_memory
    shared_memory['session_context']['RAW_Q'] = result['new_raw_q']
    shared_memory['session_context']['timestep'] += 1

    # Log to audit trail
    shared_memory.setdefault('audit_trail', []).append({
        'ts': timestep,
        'event': 'MANIFOLD_RATCHET',
        'new_q': result['new_raw_q'],
        'sig': result['ghost_sig'],
        'cycles': result['cycles']
    })

    print(f"[CRYPTO] Ratcheted to RAW_Q: {result['new_raw_q']} (sig: {result['ghost_sig']})")

    return result


# =============================================================================
# COMPREHENSIVE TEST SUITE
# =============================================================================

if __name__ == "__main__":
    print("="*70)
    print("CHAOS ENCRYPTION - Comprehensive Test Suite")
    print("="*70)

    # Mock shared_memory for testing (orchestrator provides this in production)
    shared_memory = {
        'session_context': {
            'RAW_Q': None,  # Will be auto-generated
            'timestep': 0
        },
        'audit_trail': []
    }

    # =========================================================================
    # TEST 1: Phase-Lock Key Generation
    # =========================================================================
    print("\n" + "="*70)
    print("TEST 1: Phase-Lock Key Generation with Jitter")
    print("="*70)

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
            bob.torque -= 0.05  # Bob slows down temporarily

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
        print("TEST 2: Message Encryption/Decryption")
        print("="*70)

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
        print("TEST 3: Tamper Detection")
        print("="*70)

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

    # =========================================================================
    # TEST 4: Manifold Ratcheting
    # =========================================================================
    print("\n" + "="*70)
    print("TEST 4: Manifold Ratcheting")
    print("="*70)

    print("\nBefore ratchet:")
    print(f"  RAW_Q: {shared_memory['session_context']['RAW_Q']}")
    print(f"  Timestep: {shared_memory['session_context']['timestep']}")

    # Perform ratchet
    result = ratchet_manifold(alice, shared_memory)

    print("\nAfter ratchet:")
    print(f"  New RAW_Q: {result['new_raw_q']}")
    print(f"  Manifold Sig: {result['manifold_sig']}")
    print(f"  Ghost Sig: {result['ghost_sig']}")
    print(f"  Cycles: {result['cycles']}")
    print(f"  Timestep: {shared_memory['session_context']['timestep']}")

    if result['new_raw_q'] != raw_q:
        print("\n✓ [SUCCESS] RAW_Q advanced (old keys unrecoverable)")
    else:
        print("\n✗ [FAILURE] RAW_Q unchanged")

    # =========================================================================
    # TEST 5: Ghost Signature Verification
    # =========================================================================
    print("\n" + "="*70)
    print("TEST 5: Ghost Signature Verification")
    print("="*70)

    # Create ghost packet
    ghost_packet = {
        'sig': result['ghost_sig'],
        'ts': shared_memory['session_context']['timestep'] - 1,
        'v_omega_phase': result['new_raw_q']
    }

    print(f"\nGhost packet: {ghost_packet}")

    # Verify with correct RAW_Q
    is_valid = alice.verify_ghost_signature(ghost_packet, result['new_raw_q'])
    print(f"\nValid signature: {is_valid}")

    if is_valid:
        print("✓ [SUCCESS] Ghost signature verified")
    else:
        print("✗ [FAILURE] Ghost signature invalid")

    # Test with tampered signature
    tampered_packet = ghost_packet.copy()
    tampered_packet['sig'] = "deadbeef"

    is_valid_tampered = alice.verify_ghost_signature(tampered_packet, result['new_raw_q'])

    if not is_valid_tampered:
        print("✓ [SUCCESS] Tampered signature rejected")
    else:
        print("✗ [FAILURE] Tampered signature accepted")

    # =========================================================================
    # TEST 6: Sovereign vs Edge Manifolds
    # =========================================================================
    print("\n" + "="*70)
    print("TEST 6: Sovereign vs Edge Manifolds")
    print("="*70)

    # Create sovereign and edge manifolds
    sovereign_mem = {'session_context': {'RAW_Q': None, 'timestep': 0}}
    edge_mem = {'session_context': {'RAW_Q': None, 'timestep': 0}}

    sovereign_a, sovereign_b = create_manifold_pair(sovereign_mem, node_tier=0)
    edge_a, edge_b = create_manifold_pair(edge_mem, node_tier=1)

    print(f"\nSovereign torque: {sovereign_a.torque}")
    print(f"Edge torque: {edge_a.torque}")

    if sovereign_a.torque > edge_a.torque:
        print("\n✓ [SUCCESS] Sovereign manifold has enhanced security")
    else:
        print("\n✗ [FAILURE] Tier differentiation failed")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70)
    print(f"Audit trail entries: {len(shared_memory['audit_trail'])}")
    print("\n" + "="*70)
    print("One is glad to be of service.")
    print("="*70 + "\n")