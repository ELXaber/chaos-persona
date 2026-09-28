# pending_approvals.py
import json, uuid, time
from pathlib import Path
from typing import Dict, Optional

PENDING_FILE = Path("knowledge_base/pending_approvals.json")
PENDING_FILE.parent.mkdir(exist_ok=True)

def _load() -> Dict[str, dict]:
    if not PENDING_FILE.exists():
        return {}
    try:
        with open(PENDING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def _save(data: Dict[str, dict]) -> None:
    with open(PENDING_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def create_pending(action_type: str, target: str, requester: str,
                   resume_args: dict, required_tier: Optional[str] = None) -> str:
    """required_tier=None → only the requester can resolve it (same-user popup).
    required_tier='manager' → only a manager-tier AD lookup can (cross-user)."""
    approval_id = uuid.uuid4().hex[:12]
    data = _load()
    data[approval_id] = {
        'action_type': action_type, 'target': target, 'requester': requester,
        'resume_args': resume_args, 'required_tier': required_tier,
        'status': 'pending', 'created_at': time.time(),
    }
    _save(data)
    return approval_id

def resolve(approval_id: str, approver: str, approved: bool) -> Optional[dict]:
    data = _load()
    record = data.get(approval_id)
    if not record or record['status'] != 'pending':
        return None
    record['status'] = 'approved' if approved else 'denied'
    record['approver'] = approver
    _save(data)
    return record

def list_pending(for_tier: Optional[str] = None, for_requester: Optional[str] = None) -> list:
    return [{**v, 'approval_id': k} for k, v in _load().items()
            if v['status'] == 'pending'
            and (for_tier is None or v['required_tier'] == for_tier)
            and (for_requester is None or v['requester'] == for_requester)]

# Resume dispatch — resolved args map back to a fresh call, never a stored closure
# (closures aren't JSON-serializable, and this has to survive a restart)
def get_resumable(action_type: str):
    return {
        'file_write': lambda c, a: c._do_write_file(**a),
        'file_delete': lambda c, a: c._do_delete_file(**a),
        'git_commit': lambda c, a: c._do_git_commit(**a),
        # ... one entry per gated method
    }[action_type]