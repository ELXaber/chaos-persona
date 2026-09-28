The auth_approval.py and pending_approvals.py is a prototype for active directory intergration for dual authorization on ireverseable actions in the os_control.
The basic concept is that employees can create an authorization request, but a manager has to sign off on it.
A manager or above can both create their own request and authorize it.
Those employment levels are stored in Active Directory.

-------------------------------
auth_approval.py changes
-------------------------------

# git_commit's new branch — only touches the employee case

-------------------------------

python
# os_control.py, inside git_commit, before the existing gate/_confirm logic
import auth_approval

perm = auth_approval.check_action_permission(
    self.shared_memory.get('active_user'), 'git_commit', self.ldap_config
)

if not perm['satisfied']:
    if perm['needs'] == 'unregistered_denied':
        self._log_action('git_commit', repo_path, 'blocked_unregistered')
        return {'status': 'blocked', 'reason': 'User not recognized in AD'}

    import pending_approvals
    approval_id = pending_approvals.create_pending_approval(
        action_type='git_commit',
        target=repo_path,
        payload={'repo_path': repo_path, 'message': message},
        requester=perm['requester']
    )
    self._log_action('git_commit', repo_path, f'pending_manager_approval:{approval_id}')
    return {'status': 'pending', 'approval_id': approval_id,
            'reason': 'Employee-submitted commit awaiting manager approval'}

# manager-tier requester falls through to the exact existing gate/_confirm flow, unchanged
gate = self._gate_action('git_commit', repo_path, context=message[:80])
...

-------------------------------

Notice the manager branch is literally the code you already have — nothing about git_commit's normal path changes at all. Only employees ever hit pending_approvals.

The one piece this still needs: a way for a manager to find pending requests

Approval-by-ID-only is a real usability gap — a manager can't act on a request they don't know exists. This needs a small discovery surface, not just the approve action itself:

-------------------------------

python
# pending_approvals.py
def list_pending_for_manager() -> list:
    """Everything with status == 'pending', for a manager to review."""

def approve_pending(approval_id: str, approver_id: str, ad_tier: str) -> dict:
    if ad_tier != auth_approval.AD_TIER_MANAGER:
        return {'status': 'denied', 'reason': 'Approver must be manager tier'}
    record = _load(approval_id)
    if approver_id == record['requester']:
        # shouldn't be reachable given the logic above, but a real backstop —
        # an employee can never end up in their own approval queue, and this
        # guards against a future bug or a misused manual call doing exactly that
        return {'status': 'denied', 'reason': 'Cannot self-approve'}
    record['status'] = 'approved'
    _save(record)
    return {'status': 'approved', 'payload': record['payload']}

-------------------------------

Then two small orchestrator.py commands: /pending (list, manager-tier only) and /approve <id> (calls approve_pending, and on success, actually fires os_controller.git_commit(**payload) directly — this second call skips the AD-gate check entirely since it's not re-entering through the employee path, it's executing an already-approved action).

-------------------------------
pending_approval.py changes
-------------------------------

The mechanical split in os_control.py — each gated method separates into "gate + defer-or-proceed" and "the actual mutation," so the mutation is independently callable from the resume path. Full pattern on write_file, the other six (delete_file, move_file, git_commit, execute_script, browser_interact, windows_mcp) get the identical treatment:

-------------------------------

python
def write_file(self, path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
    action = 'file_overwrite' if overwrite and pathlib.Path(path).exists() else 'file_write'
    gate = self._gate_action(action, path)
    if gate['decision'] == 'block':
        self._log_action(action, path, 'blocked')
        return {'status': 'blocked', 'reason': gate['reason']}

    if gate['decision'] == 'confirm_required' and not _in_autonomous_zone(path):
        if self.pending_approval_mode:  # set by caios_bridge.py only, off for CLI
            approval_id = pending_approvals.create_pending(
                action, path, self.shared_memory.get('active_user', 'unknown'),
                resume_args={'path': path, 'content': content, 'overwrite': overwrite},
                required_tier=self._required_tier_for(action)
            )
            return {'status': 'pending', 'approval_id': approval_id}
        if not self._confirm(action, path):  # unchanged CLI/terminal path
            self._log_action(action, path, 'denied_by_user')
            return {'status': 'denied', 'reason': 'User denied confirmation'}

    return self._do_write_file(path, content)

def _do_write_file(self, path: str, content: str) -> Dict[str, Any]:
    """The actual mutation, gate-free — called synchronously above, or by
    the resume dispatch table once an approval resolves."""
    try:
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(path).write_text(content, encoding='utf-8')
        self._log_action('file_write', path, 'allowed')
        return {'status': 'success', 'path': path}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

-------------------------------

Two new Flask routes — /api/confirm (resolves a pending record; checks requester-match for self-confirms, AD tier for manager-gated ones, then invokes the resume dispatch) and /api/pending (lets a manager's UI list what's waiting on them, lets anyone's UI check on their own). Both are small — the interesting logic already lives in pending_approvals.py and auth_approval.py.

Frontend: when a chat response comes back with status: 'pending', caios_chat_ui.html renders an in-app modal (Approve/Deny) instead of the normal bubble — for the same-user case this still feels synchronous, since it appears in the same session immediately, even though it's now two HTTP calls instead of one blocking one. For the manager-approval case, a lightweight setInterval poll of /api/pending is the honest, minimal-complexity option — matches how this whole project has stayed away from anything heavier than it needs (no new dependency, no persistent connection). A websocket/SSE push would make it feel more "live," but that's a real complexity jump I wouldn't reach for unless polling turns out to feel too laggy in practice.