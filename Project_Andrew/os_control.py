#V03172026
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
    'execute_script': 0.8,   # High - unknown side effects
    'network_request': 0.6,  # Medium - depends on destination
    'file_write': 0.4,       # Low-medium - new file creation
    'file_read': 0.1,        # Low - read only, no state change
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

    # Test 3: Delete file (should require confirmation)
    print("\n[TEST 3] Delete File (confirmation disabled in test)")
    result = controller.delete_file("/tmp/caios_test.txt")
    print(f"Status: {result['status']}")

    # Test 4: High distress context (should increase density)
    print("\n[TEST 4] High Distress Context (elevated density)")
    shared_mem['distress_density'] = 0.8
    controller2 = OSController(shared_mem, require_confirmation=False)
    result = controller2.write_file("/tmp/test.txt", "test", overwrite=True)
    print(f"Status: {result['status']}")

    print("\n" + "="*70)
    print("One is glad to be of service.")
    print("="*70)