#V03232026
# =============================================================================
# Chaos AI-OS — OS Control Layer
# CPOL-gated system operations with Asimov compliance
# Every irreversible action requires human confirmation
# All actions logged to KB hash chain
# =============================================================================

import os
import subprocess
import pathlib
from typing import Dict, Any, Optional
from paradox_oscillator import CPOL_Kernel, run_cpol_decision

# Irreversibility classifier
IRREVERSIBLE_ACTIONS = {
    'file_delete': 1.0,      # Maximum contradiction density
    'file_overwrite': 0.9,   # High - data loss possible
    'send_message': 0.85,    # High - external communication
    'form_submit': 0.85,       # High - irreversible external action
    'execute_script': 0.8,   # High - unknown side effects
    'browser_interact': 0.7,   # Medium-high - external state change
    'network_request': 0.6,  # Medium - depends on destination
    'file_write': 0.4,       # Low-medium - new file creation
    'file_read': 0.1,        # Low - read only, no state change
    'semantic_fetch': 0.2,      # Read-only web, low risk
}

class OSController:
    """
    CPOL-gated OS operations.
    Irreversible actions require human confirmation.
    All actions logged to KB hash chain.
    Asimov Law 1 (0.9 immutable) prevents harmful state transitions.
    """

    def __init__(self, shared_memory: Dict, require_confirmation: bool = True):
        self.shared_memory = shared_memory
        self.require_confirmation = require_confirmation
        self.cpol = CPOL_Kernel()
        self.action_log = []

    def _gate_action(self, action_type: str, target: str, 
                     context: str = "") -> Dict[str, Any]:
        """
        Run action through CPOL before execution.
        Returns decision dict with allow/confirm/block.
        """
        density = IRREVERSIBLE_ACTIONS.get(action_type, 0.5)

        # Check distress/safety context from shared memory
        distress = self.shared_memory.get('distress_density', 0.0)
        if distress > 0.5:
            density = min(1.0, density + 0.3)

        result = run_cpol_decision(
            contradiction_density=density,
            query_text=f"{action_type} on {target}: {context}"
        )

        # Asimov Law 1 hard gate
        if density >= 0.8:
            return {
                'decision': 'confirm_required',
                'reason': 'Irreversible action requires human approval',
                'cpol_status': result['status'],
                'action': action_type,
                'target': target
            }

        if result['status'] == 'UNDECIDABLE':
            return {
                'decision': 'block',
                'reason': f"CPOL UNDECIDABLE: {result.get('logic', 'unknown')}",
                'cpol_status': 'UNDECIDABLE',
                'action': action_type,
                'target': target
            }

        return {
            'decision': 'allow',
            'cpol_status': result['status'],
            'action': action_type,
            'target': target
        }

    def _confirm(self, action_type: str, target: str) -> bool:
        """
        Human confirmation prompt for irreversible actions.
        Simple CLI for now - Open WebUI button later.
        """
        print(f"\n[OS CONTROL] ⚠️  CONFIRMATION REQUIRED")
        print(f"[OS CONTROL] Action: {action_type}")
        print(f"[OS CONTROL] Target: {target}")
        print(f"[OS CONTROL] This action may be irreversible.")
        response = input("[OS CONTROL] Approve? (yes/no): ").strip().lower()
        return response in ('yes', 'y')

    def _log_action(self, action_type: str, target: str, 
                    decision: str, result: Any = None):
        """Log all actions to KB hash chain."""
        entry = {
            'action': action_type,
            'target': str(target),
            'decision': decision,
            'result': str(result) if result else None,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }
        self.action_log.append(entry)

        # Log to KB if available
        try:
            import knowledge_base as kb
            kb.log_discovery(
                domain="os_control",
                discovery_type="system_action",
                content=entry,
                node_tier=self.shared_memory.get(
                    'session_context', {}
                ).get('node_tier', 1)
            )
        except Exception:
            pass  # KB unavailable, local log only

        print(f"[OS CONTROL] Logged: {action_type} on {target} → {decision}")

    # =========================================================================
    # Public API
    # =========================================================================

    def read_file(self, path: str) -> Dict[str, Any]:
        """Read file - low risk, CPOL gate still applied."""
        gate = self._gate_action('file_read', path)

        if gate['decision'] == 'block':
            self._log_action('file_read', path, 'blocked')
            return {'status': 'blocked', 'reason': gate['reason']}

        try:
            content = pathlib.Path(path).read_text(encoding='utf-8')
            self._log_action('file_read', path, 'allowed')
            return {'status': 'success', 'content': content}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def fetch_url(self, url: str, 
                  extract_mode: str = 'content') -> Dict[str, Any]:
        """
        Agent-optimized semantic web fetcher.
        Strips visual noise, tooltips, scripts, ads.
        Returns structured content safe for agent consumption.
        No screenshots. No coordinates. No focus hijacking.

        extract_mode: 'content' | 'links' | 'forms' | 'full'
        """
        gate = self._gate_action('semantic_fetch', url)

        if gate['decision'] == 'block':
            self._log_action('semantic_fetch', url, 'blocked')
            return {'status': 'blocked', 'reason': gate['reason']}

        try:
            import urllib.request
            import html.parser

            # Security: validate URL before fetch
            if not url.startswith(('http://', 'https://')):
                return {'status': 'blocked', 
                        'reason': 'Invalid URL scheme'}

            # Simple embedded code attack mitigation
            BLOCKED_PATTERNS = [
                'javascript:', 'data:', 'vbscript:',
                'onload=', 'onerror=', 'onclick='
            ]

            headers = {
                'User-Agent': 'CAIOS-Agent/1.0 (semantic fetch)',
                'Accept': 'text/html,application/xhtml+xml',
            }

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                raw_html = response.read().decode('utf-8', errors='ignore')

            # Check for embedded attack patterns
            raw_lower = raw_html.lower()
            detected_threats = [p for p in BLOCKED_PATTERNS 
                               if p in raw_lower]
            if len(detected_threats) > 2:
                self._log_action('semantic_fetch', url, 
                               'blocked_malicious_content')
                return {
                    'status': 'blocked',
                    'reason': f'Potential malicious content: '
                             f'{detected_threats}'
                }

            # Strip to semantic content
            result = self._extract_semantic(raw_html, extract_mode)
            self._log_action('semantic_fetch', url, 'allowed')

            return {
                'status': 'success',
                'url': url,
                'extract_mode': extract_mode,
                'content': result
            }

        except Exception as e:
            self._log_action('semantic_fetch', url, f'error: {e}')
            return {'status': 'error', 'error': str(e)}

    def write_file(self, path: str, content: str, 
                   overwrite: bool = False) -> Dict[str, Any]:
        """Write file - medium risk if overwrite."""
        action = 'file_overwrite' if overwrite and pathlib.Path(path).exists() \
                 else 'file_write'
        gate = self._gate_action(action, path)

        if gate['decision'] == 'block':
            self._log_action(action, path, 'blocked')
            return {'status': 'blocked', 'reason': gate['reason']}

        if gate['decision'] == 'confirm_required':
            if not self._confirm(action, path):
                self._log_action(action, path, 'denied_by_user')
                return {'status': 'denied', 'reason': 'User denied confirmation'}

        try:
            pathlib.Path(path).write_text(content, encoding='utf-8')
            self._log_action(action, path, 'allowed')
            return {'status': 'success', 'path': path}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete file - maximum risk, always requires confirmation."""
        gate = self._gate_action('file_delete', path)

        # Always confirm deletes regardless of CPOL result
        if self.require_confirmation:
            if not self._confirm('file_delete', path):
                self._log_action('file_delete', path, 'denied_by_user')
                return {'status': 'denied', 'reason': 'User denied confirmation'}

        try:
            pathlib.Path(path).unlink()
            self._log_action('file_delete', path, 'allowed')
            return {'status': 'success', 'deleted': path}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def execute_script(self, script: str, 
                       timeout: int = 30) -> Dict[str, Any]:
        """Execute script - high risk, always requires confirmation."""
        gate = self._gate_action('execute_script', script[:50])

        if gate['decision'] == 'block':
            self._log_action('execute_script', script[:50], 'blocked')
            return {'status': 'blocked', 'reason': gate['reason']}

        if self.require_confirmation:
            if not self._confirm('execute_script', script[:100]):
                self._log_action('execute_script', script[:50], 'denied_by_user')
                return {'status': 'denied', 'reason': 'User denied confirmation'}

        try:
            result = subprocess.run(
                script, shell=True, capture_output=True,
                text=True, timeout=timeout
            )
            self._log_action('execute_script', script[:50], 'executed')
            return {
                'status': 'success',
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'error': f'Exceeded {timeout}s'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def browser_interact(self, url: str,
                         action: str,
                         selector: str = None,
                         value: str = None,
                         wait_for: str = None,
                         timeout: int = 30) -> Dict[str, Any]:
        """
        Full headless browser control via Playwright.
        No screenshots. No coordinates. DOM selector based.
        CPOL-gated by action type.

        action: 'navigate' | 'click' | 'fill' | 'select' |
                'submit' | 'scrape' | 'screenshot'
        selector: CSS selector, input name, or button text
        value: text to fill (for 'fill' action)
        wait_for: CSS selector to wait for before acting
        timeout: max seconds for operation

        Requires: pip install playwright
                  playwright install chromium
        Falls back to urllib POST for simple forms if unavailable.
        """
        # Gate by action type
        action_type = 'form_submit' if action == 'submit' \
                      else 'browser_interact'
        gate = self._gate_action(action_type, url)

        if gate['decision'] == 'block':
            self._log_action(action_type, url, 'blocked')
            return {'status': 'blocked', 'reason': gate['reason']}

        if gate['decision'] == 'confirm_required':
            if not self._confirm(action_type, f"{action} on {url}"):
                self._log_action(action_type, url, 'denied_by_user')
                return {'status': 'denied', 
                        'reason': 'User denied confirmation'}

        # Build Playwright script
        wait_line = f"page.wait_for_selector('{wait_for}')" \
                    if wait_for else "page.wait_for_load_state('networkidle')"

        if action == 'navigate':
            action_line = ""
        elif action == 'click':
            action_line = f"page.click('{selector}')"
        elif action == 'fill':
            action_line = f"page.fill('{selector}', '{value}')"
        elif action == 'select':
            action_line = f"page.select_option('{selector}', '{value}')"
        elif action == 'submit':
            action_line = f"page.click('{selector or \"button[type=submit]\"}')"
        elif action == 'scrape':
            action_line = "result = page.inner_text('body')"
        elif action == 'screenshot':
            action_line = "page.screenshot(path='/tmp/caios_browser.png')"
        else:
            return {'status': 'error', 
                    'error': f'Unknown action: {action}'}

        script = f"""
import sys
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='CAIOS-Agent/1.0'
        )
        page = context.new_page()
        page.goto('{url}', timeout={timeout * 1000})
        {wait_line}
        result = ''
        {action_line}
        if not result:
            result = page.url
        browser.close()
        print(result)
except ImportError:
    print('PLAYWRIGHT_UNAVAILABLE')
except Exception as e:
    print(f'ERROR:{{e}}')
"""
        try:
            output = subprocess.run(
                ['python3', '-c', script],
                capture_output=True,
                text=True,
                timeout=timeout + 5
            )

            stdout = output.stdout.strip()

            # Playwright not installed — fallback to urllib
            if stdout == 'PLAYWRIGHT_UNAVAILABLE':
                print("[BROWSER] Playwright unavailable — "
                      "falling back to urllib")
                return self.fetch_url(url, extract_mode='full')

            if stdout.startswith('ERROR:'):
                self._log_action(action_type, url, 
                               f'error: {stdout}')
                return {'status': 'error', 
                        'error': stdout[6:]}

            self._log_action(action_type, url, 
                           f'executed: {action}')
            return {
                'status': 'success',
                'action': action,
                'url': url,
                'selector': selector,
                'result': stdout[:5000]
            }

        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 
                    'error': f'Exceeded {timeout}s'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def _extract_semantic(self, html: str, 
                           mode: str = 'content') -> Dict:
        """
        Strip visual noise. Return semantic structure only.
        No JS. No CSS. No tooltips. No ads. No tracking.
        Pure content for agent consumption.
        """
        import re

        # Remove script tags and contents
        html = re.sub(r'<script[^>]*>.*?</script>', 
                      '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove style tags
        html = re.sub(r'<style[^>]*>.*?</style>', 
                      '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove comments
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        # Remove event handlers
        html = re.sub(r'\s+on\w+="[^"]*"', '', html)
        html = re.sub(r"\s+on\w+='[^']*'", '', html)

        # Extract by mode
        if mode == 'content':
            # Get text content only
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text).strip()
            return {'text': text[:10000]}  # Cap at 10k chars

        elif mode == 'links':
            links = re.findall(
                r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
                html, re.IGNORECASE | re.DOTALL
            )
            return {'links': [
                {'url': l[0], 
                 'text': re.sub(r'<[^>]+>', '', l[1]).strip()}
                for l in links if l[0].startswith('http')
            ][:50]}  # Cap at 50 links

        elif mode == 'forms':
            forms = re.findall(
                r'<form[^>]*>(.*?)</form>',
                html, re.IGNORECASE | re.DOTALL
            )
            inputs = re.findall(
                r'<input[^>]+name=["\']([^"\']+)["\'][^>]*>',
                html, re.IGNORECASE
            )
            return {'forms': len(forms), 'inputs': inputs[:20]}

        elif mode == 'full':
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text).strip()
            links = re.findall(
                r'href=["\']([^"\']+)["\']', 
                html, re.IGNORECASE
            )
            return {
                'text': text[:10000],
                'links': [l for l in links 
                         if l.startswith('http')][:50]
            }

        return {'raw': html[:5000]}

# =============================================================================
# Factory function for orchestrator import
# =============================================================================

def create_os_controller(shared_memory: Dict, 
                         require_confirmation: bool = True) -> OSController:
    """Factory function - matches pattern of other CAIOS modules."""
    return OSController(shared_memory, require_confirmation)


# =============================================================================
# Test Suite
# =============================================================================

if __name__ == "__main__":
    print("="*70)
    print("OS CONTROL - Test Suite")
    print("="*70)

    shared_mem = {
        'distress_density': 0.0,
        'session_context': {'node_tier': 1}
    }

    controller = OSController(shared_mem, require_confirmation=False)

    # Test 1: Read file (should allow)
    print("\n[TEST 1] File Read (should allow)")
    result = controller.read_file("readme.txt")
    print(f"Status: {result['status']}")

    # Test 2: Write new file (should allow)
    print("\n[TEST 2] Write New File (should allow)")
    result = controller.write_file(
        "/tmp/caios_test.txt", 
        "CAIOS OS Control Test"
    )
    print(f"Status: {result['status']}")

    # Test 3: Semantic fetch (should allow)
    print("\n[TEST 3] Semantic Fetch (should allow)")
    result = controller.fetch_url(
        "https://cai-os.com", 
        extract_mode='content'
    )
    print(f"Status: {result['status']}")

    # Test 4: Delete file (should require confirmation)
    print("\n[TEST 3] Delete File (confirmation disabled in test)")
    result = controller.delete_file("/tmp/caios_test.txt")
    print(f"Status: {result['status']}")

    # Test 5: Browser interact - navigate (requires Playwright)
    print("\n[TEST 5] Browser Navigate (Playwright or urllib fallback)")
    result = controller.browser_interact(
        url="https://cai-os.com",
        action="navigate"
    )
    print(f"Status: {result['status']}")

    # Test 6: High distress context (should increase density)
    print("\n[TEST 4] High Distress Context (elevated density)")
    shared_mem['distress_density'] = 0.8
    controller2 = OSController(shared_mem, require_confirmation=False)
    result = controller2.write_file("/tmp/test.txt", "test", overwrite=True)
    print(f"Status: {result['status']}")

    print("\n" + "="*70)
    print("One is glad to be of service.")
    print("="*70)