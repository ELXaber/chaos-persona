#V06252026
# =============================================================================
# caios_mcp_client.py — MCP JSON-RPC client for CAIOS
#
# Talks to two MCP servers that should be running alongside caios_bridge.py:
#
#   Server A — @modelcontextprotocol/server-filesystem (Node.js, stdio→HTTP)
#     Start: npx @modelcontextprotocol/server-filesystem C:\CAIOS
#     Default port: 3000  (or whatever you set with --port)
#     Used for: read_file, list_directory, search_files on C:\CAIOS
#
#   Server B — windows-mcp (Python, SSE transport)
#     Start: uvx windows-mcp serve --transport sse --host localhost --port 8000
#     Used for: PowerShell, Screenshot, Click, Snapshot, Scrape, etc.
#
# MCP protocol used here:
#   - JSON-RPC 2.0 over HTTP POST to /mcp  (filesystem server)
#   - JSON-RPC 2.0 over HTTP POST to /messages (windows-mcp SSE)
#   Both return application/json for tool calls.
#
# Usage inside caios_bridge.py:
#   from caios_mcp_client import MCPClient, mcp_tool
#   result = mcp_tool('read_file', {'path': 'C:/CAIOS/orchestrator.py'})
# =============================================================================

import json
import time
import urllib.request
import urllib.error
from typing import Any, Dict, Optional, List

# =============================================================================
# Configuration — change ports here if you started the servers differently
# =============================================================================

FS_MCP_URL   = 'http://localhost:3000'   # @modelcontextprotocol/server-filesystem
WIN_MCP_URL  = 'http://localhost:8000'   # windows-mcp

# Timeout for MCP calls (seconds)
MCP_TIMEOUT  = 15

# Tools that live on the filesystem server
FS_TOOLS = {
    'read_file',
    'write_file',
    'list_directory',
    'search_files',
    'get_file_info',
    'create_directory',
    'move_file',
    'delete_file',
}

# Tools that live on windows-mcp
WIN_TOOLS = {
    'screenshot',
    'click',
    'snapshot',
    'state',
    'type',
    'key',
    'scroll',
    'powershell',
    'registry',
    'scrape',
    'app',
    'clipboard',
    'process',
}


# =============================================================================
# Low-level JSON-RPC caller
# =============================================================================

def _jsonrpc_call(base_url: str, method: str, params: Dict,
                  rpc_id: int = 1) -> Dict[str, Any]:
    """
    Send a JSON-RPC 2.0 request to an MCP server endpoint.
    Both servers accept POST with Content-Type: application/json.

    filesystem server: POST /mcp
    windows-mcp SSE:   POST /messages  (or /mcp — try both)
    """
    payload = {
        'jsonrpc': '2.0',
        'id': rpc_id,
        'method': method,
        'params': params,
    }
    body = json.dumps(payload).encode('utf-8')

    # Try the standard MCP endpoint first, fall back to /messages if URL already includes a path (like /sse), use it directly
    if base_url.endswith('/sse'):
        endpoints = ['']
    elif 'localhost:8000' in base_url:
        endpoints = ['/mcp', '/messages']
    else:
        endpoints = ['/mcp']

    last_error = None
    for endpoint in endpoints:
        url = base_url.rstrip('/') + endpoint
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/event-stream',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=MCP_TIMEOUT) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result
        except urllib.error.HTTPError as e:
            last_error = f'HTTP {e.code}: {e.reason}'
            if e.code != 404:
                break  # don't try next endpoint for non-404 errors
        except urllib.error.URLError as e:
            last_error = f'Connection error: {e.reason}'
            break
        except Exception as e:
            last_error = str(e)
            break

    return {'jsonrpc': '2.0', 'id': rpc_id,
            'error': {'code': -32000, 'message': last_error or 'Unknown error'}}

# =============================================================================
# MCP Client class
# =============================================================================

class MCPClient:
    """
    Wraps both MCP servers with a single call interface.
    Automatically routes to the right server based on tool name.
    """

    def __init__(self,
                 fs_url: str = FS_MCP_URL,
                 win_url: str = WIN_MCP_URL):
        self.fs_url  = fs_url
        self.win_url = win_url
        self._id = 0
        self._fs_available  = None
        self._win_available = None

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def _check_server(self, base_url: str) -> bool:
        """Ping the server with an initialize call."""
        result = _jsonrpc_call(base_url, 'initialize', {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {'name': 'caios-bridge', 'version': '1.0'},
        }, rpc_id=0)
        if 'error' not in result:
            return True
        # Fallback: check if the SSE endpoint is reachable
        try:
            import urllib.request
            urllib.request.urlopen(
                base_url.rstrip('/') + '/sse', timeout=3
            )
            return True
        except Exception:
            return False

    def fs_available(self) -> bool:
        if self._fs_available is None:
            try:
                self._fs_available = self._check_server(self.fs_url)
            except Exception:
                self._fs_available = False
        return self._fs_available

    def reset_availability_cache(self):
        self._fs_available = None
        self._win_available = None

    def win_available(self) -> bool:
        if self._win_available is None:
            try:
                import socket
                with socket.create_connection(('localhost', 8000), timeout=2):
                    self._win_available = True
            except OSError:
                self._win_available = False
        return self._win_available

    def status(self) -> Dict[str, bool]:
        """Return availability of both servers."""
        return {
            'filesystem_server': self.fs_available(),
            'windows_mcp': self.win_available(),
            'fs_url': self.fs_url,
            'win_url': self.win_url,
        }

    def list_tools(self, server: str = 'fs') -> List[Dict]:
        """
        Ask a server what tools it exposes (MCP tools/list method).
        server: 'fs' or 'win'
        """
        base = self.fs_url if server == 'fs' else self.win_url
        result = _jsonrpc_call(base, 'tools/list', {}, self._next_id())
        if 'error' in result:
            return []
        return result.get('result', {}).get('tools', [])

    def call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool by name. Routes to the correct server automatically.
        Returns a normalised result dict:
          { 'ok': bool, 'content': str, 'raw': dict }
        """
        tool_lower = tool_name.lower()

        # Route to correct server
        if tool_lower in WIN_TOOLS:
            if not self.win_available():
                return _error_result(
                    f"windows-mcp not available at {self.win_url}. "
                    f"Start it with: uvx windows-mcp serve --transport streamable-http --host localhost --port 8000"
                )
            base = self.win_url
        else:
            # FS_TOOLS and unknown tools — not handled by MCP
            return _error_result(
                f"Tool '{tool_name}' is not a windows-mcp tool. "
                f"File operations are handled by os_control.py via [TOOL:read_file] etc."
            )

        rpc_result = _jsonrpc_call(
            base,
            'tools/call',
            {'name': tool_name, 'arguments': arguments},
            self._next_id(),
        )
        return _parse_mcp_result(rpc_result)

    # ── Convenience wrappers for common filesystem operations ──

    def read_file(self, path: str) -> Dict:
        """Read a file from the filesystem MCP server."""
        return self.call('read_file', {'path': path})

    def list_directory(self, path: str) -> Dict:
        """List contents of a directory."""
        return self.call('list_directory', {'path': path})

    def search_files(self, path: str, pattern: str) -> Dict:
        """Search for files matching a glob pattern under path."""
        return self.call('search_files', {'path': path, 'pattern': pattern})

    def write_file(self, path: str, content: str) -> Dict:
        """Write content to a file via the filesystem MCP server."""
        return self.call('write_file', {'path': path, 'content': content})

    # ── Convenience wrappers for windows-mcp ──

    def powershell(self, command: str) -> Dict:
        """Run a PowerShell command via windows-mcp."""
        return self.call('powershell', {'command': command})

    def screenshot(self) -> Dict:
        """Take a screenshot via windows-mcp."""
        return self.call('screenshot', {})

    def scrape(self, url: str) -> Dict:
        """Scrape a URL via windows-mcp's Scrape tool."""
        return self.call('scrape', {'url': url})


# =============================================================================
# Helpers
# =============================================================================

def _error_result(message: str) -> Dict:
    return {'ok': False, 'content': f'[MCP ERROR] {message}', 'raw': {}}


def _parse_mcp_result(rpc_result: Dict) -> Dict:
    """
    Normalise an MCP tools/call response into { ok, content, raw }.
    MCP returns content as a list of content blocks:
      [{ 'type': 'text', 'text': '...' }, ...]
    """
    if 'error' in rpc_result:
        err = rpc_result['error']
        msg = err.get('message', str(err)) if isinstance(err, dict) else str(err)
        return {'ok': False, 'content': f'[MCP ERROR] {msg}', 'raw': rpc_result}

    result = rpc_result.get('result', {})

    # MCP content blocks
    content_blocks = result.get('content', [])
    if isinstance(content_blocks, list):
        text_parts = []
        for block in content_blocks:
            if isinstance(block, dict):
                if block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
                elif block.get('type') == 'image':
                    text_parts.append('[IMAGE DATA — base64 omitted]')
            elif isinstance(block, str):
                text_parts.append(block)
        content = '\n'.join(text_parts)
    elif isinstance(content_blocks, str):
        content = content_blocks
    else:
        content = json.dumps(result)

    is_error = result.get('isError', False)
    return {'ok': not is_error, 'content': content, 'raw': rpc_result}


# =============================================================================
# Module-level singleton + convenience function for caios_bridge.py
# =============================================================================

_client: Optional[MCPClient] = None


def get_client() -> MCPClient:
    """Return (or create) the module-level singleton client."""
    global _client
    if _client is None:
        _client = MCPClient()
    return _client


def mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    One-liner for caios_bridge.py and tool_dispatcher.py:
        result = mcp_tool('read_file', {'path': 'C:/CAIOS/readme.txt'})
        print(result['content'])
    """
    return get_client().call(tool_name, arguments)


def mcp_status() -> Dict[str, bool]:
    """Quick status check for the /api/boot endpoint."""
    return get_client().status()


# =============================================================================
# CLI test — python caios_mcp_client.py
# =============================================================================

if __name__ == '__main__':
    print('=' * 60)
    print('  CAIOS MCP Client — connection test')
    print('=' * 60)

    client = MCPClient()
    status = client.status()

    import socket
    try:
        with socket.create_connection(('localhost', 8000), timeout=2):
            win_up = True
    except OSError:
        win_up = False

    print(f"\nFilesystem MCP ({status['fs_url']}): "
          f"{'✓ connected' if status['filesystem_server'] else '✗ not running'}")
    print(f"Windows MCP   (http://localhost:8000/sse): "
          f"{'✓ connected' if win_up else '✗ not running'}")

    print(f"\nFilesystem MCP ({status['fs_url']}): "
          f"{'✓ connected' if status['filesystem_server'] else '✗ not running'}")
    print(f"Windows MCP   ({status['win_url']}): "
          f"{'✓ connected' if status['windows_mcp'] else '✗ not running'}")

    if status['filesystem_server']:
        print('\n--- Listing C:\\CAIOS ---')
        result = client.list_directory('C:/CAIOS')
        if result['ok']:
            # Show first 20 lines
            lines = result['content'].split('\n')
            for line in lines[:20]:
                print(' ', line)
            if len(lines) > 20:
                print(f'  ... and {len(lines)-20} more entries')
        else:
            print(result['content'])

        print('\n--- Reading C:\\CAIOS\\readme.txt ---')
        result = client.read_file('C:/CAIOS/readme.txt')
        if result['ok']:
            print(result['content'][:500])
        else:
            print(result['content'])

    if status['windows_mcp']:
        print('\n--- PowerShell: Get-Date ---')
        result = client.powershell('Get-Date')
        print(result['content'])

    print('\n' + '=' * 60)
    print('  To start missing servers:')
    if not status['filesystem_server']:
        print('  npx @modelcontextprotocol/server-filesystem C:\\CAIOS')
    if not status['windows_mcp']:
        print('  uvx windows-mcp serve --transport sse --host localhost --port 8000')
    print('=' * 60)