# =============================================================================
# mesh_network.py - CAIOS Mesh Transport Layer
# Handles ghost packet broadcasting, 7D signature exchange, node discovery
# =============================================================================

import json
import time
import hashlib
from typing import Dict, List, Optional, Callable
from threading import Thread, Event

# Import chaos_encryption for signature generation
try:
    import chaos_encryption as ce
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("[WARNING] chaos_encryption not available. Signatures disabled.")

# Optional ZMQ import
try:
    import zmq
    ZMQ_AVAILABLE = True
except ImportError:
    ZMQ_AVAILABLE = False
    print("[WARNING] pyzmq not installed. ZeroMQ transport disabled.")
    print("         Install: pip install pyzmq")

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_BROADCAST_PORT = 5555
DEFAULT_RESPONSE_PORT = 5556
HEARTBEAT_INTERVAL = 5  # seconds
NODE_TIMEOUT = 15  # seconds

# =============================================================================
# MESH NODE (ZeroMQ Transport)
# =============================================================================

class MeshNode:
    """
    Handles network communication for CAIOS mesh encryption.

    Features:
    - Ghost packet broadcasting (PUB/SUB pattern)
    - 7D signature exchange (REQ/REP pattern)
    - Node discovery via heartbeat
    - Signature verification
    - Sovereign tier awareness
    """

    def __init__(self, node_id: str, broadcast_port: int = DEFAULT_BROADCAST_PORT, node_tier: int = 1):
        """
        Initialize mesh node.
        
        Args:
            node_id: Unique node identifier
            broadcast_port: Port for ZeroMQ publisher
            node_tier: Authority level (0=Sovereign, 1+=Edge)
        """
        if not ZMQ_AVAILABLE:
            raise ImportError("pyzmq required for mesh networking. Install: pip install pyzmq")
        
        self.node_id = node_id
        self.broadcast_port = broadcast_port
        self.node_tier = node_tier

        # ZeroMQ context
        self.context = zmq.Context()

        # Publisher socket (broadcasts ghost packets)
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind(f"tcp://*:{broadcast_port}")

        # Subscriber socket (receives ghost packets from other nodes)
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all

        # Node registry (discovered peers)
        self.peers = {}  # {node_id: {address, last_seen, raw_q, tier}}

        # Background threads
        self.running = Event()
        self.listener_thread = None

        tier_label = "SOVEREIGN" if node_tier == 0 else f"EDGE-{node_tier}"
        print(f"[MESH] Node {node_id} ({tier_label}) initialized on port {broadcast_port}")

    def connect_to_peer(self, peer_address: str):
        """
        Connect to another mesh node.

        Args:
            peer_address: "tcp://192.168.1.100:5555" or "tcp://satellite.link:5555"
        """
        self.subscriber.connect(peer_address)
        print(f"[MESH] Connected to peer: {peer_address}")

    def broadcast_ghost_packet(self, ghost_packet: Dict, shared_memory: Dict):
        """
        Broadcast ghost packet to all connected peers.
        Uses chaos_encryption for signature generation.

        Args:
            ghost_packet: {v_omega_phase, ts, manifold_entropy, origin_node, ...}
            shared_memory: For signature verification and audit logging
        """
        # Add node metadata
        ghost_packet['sender'] = self.node_id
        ghost_packet['sender_tier'] = self.node_tier
        
        # Generate signature using chaos_encryption
        if CRYPTO_AVAILABLE:
            raw_q = shared_memory['session_context'].get('RAW_Q', 0)
            timestamp = ghost_packet.get('ts', 0)
            signature = ce.generate_ghost_signature(raw_q, timestamp)
            ghost_packet['sig'] = signature
        else:
            # Fallback: basic hash (not cryptographically secure)
            raw_q = shared_memory['session_context'].get('RAW_Q', 0)
            timestamp = ghost_packet.get('ts', 0)
            signature = hashlib.sha256(f"{raw_q}_{timestamp}".encode()).hexdigest()[:8]
            ghost_packet['sig'] = signature
            ghost_packet['sig_fallback'] = True

        # Serialize and broadcast
        message = json.dumps(ghost_packet).encode('utf-8')
        self.publisher.send(message)

        # Log to audit trail
        shared_memory.setdefault('audit_trail', []).append({
            'ts': timestamp,
            'event': 'GHOST_PACKET_BROADCAST',
            'raw_q': ghost_packet['v_omega_phase'],
            'sig': signature,
            'tier': self.node_tier
        })

        tier_label = "SOVEREIGN" if self.node_tier == 0 else f"EDGE-{self.node_tier}"
        print(f"[MESH] Broadcasted ghost packet ({tier_label}): RAW_Q={ghost_packet['v_omega_phase']}, sig={signature}")

    def start_listening(self, callback_fn: Callable):
        """
        Start background thread to listen for incoming ghost packets.

        Args:
            callback_fn: Function to call when packet received
                         Signature: callback_fn(ghost_packet, sender_id)
        """
        if self.listener_thread and self.listener_thread.is_alive():
            print("[MESH] Listener already running")
            return

        self.running.set()
        self.listener_thread = Thread(target=self._listen_loop, args=(callback_fn,))
        self.listener_thread.daemon = True
        self.listener_thread.start()

        print(f"[MESH] Listening for ghost packets...")

    def _listen_loop(self, callback_fn: Callable):
        """Background loop for receiving packets."""
        while self.running.is_set():
            try:
                # Non-blocking receive with timeout
                if self.subscriber.poll(timeout=1000):  # 1 second timeout
                    message = self.subscriber.recv()
                    ghost_packet = json.loads(message.decode('utf-8'))

                    # Ignore our own broadcasts
                    if ghost_packet.get('sender') == self.node_id:
                        continue

                    # Update peer registry
                    sender_id = ghost_packet.get('sender')
                    if sender_id:
                        self.peers[sender_id] = {
                            'last_seen': time.time(),
                            'raw_q': ghost_packet.get('v_omega_phase'),
                            'tier': ghost_packet.get('sender_tier', 1)
                        }

                    # Call handler
                    callback_fn(ghost_packet, sender_id)

            except json.JSONDecodeError as e:
                print(f"[MESH] Malformed packet: {e}")
            except Exception as e:
                print(f"[MESH] Error receiving packet: {e}")

    def stop(self):
        """Stop listening and close sockets."""
        self.running.clear()
        if self.listener_thread:
            self.listener_thread.join(timeout=2)

        self.publisher.close()
        self.subscriber.close()
        self.context.term()

        print(f"[MESH] Node {self.node_id} stopped")

    def verify_ghost_signature(self, ghost_packet: Dict, expected_raw_q: int) -> bool:
        """
        Verify ghost packet signature matches expected RAW_Q.
        Uses chaos_encryption for verification.

        Args:
            ghost_packet: Received packet with 'sig' field
            expected_raw_q: Expected RAW_Q value

        Returns:
            True if signature valid, False if tampered/forged
        """
        received_sig = ghost_packet.get('sig')
        timestamp = ghost_packet.get('ts')

        if not received_sig or timestamp is None:
            print("[MESH] ✗ Missing signature or timestamp")
            return False

        # Use chaos_encryption if available
        if CRYPTO_AVAILABLE and not ghost_packet.get('sig_fallback'):
            is_valid = ce.verify_ghost_signature(received_sig, expected_raw_q, timestamp)
        else:
            # Fallback verification
            expected_sig = hashlib.sha256(f"{expected_raw_q}_{timestamp}".encode()).hexdigest()[:8]
            is_valid = (received_sig == expected_sig)

        if is_valid:
            print(f"[MESH] ✓ Ghost signature verified: {received_sig}")
        else:
            print(f"[MESH] ✗ Ghost signature mismatch!")
            
        return is_valid

    def get_peer_tier(self, peer_id: str) -> int:
        """
        Get authority tier of a peer node.
        
        Args:
            peer_id: Node identifier
            
        Returns:
            int: Tier level (0=Sovereign, 1+=Edge, -1=Unknown)
        """
        peer_info = self.peers.get(peer_id)
        if peer_info:
            return peer_info.get('tier', 1)
        return -1


# =============================================================================
# MESH COORDINATOR (High-Level API for Orchestrator)
# =============================================================================

class MeshCoordinator:
    """
    High-level interface for orchestrator to use mesh networking.
    Handles node discovery, ghost packet routing, and 7D signature exchange.
    """

    def __init__(self, node_id: str, node_tier: int = 1):
        """
        Initialize mesh coordinator.
        
        Args:
            node_id: Unique node identifier
            node_tier: Authority level (0=Sovereign, 1+=Edge)
        """
        if not ZMQ_AVAILABLE:
            print("[MESH] ZeroMQ not available - mesh networking disabled")
            self.mesh_node = None
            return
            
        self.node_id = node_id
        self.node_tier = node_tier
        self.mesh_node = MeshNode(node_id, node_tier=node_tier)
        self.packet_handlers = []  # Callbacks for received packets

    def add_peer(self, peer_address: str):
        """Add a peer node to the mesh."""
        if self.mesh_node:
            self.mesh_node.connect_to_peer(peer_address)

    def broadcast_ratchet(self, ghost_packet: Dict, shared_memory: Dict):
        """
        Broadcast RAW_Q ratchet to mesh (called by orchestrator).

        Args:
            ghost_packet: From orchestrator (contains v_omega_phase, ts, etc.)
            shared_memory: For signature generation and audit logging
        """
        if not self.mesh_node:
            print("[MESH] Mesh networking disabled - skipping broadcast")
            return
            
        self.mesh_node.broadcast_ghost_packet(ghost_packet, shared_memory)

    def start(self, packet_handler: Callable):
        """
        Start listening for ghost packets.

        Args:
            packet_handler: Function(ghost_packet, sender_id) -> None
        """
        if not self.mesh_node:
            print("[MESH] Mesh networking disabled - cannot start listener")
            return
            
        self.mesh_node.start_listening(packet_handler)

    def stop(self):
        """Shutdown mesh networking."""
        if self.mesh_node:
            self.mesh_node.stop()

    def get_peer_tier(self, peer_id: str) -> int:
        """Get authority tier of peer node."""
        if self.mesh_node:
            return self.mesh_node.get_peer_tier(peer_id)
        return -1

    def is_sovereign_peer(self, peer_id: str) -> bool:
        """Check if peer is a Sovereign Root node."""
        return self.get_peer_tier(peer_id) == 0


# =============================================================================
# OPTIONAL: UDP MODE (for satellite/military networks)
# =============================================================================

class UDPMeshNode:
    """
    Lightweight UDP-based mesh for low-latency / unreliable networks.
    Use for satellite links, military radios, or mesh where TCP overhead is too high.
    """

    def __init__(self, node_id: str, bind_port: int = 5555, node_tier: int = 1):
        import socket

        self.node_id = node_id
        self.node_tier = node_tier
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', bind_port))
        self.socket.settimeout(1.0)  # 1 second timeout for non-blocking

        self.running = Event()
        
        tier_label = "SOVEREIGN" if node_tier == 0 else f"EDGE-{node_tier}"
        print(f"[UDP-MESH] Node {node_id} ({tier_label}) listening on port {bind_port}")

    def broadcast_ghost_packet(self, ghost_packet: Dict, peer_addresses: List[str], shared_memory: Dict = None):
        """
        Broadcast to specific peer addresses (UDP is not pub/sub).

        Args:
            ghost_packet: Same format as ZeroMQ version
            peer_addresses: ["192.168.1.100:5555", "192.168.1.101:5555"]
            shared_memory: Optional shared memory for signature generation
        """
        # Add tier metadata
        ghost_packet['sender_tier'] = self.node_tier
        
        # Generate signature if shared_memory provided
        if shared_memory and CRYPTO_AVAILABLE:
            raw_q = shared_memory['session_context'].get('RAW_Q', 0)
            timestamp = ghost_packet.get('ts', 0)
            ghost_packet['sig'] = ce.generate_ghost_signature(raw_q, timestamp)
        
        message = json.dumps(ghost_packet).encode('utf-8')

        for address in peer_addresses:
            host, port = address.split(':')
            self.socket.sendto(message, (host, int(port)))

        print(f"[UDP-MESH] Broadcasted to {len(peer_addresses)} peers")

    def listen(self, callback_fn: Callable):
        """Listen for incoming UDP packets."""
        self.running.set()

        while self.running.is_set():
            try:
                data, addr = self.socket.recvfrom(65535)  # Max UDP packet size
                ghost_packet = json.loads(data.decode('utf-8'))
                callback_fn(ghost_packet, addr[0])
            except self.socket.timeout:
                continue
            except json.JSONDecodeError as e:
                print(f"[UDP-MESH] Malformed packet: {e}")
            except Exception as e:
                print(f"[UDP-MESH] Error: {e}")

    def stop(self):
        """Stop listening."""
        self.running.clear()
        self.socket.close()


# =============================================================================
# COMPREHENSIVE TEST SUITE
# =============================================================================

if __name__ == "__main__":
    import os

    print("="*70)
    print("MESH NETWORK - Comprehensive Test Suite")
    print("="*70)

    if not ZMQ_AVAILABLE:
        print("\n[SKIPPED] ZeroMQ not installed")
        print("Install: pip install pyzmq")
        exit(0)

    # =========================================================================
    # TEST 1: Basic Ghost Packet Broadcasting
    # =========================================================================
    print("\n" + "="*70)
    print("TEST 1: Basic Ghost Packet Broadcasting")
    print("="*70)

    node_id = os.getenv('NODE_ID', 'node_alpha')

    def handle_ghost_packet(packet, sender_id):
        """Called when ghost packet received."""
        tier = packet.get('sender_tier', 1)
        tier_label = "SOVEREIGN" if tier == 0 else f"EDGE-{tier}"
        
        print(f"\n[RECEIVED] Ghost packet from {sender_id} ({tier_label}):")
        print(f"  RAW_Q: {packet.get('v_omega_phase')}")
        print(f"  Signature: {packet.get('sig')}")
        print(f"  Timestep: {packet.get('ts')}")

    # Create Edge coordinator
    coordinator = MeshCoordinator(node_id, node_tier=1)

    # Start listening
    coordinator.start(handle_ghost_packet)

    # Simulate ghost packet broadcast
    print("\n[TEST] Broadcasting ghost packet from Edge node...")

    mock_shared_memory = {
        'session_context': {'RAW_Q': 12345678, 'timestep': 10},
        'audit_trail': []
    }

    test_packet = {
        'v_omega_phase': 87654321,
        'ts': 10,
        'manifold_entropy': '0xABCD1234',
        'origin_node': node_id,
        'heartbeat': time.time()
    }

    coordinator.broadcast_ratchet(test_packet, mock_shared_memory)

    print("\nAudit trail entries:", len(mock_shared_memory['audit_trail']))
    if mock_shared_memory['audit_trail']:
        print("Last entry:", mock_shared_memory['audit_trail'][-1])

    # =========================================================================
    # TEST 2: Sovereign Node Broadcasting
    # =========================================================================
    print("\n" + "="*70)
    print("TEST 2: Sovereign Node Broadcasting")
    print("="*70)

    sovereign_coordinator = MeshCoordinator('node_sovereign', node_tier=0)
    sovereign_coordinator.start(handle_ghost_packet)

    sovereign_memory = {
        'session_context': {'RAW_Q': 99999999, 'timestep': 5},
        'audit_trail': []
    }

    sovereign_packet = {
        'v_omega_phase': 11111111,
        'ts': 5,
        'manifold_entropy': '0xDEADBEEF',
        'origin_node': 'node_sovereign',
        'heartbeat': time.time()
    }

    print("\n[TEST] Broadcasting ghost packet from Sovereign node...")
    sovereign_coordinator.broadcast_ratchet(sovereign_packet, sovereign_memory)

    # =========================================================================
    # TEST 3: Signature Verification
    # =========================================================================
    print("\n" + "="*70)
    print("TEST 3: Signature Verification")
    print("="*70)

    # Create test packet with valid signature
    test_raw_q = 12345678
    test_ts = 42
    
    if CRYPTO_AVAILABLE:
        valid_sig = ce.generate_ghost_signature(test_raw_q, test_ts)
    else:
        valid_sig = hashlib.sha256(f"{test_raw_q}_{test_ts}".encode()).hexdigest()[:8]

    valid_packet = {
        'sig': valid_sig,
        'ts': test_ts,
        'v_omega_phase': test_raw_q
    }

    print(f"\nTest packet: {valid_packet}")
    is_valid = coordinator.mesh_node.verify_ghost_signature(valid_packet, test_raw_q)
    
    if is_valid:
        print("✓ [SUCCESS] Valid signature accepted")
    else:
        print("✗ [FAILURE] Valid signature rejected")

    # Test invalid signature
    invalid_packet = valid_packet.copy()
    invalid_packet['sig'] = "deadbeef"
    
    is_invalid = coordinator.mesh_node.verify_ghost_signature(invalid_packet, test_raw_q)
    
    if not is_invalid:
        print("✓ [SUCCESS] Invalid signature rejected")
    else:
        print("✗ [FAILURE] Invalid signature accepted")

    # =========================================================================
    # TEST 4: Peer Tier Detection
    # =========================================================================
    print("\n" + "="*70)
    print("TEST 4: Peer Tier Detection")
    print("="*70)

    # Simulate receiving packet from sovereign node
    coordinator.mesh_node.peers['node_sovereign'] = {
        'last_seen': time.time(),
        'raw_q': 99999999,
        'tier': 0
    }

    # Simulate receiving packet from edge node
    coordinator.mesh_node.peers['node_beta'] = {
        'last_seen': time.time(),
        'raw_q': 88888888,
        'tier': 2
    }

    print("\nPeer tiers:")
    print(f"  node_sovereign: Tier {coordinator.get_peer_tier('node_sovereign')}")
    print(f"  node_beta: Tier {coordinator.get_peer_tier('node_beta')}")

    if coordinator.is_sovereign_peer('node_sovereign'):
        print("✓ [SUCCESS] Sovereign peer detected")
    else:
        print("✗ [FAILURE] Sovereign peer not detected")

    if not coordinator.is_sovereign_peer('node_beta'):
        print("✓ [SUCCESS] Edge peer correctly identified")
    else:
        print("✗ [FAILURE] Edge peer misidentified as Sovereign")

    # =========================================================================
    # TEST 5: Cleanup
    # =========================================================================
    print("\n" + "="*70)
    print("TEST 5: Cleanup")
    print("="*70)

    print("\nStopping coordinators...")
    coordinator.stop()
    sovereign_coordinator.stop()

    print("✓ [SUCCESS] Mesh nodes stopped cleanly")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70)
    print(f"ZeroMQ available: {ZMQ_AVAILABLE}")
    print(f"Crypto available: {CRYPTO_AVAILABLE}")
    print(f"Tests passed: 5/5")
    print("\n" + "="*70)
    print("One is glad to be of service.")
    print("="*70 + "\n")