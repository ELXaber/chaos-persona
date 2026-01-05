# =============================================================================
# mesh_network.py - CAIOS Mesh Transport Layer
# Handles ghost packet broadcasting, 7D signature exchange, node discovery
# =============================================================================

import zmq
import json
import time
import hashlib
from typing import Dict, List, Optional
from threading import Thread, Event

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
    """

    def __init__(self, node_id: str, broadcast_port: int = DEFAULT_BROADCAST_PORT):
        self.node_id = node_id
        self.broadcast_port = broadcast_port

        # ZeroMQ context
        self.context = zmq.Context()

        # Publisher socket (broadcasts ghost packets)
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind(f"tcp://*:{broadcast_port}")

        # Subscriber socket (receives ghost packets from other nodes)
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all

        # Node registry (discovered peers)
        self.peers = {}  # {node_id: {address, last_seen, raw_q}}

        # Background threads
        self.running = Event()
        self.listener_thread = None

        print(f"[MESH] Node {node_id} initialized on port {broadcast_port}")

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

        Args:
            ghost_packet: {v_omega_phase, ts, manifold_entropy, origin_node, ...}
            shared_memory: For signature verification
        """
        # Add signature for authenticity
        raw_q = shared_memory['session_context'].get('RAW_Q', 0)
        timestamp = ghost_packet['ts']
        signature = hashlib.sha256(f"{raw_q}_{timestamp}".encode()).hexdigest()[:8]

        ghost_packet['sig'] = signature
        ghost_packet['sender'] = self.node_id

        # Serialize and broadcast
        message = json.dumps(ghost_packet).encode('utf-8')
        self.publisher.send(message)

        print(f"[MESH] Broadcasted ghost packet: RAW_Q={ghost_packet['v_omega_phase']}, sig={signature}")

    def start_listening(self, callback_fn):
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

    def _listen_loop(self, callback_fn):
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

                    # Call handler
                    callback_fn(ghost_packet, ghost_packet.get('sender'))

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

        Args:
            ghost_packet: Received packet with 'sig' field
            expected_raw_q: Expected RAW_Q value

        Returns:
            True if signature valid, False if tampered/forged
        """
        received_sig = ghost_packet.get('sig')
        timestamp = ghost_packet.get('ts')

        if not received_sig or not timestamp:
            return False

        expected_sig = hashlib.sha256(f"{expected_raw_q}_{timestamp}".encode()).hexdigest()[:8]

        if received_sig == expected_sig:
            print(f"[MESH] ✓ Ghost signature verified: {received_sig}")
            return True
        else:
            print(f"[MESH] ✗ Ghost signature mismatch! Expected {expected_sig}, got {received_sig}")
            return False


# =============================================================================
# MESH COORDINATOR (High-Level API for Orchestrator)
# =============================================================================

class MeshCoordinator:
    """
    High-level interface for orchestrator to use mesh networking.
    Handles node discovery, ghost packet routing, and 7D signature exchange.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.mesh_node = MeshNode(node_id)
        self.packet_handlers = []  # Callbacks for received packets

    def add_peer(self, peer_address: str):
        """Add a peer node to the mesh."""
        self.mesh_node.connect_to_peer(peer_address)

    def broadcast_ratchet(self, ghost_packet: Dict, shared_memory: Dict):
        """
        Broadcast RAW_Q ratchet to mesh (called by orchestrator).

        Args:
            ghost_packet: From orchestrator (lines 102-113)
            shared_memory: For signature generation
        """
        self.mesh_node.broadcast_ghost_packet(ghost_packet, shared_memory)

    def start(self, packet_handler):
        """
        Start listening for ghost packets.

        Args:
            packet_handler: Function(ghost_packet, sender_id) -> None
        """
        self.mesh_node.start_listening(packet_handler)

    def stop(self):
        """Shutdown mesh networking."""
        self.mesh_node.stop()


# =============================================================================
# OPTIONAL: UDP MODE (for satellite/military networks)
# =============================================================================

class UDPMeshNode:
    """
    Lightweight UDP-based mesh for low-latency / unreliable networks.
    Use for satellite links, military radios, or mesh where TCP overhead is too high.
    """

    def __init__(self, node_id: str, bind_port: int = 5555):
        import socket

        self.node_id = node_id
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', bind_port))
        self.socket.settimeout(1.0)  # 1 second timeout for non-blocking

        self.running = Event()
        print(f"[UDP-MESH] Node {node_id} listening on port {bind_port}")

    def broadcast_ghost_packet(self, ghost_packet: Dict, peer_addresses: List[str]):
        """
        Broadcast to specific peer addresses (UDP is not pub/sub).

        Args:
            ghost_packet: Same format as ZeroMQ version
            peer_addresses: ["192.168.1.100:5555", "192.168.1.101:5555"]
        """
        message = json.dumps(ghost_packet).encode('utf-8')

        for address in peer_addresses:
            host, port = address.split(':')
            self.socket.sendto(message, (host, int(port)))

        print(f"[UDP-MESH] Broadcasted to {len(peer_addresses)} peers")

    def listen(self, callback_fn):
        """Listen for incoming UDP packets."""
        self.running.set()

        while self.running.is_set():
            try:
                data, addr = self.socket.recvfrom(65535)  # Max UDP packet size
                ghost_packet = json.loads(data.decode('utf-8'))
                callback_fn(ghost_packet, addr[0])
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[UDP-MESH] Error: {e}")

    def stop(self):
        """Stop listening."""
        self.running.clear()
        self.socket.close()


# =============================================================================
# INTEGRATION EXAMPLE
# =============================================================================

if __name__ == "__main__":
    import os

    print("="*70)
    print("MESH NETWORK - Test Mode")
    print("="*70)

    # Simulate two nodes
    node_id = os.getenv('NODE_ID', 'node_alpha')

    def handle_ghost_packet(packet, sender_id):
        """Called when ghost packet received."""
        print(f"\n[RECEIVED] Ghost packet from {sender_id}:")
        print(f"  RAW_Q: {packet.get('v_omega_phase')}")
        print(f"  Signature: {packet.get('sig')}")
        print(f"  Timestep: {packet.get('ts')}")

    # Create coordinator
    coordinator = MeshCoordinator(node_id)

    # Connect to peer (change this to actual peer address)
    # coordinator.add_peer("tcp://192.168.1.100:5555")

    # Start listening
    coordinator.start(handle_ghost_packet)

    # Simulate ghost packet broadcast
    print("\n[TEST] Broadcasting ghost packet...")

    mock_shared_memory = {
        'session_context': {'RAW_Q': 12345678}
    }

    test_packet = {
        'v_omega_phase': 87654321,
        'ts': 10,
        'manifold_entropy': '0xABCD1234',
        'origin_node': node_id,
        'heartbeat': time.time()
    }

    coordinator.broadcast_ratchet(test_packet, mock_shared_memory)

    print("\nListening for 10 seconds...")
    time.sleep(10)

    coordinator.stop()
    print("\n" + "="*70)