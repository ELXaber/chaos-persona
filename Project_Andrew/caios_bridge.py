#V06252026
# =============================================================================
# CAIOS Web Bridge — Flask server that connects caios_chat_ui.html to the existing orchestrator/caios_chat.py stack.
#
# Run from the Project_Andrew directory:
#   pip install flask
#   python caios_bridge.py
#
# Then open http://localhost:5000 in your browser.
# The CLI caios_chat.py continues to work alongside this — they share the same orchestrator, shared_memory, and conversation_log.jsonl.
# =============================================================================

import os
import sys
import json
import time
import hashlib
import tempfile
import pathlib
import subprocess
import platform
import atexit
import socket
from datetime import datetime, timezone
from typing import Dict, Any

from flask import (
    Flask, request, jsonify, send_file,
    Response, stream_with_context
)

# MCP client — graceful if caios_mcp_client.py not present yet
try:
    from caios_mcp_client import mcp_tool, mcp_status, get_client as get_mcp_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    def mcp_status(): return {'filesystem_server': False, 'windows_mcp': False}
    def mcp_tool(tool, args): return {'ok': False, 'content': '[MCP] caios_mcp_client.py not found'}

app = Flask(__name__, static_folder='.', static_url_path='')

# =============================================================================
# Bootstrap — same logic as caios_chat.py load_shared_memory()
# =============================================================================

def _bootstrap_shared_memory() -> Dict[str, Any]:
    memory = {}

    if os.path.exists('system_identity.json'):
        try:
            with open('system_identity.json', 'r', encoding='utf-8') as f:
                memory['system_identity'] = json.load(f)
        except Exception:
            pass

    if os.path.exists('api_clients.json'):
        try:
            from master_init import load_api_clients
            memory['api_clients'] = load_api_clients(memory)
        except Exception:
            memory['api_clients'] = {}
    else:
        memory['api_clients'] = {}

    try:
        import ollama_config
        if ollama_config.check_ollama_available():
            memory['api_clients']['ollama_local'] = 'ollama'
            memory['node_id'] = ollama_config.SYSTEM_ID
    except Exception:
        pass

    return memory


try:
    import orchestrator as orch
    shared_memory = orch.shared_memory
    ORCH_AVAILABLE = True
    print('[BRIDGE] Orchestrator loaded')
except ImportError as e:
    shared_memory = _bootstrap_shared_memory()
    ORCH_AVAILABLE = False
    print(f'[BRIDGE] Orchestrator not available ({e}), using bootstrap memory')

# Active session state — keyed by session token
_sessions: Dict[str, Dict] = {}

UPLOAD_DIR = pathlib.Path(tempfile.gettempdir()) / 'caios_uploads'
UPLOAD_DIR.mkdir(exist_ok=True)

# =============================================================================
# Service Startup — Ollama, MCP filesystem server, windows-mcp
#
# Moved here from run_caios.bat/.sh so that BOTH launch paths documented in
# SETUP.md ("run run_caios.bat" and "run python caios_bridge.py directly")
# actually bring the same services up. run_caios.bat now only handles
# one-time environment setup (deps, model pull, first-boot identity) and
# hands off to this on every launch.
#
# Safe to call repeatedly — each service is skipped if already reachable,
# so it's harmless if ollama is already running as a background service,
# or if you start the bridge a second time.
# =============================================================================

_spawned_procs = []

def _port_in_use(host: str, port: int, timeout: float = 1.0) -> bool:
    """
    Raw TCP connect check — works even for SSE/streaming servers that don't
    respond correctly to JSON-RPC probes (e.g. windows-mcp already running).
    Returns True if something is listening on that port, regardless of protocol.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False

def _wait_until_ready(check_fn, timeout=20, interval=0.5) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if check_fn():
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False

def _start_service(name: str, cmd: str, check_fn, timeout: int = 20) -> None:
    try:
        if check_fn():
            print(f'[BRIDGE] {name} already running')
            return
    except Exception:
        pass  # treat a check failure as "not running yet" and try to start it

    print(f'[BRIDGE] Starting {name}...')
    proc = subprocess.Popen(
        cmd, shell=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    _spawned_procs.append(proc)

    if _wait_until_ready(check_fn, timeout=timeout):
        print(f'[BRIDGE] {name} ready')
    else:
        print(f'[BRIDGE] WARNING: {name} did not become ready within {timeout}s '
              f'— continuing anyway, related features will degrade gracefully')

def start_services() -> None:
    """Bring up Ollama + MCP servers if they aren't already reachable."""
    try:
        import ollama_config
        _start_service('Ollama', 'ollama serve', ollama_config.check_ollama_available)
    except ImportError:
        print('[BRIDGE] ollama_config not found — skipping Ollama auto-start')

    if MCP_AVAILABLE:
        client = get_mcp_client()
        if platform.system() == 'Windows':
            if _port_in_use('localhost', 8000):
                print('[BRIDGE] windows-mcp already running on port 8000')
            else:
                _start_service(
                    'windows-mcp',
                    'uvx windows-mcp serve --transport streamable-http --host localhost --port 8000',
                    lambda: _port_in_use('localhost', 8000),
                    timeout=15
                )
        client.reset_availability_cache()
    else:
        print('[BRIDGE] caios_mcp_client.py not found — MCP servers not auto-started')

@atexit.register
def _cleanup_services() -> None:
    for p in _spawned_procs:
        try:
            p.terminate()
        except Exception:
            pass
    if _spawned_procs:
        print('[BRIDGE] Spawned services terminated')

# =============================================================================
# Helpers
# =============================================================================

def _make_token(user_id: str) -> str:
    raw = f"{user_id}:{time.time()}:{os.urandom(8).hex()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _session(token: str) -> Dict:
    return _sessions.get(token, {})


def _get_users() -> Dict[str, Dict]:
    """Load users.json — same file orchestrator uses."""
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {u['id']: u for u in data.get('users', [])}
    except FileNotFoundError:
        return {}


def _list_ollama_models():
    try:
        import ollama
        models = ollama.list().get('models', [])
        return [m['model'] for m in models]
    except Exception:
        return []


def _list_api_providers():
    clients = shared_memory.get('api_clients', {})
    providers = []
    for k in clients:
        if k == 'ollama_local':
            continue
        providers.append(k.upper())
    return providers


def _kb_stats() -> Dict:
    log = pathlib.Path('knowledge_base') / 'discoveries.jsonl'
    total = 0
    if log.exists():
        with open(log, 'r', encoding='utf-8') as f:
            total = sum(1 for line in f if line.strip())
    axioms = 0
    try:
        from axiom_manager import create_axiom_manager
        axioms = len(create_axiom_manager().list_active_axioms())
    except Exception:
        pass
    return {'total_discoveries': total, 'active_axioms': axioms}


def _load_history(n: int = 30):
    log = pathlib.Path('knowledge_base') / 'conversation_log.jsonl'
    if not log.exists():
        return []
    entries = []
    try:
        with open(log, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entries.append(json.loads(line.strip()))
                except Exception:
                    continue
    except Exception:
        return []
    return entries[-n:]


def _log_exchange(user_input: str, response: str,
                  cpol_status: str, domain: str, user_id: str):
    entry = {
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z',
        'user': user_input,
        'andrew': response,
        'cpol_status': cpol_status,
        'domain': domain,
        'user_id': user_id,
    }
    log = pathlib.Path('knowledge_base') / 'conversation_log.jsonl'
    log.parent.mkdir(exist_ok=True)
    with open(log, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')


# =============================================================================
# Routes — startup / static
# =============================================================================

@app.route('/')
def index():
    """Serve the UI HTML file."""
    return send_file('caios_chat_ui.html')


@app.route('/favicon.ico')
def favicon():
    """Suppress favicon 404 noise."""
    return '', 204


# =============================================================================
# Route — GET /api/boot
# Returns everything the UI needs on first load:
#   identity, available models, users list (names only, no hashes), KB stats, whether auth is required.
# =============================================================================

@app.route('/api/boot')
def api_boot():
    # system_identity may be a SystemIdentity object (when orchestrator is loaded)
    # or a plain dict (bootstrap path). Normalise to a dict in both cases.
    _raw_identity = shared_memory.get('system_identity', {})
    if hasattr(_raw_identity, 'identity_data'):
        identity = _raw_identity.identity_data
    else:
        identity = _raw_identity if isinstance(_raw_identity, dict) else {}
    ollama_models = _list_ollama_models()
    api_providers = _list_api_providers()

    # Build flat model list matching caios_chat.py select_client() logic
    models = []
    if ollama_models:
        for m in ollama_models:
            models.append({'id': f'ollama:{m}', 'label': m, 'provider': 'ollama'})
    for p in api_providers:
        models.append({'id': f'api:{p.lower()}', 'label': p, 'provider': 'api'})

    users = _get_users()
    # Only send user IDs to the browser — never password hashes
    user_list = [{'id': uid, 'type': info.get('type', 'user')}
                 for uid, info in users.items()]

    requires_auth = len(users) > 0

    return jsonify({
        'system_id': identity.get('system_id', 'Andrew'),
        'primary_user': identity.get('primary_user', ''),
        'auth_method': identity.get('auth_method', 'TEXT_USERNAME'),
        'requires_auth': requires_auth,
        'models': models,
        'users': user_list,
        'kb': _kb_stats(),
        'orchestrator': ORCH_AVAILABLE,
        'mcp': mcp_status(),
    })


# =============================================================================
# Route — POST /api/auth
# Body: { "username": "...", "password": "..." }
# Mirrors orchestrator._auth_text() logic.
# Returns: { "token": "...", "user_id": "...", "display": "..." }
# =============================================================================

@app.route('/api/auth', methods=['POST'])
def api_auth():
    body = request.get_json(silent=True) or {}
    username = body.get('username', '').strip()
    password = body.get('password', '')

    users = _get_users()

    if not users:
        # No user registry — allow guest
        token = _make_token('guest')
        _sessions[token] = {'user_id': 'guest', 'conversation': []}
        shared_memory['active_user'] = 'guest'
        return jsonify({'token': token, 'user_id': 'guest', 'display': 'Guest'})

    if username not in users:
        return jsonify({'error': 'User not found'}), 401

    user = users[username]
    if 'password_hash' in user:
        submitted_hash = hashlib.sha256(password.encode()).hexdigest()
        if submitted_hash != user['password_hash']:
            return jsonify({'error': 'Incorrect password'}), 401

    token = _make_token(username)
    _sessions[token] = {
        'user_id': username,
        'conversation': [],
        'provider': None,
        'ollama_model': None,
    }
    shared_memory['active_user'] = username

    # Load user profile, increment session count, save
    try:
        if shared_memory.get('user_profile_kb'):
            upkb = shared_memory['user_profile_kb']
            profile = upkb['load'](username)
            profile['session_count'] = profile.get('session_count', 0) + 1
            upkb['save'](username, profile)
            shared_memory['personality_weights'] = profile.get('personality', {})
    except Exception:
        pass

    return jsonify({'token': token, 'user_id': username,
                    'display': username})


# =============================================================================
# Route — POST /api/select_model
# Body: { "token": "...", "model_id": "ollama:qwen3.6:27b" } <- example
# =============================================================================

@app.route('/api/select_model', methods=['POST'])
def api_select_model():
    body = request.get_json(silent=True) or {}
    token = body.get('token', '')
    model_id = body.get('model_id', '')

    sess = _sessions.get(token)
    if sess is None:
        return jsonify({'error': 'Invalid session'}), 401

    if model_id.startswith('ollama:'):
        sess['provider'] = 'ollama_local'
        sess['ollama_model'] = model_id[len('ollama:'):]
    else:
        provider = model_id.split(':')[1] if ':' in model_id else model_id
        sess['provider'] = provider
        sess['ollama_model'] = None

    return jsonify({'ok': True, 'model_id': model_id})


# =============================================================================
# Route — POST /api/upload
# Saves attached file, returns a reference path.
# =============================================================================

@app.route('/api/upload', methods=['POST'])
def api_upload():
    token = request.form.get('token', '')
    if token not in _sessions:
        return jsonify({'error': 'Invalid session'}), 401

    f = request.files.get('file')
    if not f or f.filename == '':
        return jsonify({'error': 'No file'}), 400

    safe_name = pathlib.Path(f.filename).name
    dest = UPLOAD_DIR / safe_name
    f.save(str(dest))

    return jsonify({'filename': safe_name, 'path': str(dest)})


# =============================================================================
# Route — POST /api/chat   (non-streaming version)
# Body: { "token": "...", "message": "...", "attachment_path": null }
# =============================================================================

@app.route('/api/chat', methods=['POST'])
def api_chat():
    body = request.get_json(silent=True) or {}
    token = body.get('token', '')
    user_input = body.get('message', '').strip()
    attachment_path = body.get('attachment_path')

    sess = _sessions.get(token)
    if sess is None:
        return jsonify({'error': 'Invalid session'}), 401
    if not user_input:
        return jsonify({'error': 'Empty message'}), 400

    user_id = sess['user_id']
    provider = sess.get('provider', 'ollama_local')
    ollama_model = sess.get('ollama_model')
    shared_memory['preferred_model'] = ollama_model

    # Prepend attachment context if present
    full_input = user_input
    if attachment_path and pathlib.Path(attachment_path).exists():
        try:
            content = pathlib.Path(attachment_path).read_text(encoding='utf-8', errors='replace')
            truncated = content[:8000]
            full_input = (
                f"[ATTACHED FILE: {pathlib.Path(attachment_path).name}]\n"
                f"{truncated}\n"
                f"[END OF FILE]\n\n"
                f"{user_input}"
            )
        except Exception:
            pass

    # --- Route through orchestrator if available ---
    cpol_status = 'unknown'
    domain = 'general'
    response_text = ''

    if ORCH_AVAILABLE:
        try:
            result = orch.system_step(
                user_input=full_input,
                prompt_complexity='medium',
                api_clients=shared_memory.get('api_clients'),
                user_id=user_id,
            )
            if isinstance(result, dict):
                response_text = result.get('llm_response') or result.get('output', '')
                cpol_status = result.get('status', 'unknown')
                domain = result.get('domain', 'general')
            else:
                response_text = str(result)
        except Exception as e:
            response_text = f'[ORCHESTRATOR ERROR] {e}'

    # --- Fallback: direct Ollama ---
    if not response_text:
        try:
            import ollama
            from caios_chat import get_personalized_prompt, load_recent_history
            sys_prompt = get_personalized_prompt()
            history = load_recent_history(n=6)
            conv = [{'role': 'system', 'content': sys_prompt}] + history
            conv.append({'role': 'user', 'content': full_input})

            from ollama_config import get_cpol_ollama_params
            params = get_cpol_ollama_params(preferred_model=ollama_model)
            resp = ollama.chat(model=params['model'], messages=conv,
                               options=params['options'])
            response_text = resp.get('message', {}).get('content', '').strip()
            cpol_status = 'RESOLVED'
        except Exception as e:
            response_text = f'[ERROR] {e}'

    if not response_text:
        response_text = '[Andrew] No response generated. Please try again.'

    # Log to conversation_log.jsonl
    _log_exchange(user_input, response_text, cpol_status, domain, user_id)

    # KB stats for status bar update
    kb = _kb_stats()

    return jsonify({
        'response': response_text,
        'cpol_status': cpol_status,
        'domain': domain,
        'kb': kb,
    })


# =============================================================================
# Route — GET /api/history?token=...&n=30
# =============================================================================

@app.route('/api/history')
def api_history():
    token = request.args.get('token', '')
    n = int(request.args.get('n', 30))
    if token not in _sessions:
        return jsonify({'error': 'Invalid session'}), 401

    entries = _load_history(n)
    return jsonify({'entries': entries})


# =============================================================================
# Route — GET /api/status?token=...
# =============================================================================

@app.route('/api/status')
def api_status():
    token = request.args.get('token', '')
    sess = _sessions.get(token, {})
    return jsonify({
        'kb': _kb_stats(),
        'cpol': shared_memory.get('last_cpol_result', {}).get('status', 'idle'),
        'model': sess.get('ollama_model', 'none'),
        'provider': sess.get('provider', 'none'),
        'user': sess.get('user_id', 'guest'),
    })


# =============================================================================
# Route — POST /api/mcp
# Lets the UI (and Andrew via tool tags) call MCP tools directly.
# Body: { "token": "...", "tool": "read_file", "args": { "path": "C:/CAIOS/readme.txt" } }
# =============================================================================

@app.route('/api/mcp', methods=['POST'])
def api_mcp():
    body = request.get_json(silent=True) or {}
    token = body.get('token', '')
    if token not in _sessions:
        return jsonify({'error': 'Invalid session'}), 401

    if not MCP_AVAILABLE:
        return jsonify({'ok': False,
                        'content': 'caios_mcp_client.py not found in CAIOS directory'})

    tool = body.get('tool', '')
    args = body.get('args', {})

    if not tool:
        # Return server status if no tool specified
        return jsonify({'status': mcp_status()})

    # KB cleanup commands — routed here so Andrew can call them via tool tags
    if tool == 'kb_sweep':
        try:
            import kb_cleanup
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                kb_cleanup.cmd_sweep(fix=args.get('fix', False))
            return jsonify({'ok': True, 'content': buf.getvalue()})
        except Exception as e:
            return jsonify({'ok': False, 'content': f'kb_sweep error: {e}'})

    if tool == 'kb_purge':
        target = args.get('id') or args.get('pattern', '')
        by_pattern = 'pattern' in args
        if not target:
            return jsonify({'ok': False, 'content': 'kb_purge requires id or pattern'})
        try:
            import kb_cleanup
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                # Auto-confirm in API context (user confirmed via UI)
                import unittest.mock
                with unittest.mock.patch('builtins.input', return_value='yes'):
                    kb_cleanup.cmd_purge(target, by_pattern=by_pattern)
            return jsonify({'ok': True, 'content': buf.getvalue()})
        except Exception as e:
            return jsonify({'ok': False, 'content': f'kb_purge error: {e}'})

    if tool == 'kb_validate':
        try:
            import kb_cleanup
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                kb_cleanup.cmd_validate()
            return jsonify({'ok': True, 'content': buf.getvalue()})
        except Exception as e:
            return jsonify({'ok': False, 'content': f'kb_validate error: {e}'})

    result = mcp_tool(tool, args)

    # Log to audit trail
    shared_memory.setdefault('audit_trail', []).append({
        'ts': time.time(),
        'event': 'MCP_TOOL_CALL',
        'tool': tool,
        'args': args,
        'ok': result.get('ok'),
        'user': _sessions[token].get('user_id'),
    })

    return jsonify(result)


# =============================================================================
# Entry point
# =============================================================================

if __name__ == '__main__':
    print('=' * 60)
    print('  CAIOS Web Bridge')
    print('  Open http://localhost:5000 in your browser')
    print('  Ctrl+C to stop')
    print('=' * 60)
    start_services()
    app.run(host='0.0.0.0', port=5000, debug=False)
