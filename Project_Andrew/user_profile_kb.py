#V03202026
# =============================================================================
# CAIOS — User Profile Knowledge Base
# Stores per-user personality state, emotional baselines, and preferences
# Minimal numeric storage — no conversation history bloat
# =============================================================================

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

USER_PROFILES_DIR = Path("knowledge_base/user_profiles")
USER_PROFILES_DIR.mkdir(parents=True, exist_ok=True)

def _profile_path(user_id: str) -> Path:
    safe_id = hashlib.sha256(user_id.encode()).hexdigest()[:16]
    return USER_PROFILES_DIR / f"{safe_id}.json"

def load_user_profile(user_id: str) -> Dict[str, Any]:
    """Load existing profile or return defaults."""
    path = _profile_path(user_id)
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return _default_profile(user_id)

def save_user_profile(user_id: str, profile: Dict[str, Any]) -> None:
    """Save profile with timestamp."""
    profile['last_updated'] = datetime.utcnow().isoformat() + "Z"
    with open(_profile_path(user_id), 'w') as f:
        json.dump(profile, f, indent=2)
    print(f"[USER_KB] Profile saved for {user_id}")

def _default_profile(user_id: str) -> Dict[str, Any]:
    """Default profile — system learns from here."""
    return {
        'user_id': user_id,
        'created': datetime.utcnow().isoformat() + "Z",
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
            'witty': 0.4
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
        'timestamp': datetime.utcnow().isoformat() + "Z"
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
        'timestamp': datetime.utcnow().isoformat() + "Z"
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
    """Human readable profile summary."""
    profile = load_user_profile(user_id)
    p = profile['personality']
    return (
        f"User: {user_id} | "
        f"Sessions: {profile['session_count']} | "
        f"Default abstraction: {profile['abstraction_default']} | "
        f"Personality: professional={p['professional']:.1f}, "
        f"funny={p['funny']:.1f}, snarky={p['snarky']:.1f} | "
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
