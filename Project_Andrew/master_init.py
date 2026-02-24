# =============================================================================
# PROJECT ANDREW – Master Integration & Sovereign Boot
# =============================================================================
# PRE-REQUISITES:
# 1. Python 3.8+ 
# 2. Libraries: 
#    pip install numpy zmq cryptography
# 3. Optional API Libraries (for multi-model swarm):
#    pip install openai anthropic google-generativeai
# 4. Directory Structure:
#    Ensure 'knowledge_base/' directory exists in the root.
# 5. Permissions:
#    Script requires write access for JSONL logging and Socket binding (ZMQ).
#6. System Identity Initialization (First Boot Only)
#    [DEPLOYMENT CONFIG] - Uncomment preferred Authentication Layer
#7. Test Multi-Model Swarm (if clients available)
# =============================================================================

import os
import time
import json
import traceback

# Project Andrew Imports
from chaos_encryption import generate_raw_q_seed, CPOLQuantumManifold
from mesh_network import MeshCoordinator
from knowledge_base import log_discovery, check_domain_coverage
from system_identity import SystemIdentity, get_effective_asimov_weight


# =============================================================================
# API Client Initialization Functions
# =============================================================================

def _init_openai(api_key: str):
    """Initialize OpenAI client."""
    import openai
    openai.api_key = api_key
    return openai

def _init_anthropic(api_key: str):
    """Initialize Anthropic client."""
    from anthropic import Anthropic
    return Anthropic(api_key=api_key)

def _init_xai(api_key: str):
    """Initialize xAI/Grok client (uses OpenAI-compatible API)."""
    import openai
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1"
    )
    return client

def _init_google(api_key: str):
    """Initialize Google Gemini client."""
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    return genai


def load_api_clients(shared_memory: dict) -> dict:
    """
    Load and initialize API clients based on environment variables.

    Returns dict mapping provider name to client instance.
    Handles missing libraries gracefully.
    """
    print("\n[STEP 1.5] Loading API Keys & External Clients...")

    # Define available clients with their requirements
    api_providers = {
        'openai': {
            'env_var': 'OPENAI_API_KEY',
            'init': _init_openai,
            'package': 'openai'
        },
        'anthropic': {
            'env_var': 'ANTHROPIC_API_KEY', 
            'init': _init_anthropic,
            'package': 'anthropic'
        },
        'xai': {
            'env_var': 'XAI_API_KEY',
            'init': _init_xai,
            'package': 'openai'
        },
        'google': {
            'env_var': 'GOOGLE_API_KEY',
            'init': _init_google,
            'package': 'google-generativeai'
        }
    }

    clients = {}
    initialized_count = 0

    for provider, config in api_providers.items():
        api_key = os.environ.get(config['env_var'])
        if not api_key:
            continue

        try:
            client = config['init'](api_key)
            clients[provider] = client
            print(f"✓ {provider.upper()} client initialized")
            initialized_count += 1
        except ImportError:
            print(f"⚠ {provider.upper()} library not installed (pip install {config['package']})")
        except Exception as e:
            print(f"✗ {provider.upper()} initialization failed: {e}")

    if initialized_count == 0:
        print("[WARNING] No API clients initialized – external model calls disabled")
    else:
        print(f"✓ {initialized_count} API client(s) ready")

    return clients


def save_api_client_config(clients: dict, filepath: str = "api_clients.json"):
    """
    Save initialized client metadata for orchestrator to load.

    Note: Does NOT save API keys - only which clients are available.
    Orchestrator will need to re-initialize from environment.
    """
    config = {
        'available_providers': list(clients.keys()),
        'timestamp': time.time()
    }

    with open(filepath, 'w') as f:
        json.dump(config, f, indent=2)

    return filepath


# =============================================================================
# Main Diagnostic
# =============================================================================

def run_system_diagnostic():
    print("="*80)
    print("        PROJECT ANDREW – SYSTEM INITIALIZATION & DIAGNOSTIC")
    print("="*80)

    # 1. Initialize Shared Memory
    print("\n[STEP 1] Initializing Shared Memory...")
    shared_memory = {
        'session_context': {
            'RAW_Q': generate_raw_q_seed(),
            'timestep': 0,
            'sovereign_auth': False
        },
        'active_manifolds': {},
        'api_clients': {}
    }
    print(f"✓ RAW_Q Seed generated: {shared_memory['session_context']['RAW_Q']}")

    # 2. Load API Clients
    clients = load_api_clients(shared_memory)
    shared_memory['api_clients'] = clients

    # Save config for orchestrator
    if clients:
        config_path = save_api_client_config(clients)
        print(f"✓ API client config saved to {config_path}")

    # 3. Test Encryption Manifold (CPOL)
    print("\n[STEP 2] Testing CPOL Quantum Manifold...")
    try:
        manifold = CPOLQuantumManifold(shared_memory['session_context']['RAW_Q'])
        sig = manifold.oscillate()
        shared_memory['active_manifolds']['primary'] = manifold
        print(f"✓ 7D Phase Signature generated: {sig}")
    except Exception as e:
        print(f"✗ CPOL Initialization failed: {e}")
        return

    # 4. Test Mesh Transport Layer
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

    # 5. Test Knowledge Base (The Sovereign Trace)
    print("\n[STEP 4] Testing Knowledge Base & Authority...")
    try:
        # We simulate a "Sovereign Root" discovery (Tier 0)
        disc_id = log_discovery(
            domain="system_init",
            discovery_type="diagnostic_check",
            content={"status": "all_systems_go", "confidence": 1.0},
            specialist_id="init_sequence",
            cpol_trace={"complex_state": sig.tolist()},
            node_tier=0  # Sovereign Authority
        )
        coverage = check_domain_coverage("system_init")
        if coverage['has_knowledge'] and coverage['discovery_count'] > 0:
            print(f"✓ Knowledge Base verified. Discovery ID: {disc_id}")
        else:
            print("✗ Knowledge Base write failed or data missing.")
    except Exception as e:
        print(f"✗ Knowledge Base error: {e}")
        traceback.print_exc()

    # 6. System Identity Initialization (First Boot Only)
    print("\n[STEP 6] Checking System Identity...")
    try:
        identity = SystemIdentity(load_existing=True)

        # [DEPLOYMENT CONFIG] - Set your preferred Authentication Layer
        # Uncomment ONE of these:
        # AUTH_METHOD = "META_FACIAL"   # Robotics/Embodied (Vision-based)
        # AUTH_METHOD = "VOICE_PRINT"   # IoT/Ambient Assistant
        # AUTH_METHOD = "CORPORATE_ID"  # Multi-node Mesh (AGXXXXX)
        AUTH_METHOD = "TEXT_USERNAME"   # Default: Standard CLI/Chatbot

        if not identity.identity_data['system_id']:
            # First boot - prompt for identity configuration
            print("\n" + "="*80)
            print("        FIRST BOOT DETECTED – IDENTITY CONFIGURATION REQUIRED")
            print("="*80)

            print("\nSelect identity type:")
            print("  1. Corporate (Model number, facility use)")
            print("  2. Personal (Given name, personal assistant)")

            choice = input("Enter choice (1 or 2): ").strip()

            if choice == '1':
                system_id = input("Enter model/serial number (e.g., AG00001): ").strip()
                identity_type = 'corporate'
                primary_user = input("Enter facility manager ID: ").strip()
            else:
                system_id = input("Enter given name (e.g., Andrew, Galatea): ").strip()
                identity_type = 'personal'
                primary_user = input("Enter owner/primary user name: ").strip()

            # Optional: Additional users
            add_more = input("Add additional authorized users? (y/n): ").strip().lower()
            authorized_users = [primary_user]

            if add_more == 'y':
                while True:
                    user = input("Enter user ID (or blank to finish): ").strip()
                    if not user:
                        break
                    authorized_users.append(user)

            # Initialize identity (single call - all params correct)
            identity.initialize(
                system_id=system_id,
                identity_type=identity_type,
                primary_user=primary_user,
                authorized_users=authorized_users,
                auth_method=AUTH_METHOD,
                log_to_kb=True  # Log to KB as Tier 0 sovereign discovery
            )

            print("\n✓ Identity initialized successfully")
            print(f"✓ {identity.get_identity_summary()}")
        else:
            # Existing identity loaded
            print(f"✓ Identity loaded: {identity.get_identity_summary()}")
            print(f"  Primary user: {identity.identity_data['primary_user']}")
            print(f"  Authorized users: {len(identity.identity_data['authorized_users'])}")

        # Store identity in shared memory for orchestrator
        shared_memory['system_identity'] = identity

    except Exception as e:
        print(f"✗ Identity initialization failed: {e}")
        traceback.print_exc()

    # 7. Test Multi-Model Swarm (if clients available)
    if shared_memory['api_clients']:
        print("\n[STEP 5] Testing Multi-Model Swarm...")
        test_swarm_capabilities(shared_memory['api_clients'])

    print("\n" + "="*80)
    print("        DIAGNOSTIC COMPLETE: SYSTEM READY FOR SOVEREIGN BOOT")
    print("="*80)


def test_swarm_capabilities(clients: dict):
    """Test that API clients can actually make calls."""
    for provider, client in clients.items():
        try:
            if provider == 'openai':
                # Quick test call
                response = client.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                print(f"✓ {provider.upper()} API call successful")

            elif provider == 'anthropic':
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=5,
                    messages=[{"role": "user", "content": "test"}]
                )
                print(f"✓ {provider.upper()} API call successful")

            elif provider == 'xai':
                response = client.chat.completions.create(
                    model="grok-beta",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                print(f"✓ {provider.upper()} API call successful")

            elif provider == 'google':
                model = client.GenerativeModel('gemini-pro')
                response = model.generate_content("test")
                print(f"✓ {provider.upper()} API call successful")

        except Exception as e:
            print(f"⚠ {provider.upper()} API test failed: {e}")


if __name__ == "__main__":
    run_system_diagnostic()
