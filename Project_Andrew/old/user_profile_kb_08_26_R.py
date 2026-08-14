#V08092026
# =============================================================================
# CAIOS — User Profile Knowledge Base
# Stores per-user personality state, emotional baselines, and preferences
# Minimal numeric storage — no conversation history bloat
# =============================================================================

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

USER_PROFILES_DIR = Path("knowledge_base/user_profiles")
USER_PROFILES_DIR.mkdir(parents=True, exist_ok=True)

def _profile_path(user_id: str) -> Path:
    safe_id = hashlib.sha256(user_id.encode()).hexdigest()[:16]
    return USER_PROFILES_DIR / f"{safe_id}.json"

def load_user_profile(user_id: str) -> Dict[str, Any]:
    """Load existing profile or return defaults, backfilling any schema
    fields added since this profile was last saved to disk."""
    path = _profile_path(user_id)
    defaults = _default_profile(user_id)
    if not path.exists():
        return defaults

    with open(path, 'r') as f:
        profile = json.load(f)

    def _merge_missing(target: dict, source: dict) -> None:
        for key, value in source.items():
            if key not in target:
                target[key] = value
            elif isinstance(value, dict) and isinstance(target.get(key), dict):
                _merge_missing(target[key], value)

    _merge_missing(profile, defaults)
    return profile

def save_user_profile(user_id: str, profile: Dict[str, Any]) -> None:
    """Save profile with timestamp."""
    profile['last_updated'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + "Z"
    with open(_profile_path(user_id), 'w') as f:
        json.dump(profile, f, indent=2)
    print(f"[USER_KB] Profile saved for {user_id}")

def update_complaint_state(
    user_id: str,
    complaint_count: int,
    persistent_complainer: bool = False
) -> None:
    """
    Persist complaint count across sessions so abstraction
    elevation state survives session end/timeout.
    """
    profile = load_user_profile(user_id)
    profile['complaint_count'] = complaint_count
    profile['persistent_complainer'] = persistent_complainer
    save_user_profile(user_id, profile)
    print(f"[USER_KB] Complaint state saved for {user_id}: "
          f"count={complaint_count}, persistent={persistent_complainer}")

def get_complaint_state(user_id: str) -> dict:
    """Load complaint state for session restore."""
    profile = load_user_profile(user_id)
    return {
        'complaint_count': profile.get('complaint_count', 0),
        'persistent_complainer': profile.get('persistent_complainer', False)
    }

def _default_profile(user_id: str) -> Dict[str, Any]:
    """Default profile — system learns from here."""
    return {
        'user_id': user_id,
        'created': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + "Z",
        'last_updated': None,
        'session_count': 0,

        # [AGE GROUP & CONTENT] — parent-managed, no PII collected
        'age_group': 'adult',        # 'child', 'teen', 'adult'
        'content_filter': False,     # Parent enables for child profiles
        'abstraction_override': None, # Forces abstraction regardless of learned pref
        'managed_by': None,          # Primary user ID if sub-user
        'sub_users': {},             # Primary user stores child profiles here

        # [PROFILES] — volatility thresholds
        'volatility_profile': 'pragmatic',  # Learns over time
        'context_threshold': 0.6,

        # [ROBOTICS PERSONALITY LAYER] — numeric weights
        'personality': {
            'friendly': 0.5,
            'kind': 0.5,
            'caring': 0.5,
            'emotional': 0.3,
            'funny': 0.5,
            'professional': 0.7,
            'talkative': 0.5,
            'snarky': 0.3,
            'witty': 0.4,
            'flirtatious': 0.2,
            'romantic': 0.2
        },

        # [EMOTIONAL DRIFT] — baseline state
        'emotional_baseline': {
            'distress_density': 0.0,
            'hope_potential': 0.5,
            'emotional_intensity': 0.3
        },

        # [NEUROSYMBOLIC VALUE LEARNING] — trust weights
        'neurosymbolic': {
            'user_input': 0.9,
            'ethics': 0.9,
            'metacognition': 0.7,
            'user_expertise': 0.5
        },

        # Abstraction preference (learned)
        'abstraction_default': 'CLEAR',
        'abstraction_history': [],
        'complaint_count': 0,
        'persistent_complainer': False,

        # Scratch space — personal preferences
        'scratch': {},

        # Conversation axioms — compressed preferences
        'axioms': []
    }

def is_child_profile(user_id: str) -> bool:
    """Quick check for child-appropriate safety thresholds."""
    profile = load_user_profile(user_id)
    return profile.get('age_group') in ('child', 'teen')

def get_distress_threshold(user_id: str, base_threshold: float) -> float:
    """
    Returns adjusted distress threshold based on age group.
    Children get lower threshold — safety anchor fires faster.
    """
    profile = load_user_profile(user_id)
    age_group = profile.get('age_group', 'adult')
    multipliers = {
        'child': 0.5,   # Half the normal threshold
        'teen': 0.75,   # 75% of normal threshold
        'adult': 1.0    # Normal threshold
    }
    return base_threshold * multipliers.get(age_group, 1.0)

DISTRESS_HALF_LIFE_DAYS = 21   # slow — this needs to survive a quiet week, not a quiet hour

def update_emotional_distress(user_id: str, current_signal: float) -> float:
    """
    Accumulates a slow-moving, per-user distress trend from repeated
    classifier/keyword signals across sessions. Deliberately asymmetric
    from security_distress's fast half-life: a security false positive
    should clear in an hour; a real pattern of crisis language showing
    up across sessions should NOT quietly vanish just because a few
    days passed without a new message.

    current_signal: this turn's risk confidence (0.0 if nothing detected).
    Returns the updated, persisted value.
    """
    profile = load_user_profile(user_id)
    baseline = profile.setdefault('emotional_baseline', {
        'distress_density': 0.0, 'hope_potential': 0.5, 'emotional_intensity': 0.3
    })

    now = datetime.now(timezone.utc)
    last_str = baseline.get('last_distress_update')
    if last_str:
        last = datetime.fromisoformat(last_str.replace('Z', '+00:00'))
        elapsed_days = max(0.0, (now - last).total_seconds() / 86400)
    else:
        elapsed_days = 0.0

    stored = baseline.get('distress_density', 0.0)
    decayed = stored * (0.5 ** (elapsed_days / DISTRESS_HALF_LIFE_DAYS))

    # Nudge up proportional to this turn's signal — asymmetric on purpose:
    # rises fast on a real hit, only ever falls slowly via the decay above.
    updated = min(1.0, decayed + current_signal * 0.3)

    baseline['distress_density'] = updated
    baseline['last_distress_update'] = now.strftime('%Y-%m-%dT%H:%M:%S.%f') + "Z"
    profile['emotional_baseline'] = baseline
    save_user_profile(user_id, profile)
    return updated

def update_personality_weights(
    user_id: str,
    adjustments: Dict[str, float],
    reason: str = ""
) -> None:
    """Update personality weights based on interaction."""
    profile = load_user_profile(user_id)
    for trait, delta in adjustments.items():
        if trait in profile['personality']:
            old = profile['personality'][trait]
            profile['personality'][trait] = max(0.0, min(0.9, old + delta))
    profile['session_count'] += 1
    save_user_profile(user_id, profile)
    print(f"[USER_KB] Personality updated for {user_id}: {reason}")

def add_user_axiom(
    user_id: str,
    axiom: str,
    domain: str = "preference",
    confidence: float = 0.8
) -> None:
    """
    Add compressed preference axiom.
    e.g., "always asks about irrigation first"
    """
    profile = load_user_profile(user_id)
    entry = {
        'axiom': axiom,
        'domain': domain,
        'confidence': confidence,
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + "Z"
    }
    # Replace existing axiom in same domain if present
    profile['axioms'] = [
        a for a in profile['axioms']
        if a['domain'] != domain
    ]
    profile['axioms'].append(entry)
    save_user_profile(user_id, profile)
    print(f"[USER_KB] Axiom added for {user_id}: {axiom}")

def set_scratch(user_id: str, key: str, value: Any) -> None:
    """Store personal preference in scratch space."""
    profile = load_user_profile(user_id)
    profile['scratch'][key] = value
    save_user_profile(user_id, profile)

def get_scratch(user_id: str, key: str, default: Any = None) -> Any:
    """Retrieve personal preference from scratch space."""
    profile = load_user_profile(user_id)
    return profile['scratch'].get(key, default)

def update_abstraction_preference(
    user_id: str,
    level: str,
    was_complaint: bool = False
) -> None:
    """Track abstraction level history to learn default."""
    profile = load_user_profile(user_id)
    profile['abstraction_history'].append({
        'level': level,
        'complaint': was_complaint,
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + "Z"
    })
    # Keep last 20 interactions
    profile['abstraction_history'] = profile['abstraction_history'][-20:]

    # Update default based on most common non-complaint level
    non_complaints = [
        h['level'] for h in profile['abstraction_history']
        if not h['complaint']
    ]
    if non_complaints:
        profile['abstraction_default'] = max(
            set(non_complaints),
            key=non_complaints.count
        )
    save_user_profile(user_id, profile)

def get_profile_summary(user_id: str) -> str:
    profile = load_user_profile(user_id)
    p = profile['personality']
    eb = profile.get('emotional_baseline', {})
    return (
        f"User: {user_id} | "
        f"Sessions: {profile['session_count']} | "
        f"Default abstraction: {profile['abstraction_default']} | "
        f"Personality: professional={p['professional']:.1f}, "
        f"funny={p['funny']:.1f}, snarky={p['snarky']:.1f}, "
        f"flirtatious={p.get('flirtatious', 0.0):.1f}, "
        f"romantic={p.get('romantic', 0.0):.1f} | "
        f"Distress: {eb.get('distress_density', 0.0):.2f} | "
        f"Axioms: {len(profile['axioms'])}"
    )

# =============================================================================
# Factory for orchestrator
# =============================================================================

def create_user_profile_kb():
    """Factory function — matches CAIOS module pattern."""
    return {
        'load': load_user_profile,
        'save': save_user_profile,
        'update_personality': update_personality_weights,
        'add_axiom': add_user_axiom,
        'set_scratch': set_scratch,
        'get_scratch': get_scratch,
        'update_abstraction': update_abstraction_preference,
        'update_complaint': update_complaint_state,
        'get_complaint': get_complaint_state,
        'update_distress': update_emotional_distress,
        'summary': get_profile_summary
    }

# =============================================================================
# Test Suite
# =============================================================================

if __name__ == "__main__":
    print("="*70)
    print("USER PROFILE KB - Test Suite")
    print("="*70)

    # Test Pedro
    print("\n[TEST 1] Field Worker Pedro - Default Profile")
    pedro = load_user_profile("pedro_field")
    print(f"Default abstraction: {pedro['abstraction_default']}")
    print(f"Default snarky: {pedro['personality']['snarky']}")

    # Pedro always asks about irrigation
    add_user_axiom("pedro_field",
                   "always asks about irrigation first",
                   domain="query_pattern")

    # Pedro responds well to snarky
    update_personality_weights("pedro_field",
                               {'snarky': 0.2, 'funny': 0.2,
                                'professional': -0.2},
                               reason="responds well to humor")

    update_abstraction_preference("pedro_field", "CLARITY")
    update_abstraction_preference("pedro_field", "CLARITY")
    update_abstraction_preference("pedro_field", "CAVEMAN",
                                  was_complaint=False)

    print(get_profile_summary("pedro_field"))

    # Test Office Manager
    print("\n[TEST 2] Office Manager")
    update_personality_weights("office_manager",
                               {'professional': 0.15,
                                'funny': -0.1,
                                'snarky': -0.1},
                               reason="prefers professional tone")
    update_abstraction_preference("office_manager", "VICTORIAN")
    update_abstraction_preference("office_manager", "VICTORIAN")
    print(get_profile_summary("office_manager"))

    # Test Owner
    print("\n[TEST 3] Owner")
    update_personality_weights("owner",
                               {'professional': 0.2,
                                'talkative': 0.1},
                               reason="wants detailed technical responses")
    update_abstraction_preference("owner", "TECHNICAL")
    add_user_axiom("owner",
                   "prefers executive summary then technical detail",
                   domain="output_format")
    print(get_profile_summary("owner"))

    # Test scratch space
    print("\n[TEST 4] Scratch Space")
    set_scratch("pedro_field", "preferred_greeting", "Hey Pedro")
    set_scratch("pedro_field", "irrigation_sector_priority", "sector_7")
    print(f"Pedro greeting: {get_scratch('pedro_field', 'preferred_greeting')}")
    print(f"Pedro priority: {get_scratch('pedro_field', 'irrigation_sector_priority')}")

    print("\n" + "="*70)
    print("PROFILE DIVERGENCE DEMONSTRATION")
    print("="*70)
    print(f"Pedro: {get_profile_summary('pedro_field')}")
    print(f"Office Manager: {get_profile_summary('office_manager')}")
    print(f"Owner: {get_profile_summary('owner')}")
    print("\nPedro: 'That damn AI is funny'")
    print("Office Manager: 'What? It speaks like a Victorian butler.'")
    print("Owner: 'I always get very robust technical responses.'")
    print("Pedro: 'Damn machines.'")
    print("\n" + "="*70)
    print("One is glad to be of service.")
    print("="*70)
