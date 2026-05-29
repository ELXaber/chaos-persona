#V05282026
#!/usr/bin/env python3
"""
CAIOS Inference Wrapper
Simple interactive chat that uses CAIOS.txt as the system prompt and any model client initialized by master_init.py
"""

# Mac OS import readline

import os
import time
import json
import sys

from typing import Dict, Any, List

try:
    import orchestrator as orch
    print("[CAIOS_CHAT] Full Orchestrator loaded successfully.")
    ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    print(f"[CAIOS_CHAT] Orchestrator not loaded: {e}")
    ORCHESTRATOR_AVAILABLE = False

# =============================================================================
# Load shared memory (created by master_init.py)
# =============================================================================

SHARED_MEMORY_FILE = "shared_memory.json"  # optional - if you want to save/load

def load_shared_memory() -> Dict[str, Any]:
    """Load shared memory from file or bootstrap from existing config files."""
    # Try shared_memory.json first
    if os.path.exists(SHARED_MEMORY_FILE):
        try:
            with open(SHARED_MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load shared_memory.json: {e}")

    # Bootstrap from files master_init.py already wrote
    memory = {}

    # Load system identity
    if os.path.exists("system_identity.json"):
        try:
            with open("system_identity.json", "r", encoding="utf-8") as f:
                identity = json.load(f)
            memory['system_identity'] = identity
        except Exception:
            pass

    # Load API client list
    if os.path.exists("api_clients.json"):
        try:
            with open("api_clients.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            # Re-initialize actual clients from environment
            from master_init import load_api_clients
            memory['api_clients'] = load_api_clients(memory)
        except Exception:
            memory['api_clients'] = {}
    else:
        memory['api_clients'] = {}

    # Add Ollama as available client if running
    try:
        import ollama_config
        if ollama_config.check_ollama_available():
            memory['api_clients']['ollama_local'] = 'ollama'
            memory['node_id'] = ollama_config.SYSTEM_ID
    except Exception:
        pass

    return memory

shared_memory = load_shared_memory()

def refresh_and_inject_kb_state():
    """Force reload KB and return summary for injection"""
    try:
        from axiom_manager import create_axiom_manager
        am = create_axiom_manager()
        active = am.list_active_axioms()
        count = len(active)
        shared_memory['kb_state'] = {
            'discoveries': count,
            'has_knowledge': count > 0,
            'last_refresh': time.time()
        }
        summary = f"[KB_STATE discoveries={count} has_knowledge={count > 0}]"
        print(f"[KB] Refreshed: {count} axioms loaded")
        return summary
    except Exception as e:
        print(f"[KB Refresh Warning]: {e}")
        return "[KB_STATE discoveries=0 has_knowledge=False]"

# =============================================================================
# Load CAIOS system prompt
# =============================================================================

def load_caios_prompt() -> str:
    """Read CAIOS.txt as the system prompt, stripping # comments."""
    try:
        with open("CAIOS.txt", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("Error: CAIOS.txt not found in current directory.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CAIOS.txt: {e}")
        sys.exit(1)

    # Strip # comments after reading
    cleaned = []
    for l in content.split('\n'):
        if l.strip().startswith('#'):
            continue  # Skip full comment lines
        if '#' in l:
            l = l[:l.index('#')].rstrip()  # Strip inline comments
        if l.strip():  # Skip now-empty lines
            cleaned.append(l)

    return '\n'.join(cleaned)

system_prompt = load_caios_prompt()

def get_personalized_prompt():
    base_prompt = load_caios_prompt()
    identity = shared_memory.get('system_identity', {})

    # system_identity.json uses 'system_id' not 'system_name'
    name = identity.get('system_id', 
           identity.get('system_name', 'Andrew'))
    owner = identity.get('primary_user', 'User')

    identity_prefix = (
        f"Your name is {name}. "
        f"Your primary authority and owner is {owner}. "
        f"When introducing yourself, state your name and that you serve {owner}."
    )
    return f"{identity_prefix}\n\n{base_prompt}"

# =============================================================================
# Client selection & chat function
# =============================================================================

def select_client(clients: Dict[str, Any]) -> tuple:
    """Let user choose a model from available clients."""
    options = list(clients.keys())

    if not options:
        print("No clients available. Run master_init.py first.")
        sys.exit(1)

    print("\nAvailable models:")
    for i, provider in enumerate(options, 1):
        if provider == 'ollama_local':
            try:
                import ollama
                models = ollama.list().get('models', [])
                model_names = [m['model'] for m in models]
                print(f"  {i}. OLLAMA Local — {len(model_names)} models available")
                if model_names:
                    for j, m in enumerate(model_names, 1):
                        print(f"      {i}.{j} {m}")
            except Exception:
                print(f"  {i}. OLLAMA Local (could not list models)")
        else:
            print(f"  {i}. {provider.upper()}")

    while True:
        try:
            choice = int(input("\nSelect model (number): "))
            if 1 <= choice <= len(options):
                provider = options[choice - 1]
                client = clients[provider]

                if provider == 'ollama_local':
                    try:
                        import ollama
                        models = ollama.list().get('models', [])
                        model_names = [m['model'] for m in models]

                        if not model_names:
                            selected_model = input("No models found. Enter model name (e.g. llama3.2): ") or "llama3.2"
                        elif len(model_names) == 1:
                            selected_model = model_names[0]
                            print(f"Using: {selected_model}")
                        else:
                            for k, m in enumerate(model_names, 1):
                                print(f"  {k}. {m}")
                            m_choice = int(input("Select Ollama model (number): "))
                            selected_model = model_names[m_choice - 1]
                    except Exception as e:
                        print(f"Warning: Could not list Ollama models: {e}")
                        selected_model = input("Enter Ollama model name: ") or "llama3.2"
                    return provider, client, selected_model

                return provider, client, None
            print(f"Please enter a number between 1 and {len(options)}.")
        except ValueError:
            print("Please enter a valid number.")

def chat_with_model(provider: str, client: Any, 
                    messages: List[Dict[str, str]],
                    ollama_model: str = None) -> str:
    """Main entry point: CAIOS Prompt → Orchestrator → Model"""
    user_input = messages[-1]["content"] if messages else ""

    # === 1. Try Full Orchestrator (Preferred Path) ===
    try:
        import orchestrator as orch

        # Pass through the full orchestration pipeline
        result = orch.system_step(
            user_input=user_input,
            prompt_complexity="medium",        # Can be made dynamic later
            api_clients=shared_memory.get('api_clients'),
            user_id=shared_memory.get('active_user')
        )

        # Extract final output
        if isinstance(result, dict):
            # Priority: actual LLM response > abstraction output > raw dict
            output = result.get('llm_response')
            if not output:
                output = result.get('output', '')
            if not output or output == str(result):
                output = "[Andrew] I processed that but couldn't generate a response. Please try rephrasing."
            return output
        else:
            return str(result)

    except Exception as e:
        print(f"[ORCHESTRATOR] Failed: {e} — falling back to direct model")

    # === 2. Fallback: Direct Ollama with full prompt ===
    try:
        import ollama
        from ollama_config import get_cpol_ollama_params

        params = get_cpol_ollama_params(preferred_model=ollama_model)
        full_system_prompt = get_personalized_prompt()

        full_messages = [
            {"role": "system", "content": full_system_prompt}
        ] + [msg for msg in messages if msg.get("role") != "system"]

        response = ollama.chat(
            model=params['model'],
            messages=[
                {"role": "system", "content": identity_prefix + params['system']},
                {"role": "user", "content": user_query}
            ],
            options=params['options']
        )
        result = response.get('message', {}).get('content', '').strip()

    except Exception as e:
        return f"[ERROR] Both orchestrator and direct model failed: {e}"

    try:
        if provider == "openai":
            response = client.chat.completions.create(
                model="gpt-4o",  # change to your preferred model
                messages=messages,
                temperature=0.7,
                max_tokens=2048
            )
            return response.choices[0].message.content.strip()

        elif provider == "anthropic":
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",  # or haiku/opus
                max_tokens=2048,
                messages=messages,
                temperature=0.7
            )
            return response.content[0].text.strip()

        elif provider == "xai":
            response = client.chat.completions.create(
                model="grok-beta",
                messages=messages,
                temperature=0.7,
                max_tokens=2048
            )
            return response.choices[0].message.content.strip()

        elif provider == "google":
            model = client.GenerativeModel("gemini-1.5-pro")  # or gemini-pro
            response = model.generate_content(messages[-1]["content"])  # Gemini API is different
            return response.text.strip()

        else:
            return f"Unsupported provider: {provider}"

    except Exception as e:
        return f"Error during API call: {str(e)}"

# =============================================================================
# Command Palette (Tab Completion)
# =============================================================================

try:
    import readline

    COMMANDS = [
        # Reasoning
        '/show_reasoning', '/trace_mode_verbose', '/status',
        # Abstraction
        '/gearbox', '/lock L0', '/lock L1', '/lock L2', '/lock L3',
        '/mungo-stats', '/invert_idx',
        # Knowledge
        '/axioms', '/axiom_add', '/axiom_refresh', '/rotate axioms',
        # Agents
        '/design_agent', '/regen_raw_q',
        # System
        '/whoami', '/mesh', 'exit', 'quit'
    ]

    def completer(text, state):
        options = [c for c in COMMANDS if c.startswith(text)]
        return options[state] if state < len(options) else None

    readline.set_completer(completer)
    readline.parse_and_bind('tab: complete')
    READLINE_AVAILABLE = True

except ImportError:
    READLINE_AVAILABLE = False  # Windows fallback - readline not available

# =============================================================================
# Main interactive loop
# =============================================================================

def main():
    print("CAIOS Interactive Chat")
    print("=====================")
    if READLINE_AVAILABLE:
        print("Tip: Press Tab to autocomplete / commands")
    print("Type your message and press Enter. Type 'exit' or 'quit' to end.\n")

    # === AUTHENTICATION ===
    if ORCHESTRATOR_AVAILABLE:
        try:
            from orchestrator import prompt_auth, shared_memory as orch_memory
            print("[AUTH] Authentication required.")
            user_id = prompt_auth(orch_memory)
            shared_memory['active_user'] = user_id
            print(f"[AUTH] Welcome, {user_id}.")
        except PermissionError as e:
            print(f"[AUTH] Access denied: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[AUTH] Auth unavailable: {e} — proceeding as guest")
            user_id = "guest"
            shared_memory['active_user'] = user_id
    else:
        user_id = "guest"
        shared_memory['active_user'] = user_id

    # === MODEL SELECTION ===
    clients = shared_memory.get("api_clients", {})
    if not clients:
        print("No API clients found in shared memory.")
        print("Run 'python master_init.py' first to initialize clients.")
        return

    provider, client, ollama_model = select_client(clients)
    print(f"\nUsing: {provider.upper()}")

    # Generate the prompt dynamically at boot
    current_system_prompt = get_personalized_prompt()
    # 2. Initialize conversation with the PERSONALIZED prompt
    conversation = [{"role": "system", "content": current_system_prompt}]

    while True:
        user_input = input("\nYou: ").strip()

        # 1. Exit Check
        if user_input.lower() in ("exit", "quit", "q"):
            print("Goodbye.")
            break

        # 2. LOCAL COMMAND: /whoami
        if user_input.lower() == "/whoami":
            identity = shared_memory.get('system_identity', {})
            name = identity.get('system_name', 'Andrew/Galatea (Uninitialized)')
            owner = identity.get('primary_user', 'Unknown')

            # Pull networking info from shared memory
            node_id = shared_memory.get('node_id', 'Local_Node')
            tier = "0 (Sovereign)" if "Sovereign" in node_id else "1 (Edge)"

            print("\n" + "-"*30)
            print(f"IDENTITY: {name}")
            print(f"AUTHORITY: {owner} (Primary)")
            print(f"NETWORK ID: {node_id}")
            print(f"HIERARCHY: Tier {tier}")
            print(f"KB STATUS: {'Connected' if os.path.exists('knowledge_base') else 'Offline'}")
            print("-"*30)
            continue # Don't send this to the AI, it's for you.

        # 3. LOCAL COMMAND: /debug
        if user_input.lower() == "/debug":
            print("\n" + "="*70)
            print("CAIOS DEBUG INFORMATION")
            print("="*70)

            identity = shared_memory.get('system_identity', {})
            print(f"System ID          : {identity.get('system_id', 'Not set')}")
            print(f"Primary User       : {identity.get('primary_user', 'Not set')}")
            print(f"Auth Method        : {identity.get('auth_method', 'TEXT_USERNAME')}")
            print(f"Current Model      : {ollama_model or 'Unknown'}")

            prompt_len = len(full_system_prompt) if 'full_system_prompt' in locals() else len(get_personalized_prompt())
            print(f"System Prompt Size : {prompt_len} characters")

            print("\nPrompt Preview (first 500 characters):")
            preview = full_system_prompt[:500] if 'full_system_prompt' in locals() else get_personalized_prompt()[:500]
            print(preview + "..." if len(preview) == 500 else preview)

            cpol = shared_memory.get('cpol_state', {})
            print(f"CPOL Status        : {cpol.get('status', 'Unknown')}")

            print("="*70)
            continue

        # 4. LOCAL COMMAND: /mesh
        if user_input.lower() == "/mesh":
            # Assuming mesh_peers is a dict of {node_id: last_seen_timestamp}
            peers = shared_memory.get('mesh_peers', {})
            print("\n" + "="*40)
            print(f"NEIGHBORHOOD DISCOVERY: {len(peers)} Active Nodes")
            print("="*40)
            
            if not peers:
                print("No neighbors detected yet. Pinging...")
            else:
                for peer_id, last_seen in peers.items():
                    latency = round(time.time() - last_seen, 2)
                    status = "ONLINE" if latency < 30 else "STALE"
                    print(f"• [{status}] {peer_id} | Seen: {latency}s ago")
            
            print("="*40)
            continue

        if not user_input:
            continue

        # Add user message
        conversation.append({"role": "user", "content": user_input})

        print("\nThinking...", end="", flush=True)

        # Get response from model
        kb_summary = refresh_and_inject_kb_state()
        response_text = chat_with_model(provider, client, conversation, ollama_model)

        print("\r" + " " * 20 + "\r", end="")  # clear "Thinking..."
        print(f"CAIOS: {response_text}")

        # Add assistant response to history
        conversation.append({"role": "assistant", "content": response_text})


if __name__ == "__main__":
    main()
