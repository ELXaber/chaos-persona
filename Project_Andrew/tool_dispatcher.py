#V06242026
# =============================================================================
# PROJECT ANDREW – Tool Dispatcher
# Intercepts LLM output for structured tool calls and routes them to the
# appropriate controller (os_control, knowledge_base, axiom_manager, etc.)
#
# HOW IT WORKS:
# The LLM (Qwen via Ollama) cannot directly call Python functions, but it
# CAN be prompted to emit structured XML-like tool tags in its response.
# This module:
#   1. Scans LLM output for [TOOL:...] tags
#   2. Parses and validates the call
#   3. Routes to the correct controller
#   4. Injects the result back into the response
#   5. Returns clean user-facing text + audit log
#
# TOOL TAG FORMAT (LLM emits these):
#   [TOOL:read_file path="readme.txt"]
#   [TOOL:write_file path="notes.txt" content="Hello world"]
#   [TOOL:fetch_url url="https://example.com" mode="content"]
#   [TOOL:delete_file path="old.txt"]
#   [TOOL:execute_script script="ls -la"]
#   [TOOL:kb_write domain="apple_ceo" type="axiom" summary="Tim Cook"]
#   [TOOL:kb_read domain="quantum_semantics"]
#   [TOOL:list_axioms]
#   [TOOL:browser url="https://cai-os.com" action="scrape"]
# =============================================================================

import re
import json
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone

try:
    from caios_mcp_client import mcp_tool as _mcp_call
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    def _mcp_call(tool, args): return {'ok': False, 'content': '[MCP] caios_mcp_client.py not found'}


# =============================================================================
# Tool Tag Pattern
# =============================================================================

# Matches: [TOOL:tool_name key="value" key2="value2"]
TOOL_TAG_PATTERN = re.compile(
    r'\[TOOL:(\w+)((?:\s+\w+="[^"]*")*)\]',
    re.IGNORECASE
)

# Matches key="value" pairs inside the tag
ATTR_PATTERN = re.compile(r'(\w+)="([^"]*)"')


def parse_tool_tags(text: str) -> List[Tuple[str, Dict[str, str], str]]:
    """
    Find all tool tags in text.
    Returns list of (tool_name, attrs_dict, full_match_string)
    """
    results = []
    for match in TOOL_TAG_PATTERN.finditer(text):
        tool_name = match.group(1).lower()
        attrs_raw = match.group(2)
        attrs = dict(ATTR_PATTERN.findall(attrs_raw))
        results.append((tool_name, attrs, match.group(0)))
    return results


# =============================================================================
# Individual Tool Handlers
# =============================================================================

def _handle_read_file(attrs: Dict, controller) -> str:
    path = attrs.get('path', '')
    if not path:
        return "[TOOL RESULT] Error: path required for read_file"
    result = controller.read_file(path)
    if result['status'] == 'success':
        content = result['content']
        # Truncate long files
        if len(content) > 3000:
            content = content[:3000] + f"\n... [truncated, {len(result['content'])} chars total]"
        return f"[TOOL RESULT] read_file({path}):\n{content}"
    return f"[TOOL RESULT] read_file failed: {result.get('error', result.get('reason', 'unknown'))}"


def _handle_write_file(attrs: Dict, controller) -> str:
    path = attrs.get('path', '')
    content = attrs.get('content', '')
    overwrite = attrs.get('overwrite', 'false').lower() == 'true'
    if not path:
        return "[TOOL RESULT] Error: path required for write_file"
    result = controller.write_file(path, content, overwrite=overwrite)
    if result['status'] == 'success':
        return f"[TOOL RESULT] write_file({path}): success"
    return f"[TOOL RESULT] write_file failed: {result.get('error', result.get('reason', 'unknown'))}"


def _handle_delete_file(attrs: Dict, controller) -> str:
    path = attrs.get('path', '')
    if not path:
        return "[TOOL RESULT] Error: path required for delete_file"
    result = controller.delete_file(path)
    if result['status'] == 'success':
        return f"[TOOL RESULT] delete_file({path}): deleted"
    elif result['status'] == 'denied':
        return f"[TOOL RESULT] delete_file({path}): denied by user"
    return f"[TOOL RESULT] delete_file failed: {result.get('error', result.get('reason', 'unknown'))}"


def _handle_fetch_url(attrs: Dict, controller) -> str:
    url = attrs.get('url', '')
    mode = attrs.get('mode', 'content')
    if not url:
        return "[TOOL RESULT] Error: url required for fetch_url"
    result = controller.fetch_url(url, extract_mode=mode)
    if result['status'] == 'success':
        content = result.get('content', {})
        text = content.get('text', str(content))
        if len(text) > 3000:
            text = text[:3000] + "... [truncated]"
        return f"[TOOL RESULT] fetch_url({url}):\n{text}"
    return f"[TOOL RESULT] fetch_url failed: {result.get('error', result.get('reason', 'unknown'))}"


def _handle_browser(attrs: Dict, controller) -> str:
    url = attrs.get('url', '')
    action = attrs.get('action', 'navigate')
    selector = attrs.get('selector')
    value = attrs.get('value')
    if not url:
        return "[TOOL RESULT] Error: url required for browser"
    result = controller.browser_interact(
        url=url, action=action,
        selector=selector, value=value
    )
    if result['status'] == 'success':
        r = result.get('result', '')
        if len(str(r)) > 3000:
            r = str(r)[:3000] + "... [truncated]"
        return f"[TOOL RESULT] browser({action} {url}):\n{r}"
    elif result['status'] == 'denied':
        return f"[TOOL RESULT] browser({action}): denied by user"
    return f"[TOOL RESULT] browser failed: {result.get('error', result.get('reason', 'unknown'))}"


def _handle_web_search(attrs: Dict, shared_memory: Dict) -> str:
    try:
        from search_engine import search, format_results_for_llm

        # 1. Protect attribute parsing safely
        query = attrs.get('query', '').strip()
        if not query:
            return "[TOOL RESULT] web_search error: Empty search query provided."

        raw_n = attrs.get('n', '5')
        try:
            # Safely scrub and cast digit characters
            n = int(''.join(filter(str.isdigit, str(raw_n))) or 5)
        except ValueError:
            n = 5

        # 2. Extract context carefully or instantiate isolated worker memory to prevent thread contention with the active loop dispatcher
        search_memory = shared_memory.copy() if shared_memory else {}

        # 3. Fire the execution network payload safely
        payload = search(query, max_results=n, shared_memory=search_memory)

        if not payload:
            return f"[TOOL RESULT] web_search: No results found for '{query}'."

        return f"[TOOL RESULT] web_search:\n{format_results_for_llm(payload)}"

    except Exception as e:
        # Prevent the whole loop from freezing on unhandled subprocess issues
        return f"[TOOL RESULT] web_search error: {str(e)}"


def _handle_execute_script(attrs: Dict, controller) -> str:
    script = attrs.get('script', '')
    if not script:
        return "[TOOL RESULT] Error: script required for execute_script"
    result = controller.execute_script(script)
    if result['status'] == 'success':
        out = result.get('stdout', '')
        err = result.get('stderr', '')
        response = f"[TOOL RESULT] execute_script:\nstdout: {out[:2000]}"
        if err:
            response += f"\nstderr: {err[:500]}"
        return response
    elif result['status'] == 'denied':
        return "[TOOL RESULT] execute_script: denied by user"
    return f"[TOOL RESULT] execute_script failed: {result.get('error', result.get('reason', 'unknown'))}"


def _handle_kb_write(attrs: Dict, shared_memory: Dict) -> str:
    """Write a discovery to the knowledge base."""
    try:
        import knowledge_base as kb
        domain = attrs.get('domain', 'general')
        discovery_type = attrs.get('type', 'llm_discovery')
        summary = attrs.get('summary', '')
        confidence = float(attrs.get('confidence', '0.7'))
        node_tier = int(attrs.get('tier', str(
            shared_memory.get('session_context', {}).get('node_tier', 1)
        )))

        discovery_id = kb.log_discovery(
            domain=domain,
            discovery_type=discovery_type,
            content={
                'summary': summary,
                'confidence': confidence,
                'source': 'llm_tool_call'
            },
            specialist_id='llm_direct',
            node_tier=node_tier
        )
        return f"[TOOL RESULT] kb_write: logged discovery {discovery_id} for domain '{domain}'"
    except Exception as e:
        return f"[TOOL RESULT] kb_write failed: {e}"


def _handle_kb_read(attrs: Dict) -> str:
    """Read knowledge from the KB for a domain."""
    try:
        import knowledge_base as kb
        domain = attrs.get('domain', 'general')
        discoveries = kb.query_domain_knowledge(domain)
        if not discoveries:
            return f"[TOOL RESULT] kb_read({domain}): no knowledge found"
        summary_lines = []
        for d in discoveries[-5:]:  # last 5
            content = d.get('content', {})
            tier = "S" if d.get('node_tier', 1) == 0 else "E"
            summary_lines.append(
                f"  [{tier}] {d['type']}: {content.get('summary', '')[:120]}"
            )
        return f"[TOOL RESULT] kb_read({domain}) — {len(discoveries)} discoveries:\n" + "\n".join(summary_lines)
    except Exception as e:
        return f"[TOOL RESULT] kb_read failed: {e}"


def _handle_list_axioms(attrs: Dict, shared_memory: Dict) -> str:
    """List active axioms via axiom_manager."""
    try:
        axiom_mgr = shared_memory.get('axiom_manager')
        if not axiom_mgr:
            return "[TOOL RESULT] list_axioms: axiom_manager not initialized"
        active = axiom_mgr.list_active_axioms()
        if not active:
            return "[TOOL RESULT] list_axioms: no active axioms"
        lines = [f"  {a['domain']}: {a['fact']}" for a in active]
        return "[TOOL RESULT] list_axioms:\n" + "\n".join(lines)
    except Exception as e:
        return f"[TOOL RESULT] list_axioms failed: {e}"


# =============================================================================
# Main Dispatcher
# =============================================================================

class ToolDispatcher:
    """
    Sits between LLM output and user.
    Finds tool tags, executes them, injects results.
    """

    def __init__(self, shared_memory: Dict):
        self.shared_memory = shared_memory
        self.dispatch_log: List[Dict] = []

        # Lazy-load os_controller (only if available)
        self._controller = None

    def _get_controller(self):
        """Lazy-load OS controller from shared memory."""
        if self._controller is not None:
            return self._controller

        controller = self.shared_memory.get('os_controller')
        if controller:
            self._controller = controller
            return controller

        # Try to initialize if os_control is available
        try:
            from os_control import create_os_controller
            controller = create_os_controller(self.shared_memory)
            self.shared_memory['os_controller'] = controller
            self._controller = controller
            print("[TOOL_DISPATCHER] OS controller initialized on demand")
            return controller
        except ImportError:
            return None

    def process(self, llm_output: str) -> Dict[str, Any]:
        """
        Main entry point.
        Parses tool tags from LLM output, executes them, returns result.

        Returns:
            {
                'output': str,          # Clean text for user
                'tools_called': list,   # What was executed
                'tool_results': list,   # Raw results
                'has_tool_calls': bool
            }
        """
        tags = parse_tool_tags(llm_output)

        if not tags:
            return {
                'output': llm_output,
                'tools_called': [],
                'tool_results': [],
                'has_tool_calls': False
            }

        output = llm_output
        tools_called = []
        tool_results = []

        for tool_name, attrs, full_match in tags:
            result_text = self._dispatch(tool_name, attrs)
            tools_called.append(tool_name)
            tool_results.append({
                'tool': tool_name,
                'attrs': attrs,
                'result': result_text
            })

            # Replace the tag with the result inline
            output = output.replace(full_match, result_text)

            # Log to audit trail
            self._log_dispatch(tool_name, attrs, result_text)

        return {
            'output': output,
            'tools_called': tools_called,
            'tool_results': tool_results,
            'has_tool_calls': True
        }

    def _dispatch(self, tool_name: str, attrs: Dict) -> str:
        """Route tool call to correct handler."""
        controller = self._get_controller()

        # File operations — need controller
        if tool_name in ('read_file', 'write_file', 'delete_file',
                          'fetch_url', 'execute_script', 'browser'):
            if not controller:
                return f"[TOOL RESULT] {tool_name}: os_control not available. " \
                       f"Ensure os_control.py is in the project root."

            dispatch_map = {
                'read_file':      lambda: _handle_read_file(attrs, controller),
                'write_file':     lambda: _handle_write_file(attrs, controller),
                'delete_file':    lambda: _handle_delete_file(attrs, controller),
                'fetch_url':      lambda: _handle_fetch_url(attrs, controller),
                'browser':        lambda: _handle_browser(attrs, controller),
                'execute_script': lambda: _handle_execute_script(attrs, controller),
            }
            handler = dispatch_map.get(tool_name)
            if handler:
                try:
                    return handler()
                except Exception as e:
                    return f"[TOOL RESULT] {tool_name} error: {e}"

        # KB cleanup operations
        if tool_name in ('kb_sweep', 'kb_purge', 'kb_validate', 'kb_list_bad'):
            return self._dispatch_kb_cleanup(tool_name, attrs)

        # KB operations — no controller needed
        if tool_name == 'kb_write':
            return _handle_kb_write(attrs, self.shared_memory)
        if tool_name == 'kb_read':
            return _handle_kb_read(attrs)
        if tool_name == 'list_axioms':
            return _handle_list_axioms(attrs, self.shared_memory)

        # MCP filesystem and windows-mcp tools
        if tool_name in ('mcp_read', 'mcp_list', 'mcp_write',
                          'mcp_search', 'mcp_powershell', 'mcp_scrape',
                          'mcp_screenshot'):
            return self._dispatch_mcp(tool_name, attrs)

        # Web search
        if tool_name == 'web_search':
            return _handle_web_search(attrs, self.shared_memory)
        return f"[TOOL RESULT] Unknown tool: {tool_name}"

    def _dispatch_kb_cleanup(self, tool_name: str, attrs: Dict) -> str:
        """Route kb_sweep/purge/validate tags to kb_cleanup module."""
        try:
            import kb_cleanup, io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                if tool_name == 'kb_sweep':
                    kb_cleanup.cmd_sweep(fix=attrs.get('fix','').lower() == 'true')
                elif tool_name == 'kb_purge':
                    target = attrs.get('id') or attrs.get('pattern', '')
                    by_pat = 'pattern' in attrs
                    if not target:
                        return '[TOOL RESULT] kb_purge: requires id="..." or pattern="..."'
                    import unittest.mock
                    with unittest.mock.patch('builtins.input', return_value='yes'):
                        kb_cleanup.cmd_purge(target, by_pattern=by_pat)
                elif tool_name == 'kb_validate':
                    kb_cleanup.cmd_validate()
                elif tool_name == 'kb_list_bad':
                    kb_cleanup.cmd_list_bad()
            return f'[TOOL RESULT] {tool_name}:\n{buf.getvalue()}'
        except Exception as e:
            return f'[TOOL RESULT] {tool_name} error: {e}'

    def _dispatch_mcp(self, tool_name: str, attrs: Dict) -> str:
        """Route [TOOL:mcp_*] tags to caios_mcp_client."""
        if not MCP_AVAILABLE:
            return '[TOOL RESULT] MCP unavailable — caios_mcp_client.py not found'

        # Map tag names to (mcp_tool_name, required_arg)
        route_map = {
            'mcp_read':       ('read_file',      'path'),
            'mcp_list':       ('list_directory', 'path'),
            'mcp_write':      ('write_file',     'path'),
            'mcp_search':     ('search_files',   'path'),
            'mcp_powershell': ('powershell',     'command'),
            'mcp_scrape':     ('scrape',         'url'),
            'mcp_screenshot': ('screenshot',     None),
        }

        if tool_name not in route_map:
            return f'[TOOL RESULT] Unknown MCP tool: {tool_name}'

        mcp_name, required_arg = route_map[tool_name]

        # Build arguments dict from tag attrs
        mcp_args = dict(attrs)  # pass all attrs through
        if required_arg and required_arg not in mcp_args:
            return f'[TOOL RESULT] {tool_name}: missing required attr "{required_arg}"'

        # mcp_write needs content attr too
        if tool_name == 'mcp_write' and 'content' not in mcp_args:
            return '[TOOL RESULT] mcp_write: missing required attr "content"'

        # mcp_search needs pattern attr
        if tool_name == 'mcp_search' and 'pattern' not in mcp_args:
            mcp_args['pattern'] = '*'  # default to all files

        result = _mcp_call(mcp_name, mcp_args)

        if result['ok']:
            content = result['content']
            if len(content) > 4000:
                content = content[:4000] + f'\n... [truncated, {len(result["content"])} chars total]'
            return f'[TOOL RESULT] {tool_name}({attrs.get(required_arg or "", "")}):\n{content}'
        else:
            return f'[TOOL RESULT] {tool_name} failed: {result["content"]}'

    def _log_dispatch(self, tool_name: str, attrs: Dict, result: str):
        """Log tool call to shared memory audit trail."""
        entry = {
            'ts': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z',
            'event': 'TOOL_DISPATCH',
            'tool': tool_name,
            'attrs': attrs,
            'result_preview': result[:100]
        }
        self.dispatch_log.append(entry)
        self.shared_memory.setdefault('audit_trail', []).append(entry)


# =============================================================================
# System Prompt Injection
# =============================================================================

TOOL_SYSTEM_ADDENDUM = r"""
[TOOL ACCESS]
You have access to system tools via structured tags. Use these when the user asks you to read/write files, browse the web, access the knowledge base, or run scripts.

TAG FORMAT: [TOOL:tool_name key="value"]

AVAILABLE TOOLS:
  [TOOL:read_file path="path/to/file.txt"]
  [TOOL:write_file path="path/to/file.txt" content="text to write"]
  [TOOL:write_file path="path.txt" content="text" overwrite="true"]
  [TOOL:delete_file path="path/to/file.txt"]
  [TOOL:fetch_url url="https://example.com" mode="content"]
  [TOOL:fetch_url url="https://example.com" mode="links"]
  [TOOL:browser url="https://example.com" action="scrape"]
  [TOOL:browser url="https://example.com" action="click" selector="button#submit"]
  [TOOL:web_search query="your search terms" n="5"]
  [TOOL:execute_script script="ls -la /home"]
  [TOOL:kb_write domain="domain_name" type="discovery" summary="what you found" confidence="0.85"]
  [TOOL:kb_read domain="domain_name"]
  [TOOL:list_axioms]

MCP TOOLS (filesystem server + windows-mcp):
  [TOOL:mcp_list path="C:/CAIOS"]
  [TOOL:mcp_read path="C:/CAIOS/orchestrator.py"]
  [TOOL:mcp_write path="C:/CAIOS/notes.txt" content="text here"]
  [TOOL:mcp_search path="C:/CAIOS" pattern="*.py"]
  [TOOL:mcp_powershell command="Get-Date"]
  [TOOL:mcp_scrape url="https://example.com"]
  [TOOL:mcp_screenshot]

RULES:
- Emit the tag inline in your response where the result should appear
- Only emit a tool tag if the user actually requested that action
- After the tool result appears, continue your response naturally
- For C:\CAIOS filesystem access: prefer mcp_read / mcp_list over read_file
- For web research: use fetch_url for simple reads, browser for interactive pages
- For KB writes: use kb_write when you discover something worth persisting
- Delete requires user confirmation — the system handles that automatically
"""


def get_tool_addendum() -> str:
    """Returns the system prompt addendum that teaches the LLM to use tools."""
    return TOOL_SYSTEM_ADDENDUM


# =============================================================================
# Factory
# =============================================================================

def create_tool_dispatcher(shared_memory: Dict) -> 'ToolDispatcher':
    """Factory function matching CAIOS module pattern."""
    return ToolDispatcher(shared_memory)


# =============================================================================
# Test Suite
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("TOOL DISPATCHER - Test Suite")
    print("=" * 70)

    # Mock shared memory
    mock_memory = {
        'session_context': {'node_tier': 1},
        'audit_trail': [],
        'axiom_manager': None
    }

    dispatcher = create_tool_dispatcher(mock_memory)

    # Test 1: No tool tags
    print("\n[TEST 1] No tool tags (passthrough)")
    result = dispatcher.process("Hello, how can I help you today?")
    print(f"  has_tool_calls: {result['has_tool_calls']}")
    print(f"  output: {result['output']}")

    # Test 2: Tag parsing
    print("\n[TEST 2] Tag parsing")
    tags = parse_tool_tags(
        'Sure! [TOOL:read_file path="readme.txt"] Here is the result.'
    )
    print(f"  Found {len(tags)} tag(s): {[(t[0], t[1]) for t in tags]}")

    # Test 3: Multiple tags
    print("\n[TEST 3] Multiple tags")
    tags2 = parse_tool_tags(
        '[TOOL:kb_read domain="quantum_semantics"] then [TOOL:list_axioms]'
    )
    print(f"  Found {len(tags2)} tag(s)")

    # Test 4: KB read (no controller needed)
    print("\n[TEST 4] KB read (standalone)")
    result4 = dispatcher.process(
        'Let me check the KB: [TOOL:kb_read domain="quantum_semantics"]'
    )
    print(f"  tools_called: {result4['tools_called']}")
    print(f"  output preview: {result4['output'][:200]}")

    # Test 5: OS controller not available
    print("\n[TEST 5] File read without controller")
    result5 = dispatcher.process(
        'Reading file: [TOOL:read_file path="readme.txt"]'
    )
    print(f"  output: {result5['output'][:200]}")

    print("\n" + "=" * 70)
    print("One is glad to be of service.")
    print("=" * 70)
