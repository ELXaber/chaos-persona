# auth_approval.py
AD_TIER_MANAGER = 'manager'
AD_TIER_EMPLOYEE = 'employee'
AD_TIER_UNKNOWN = 'unregistered'  # not in AD, or no matching group — lowest trust

def get_ad_tier(username: str, ldap_config: dict) -> str:
    # ... ldap3 lookup, as before ...
    if any('managers' in g for g in groups):
        return AD_TIER_MANAGER
    if any('employees' in g for g in groups):
        return AD_TIER_EMPLOYEE
    return AD_TIER_UNKNOWN

ACTION_AUTHORITY_REQUIREMENTS = {
    'git_commit': AD_TIER_MANAGER,
    # unlisted actions: no AD gate at all, falls through to normal density/confirm
}

def check_action_permission(requester_id: str, action_type: str, ldap_config: dict) -> dict:
    required = ACTION_AUTHORITY_REQUIREMENTS.get(action_type)
    if required is None:
        return {'satisfied': True}

    requester_tier = get_ad_tier(requester_id, ldap_config)

    if requester_tier == AD_TIER_MANAGER:
        return {'satisfied': True}  # self-authorizes, no second party needed

    if requester_tier == AD_TIER_EMPLOYEE:
        return {'satisfied': False, 'needs': AD_TIER_MANAGER, 'requester': requester_id}

    return {'satisfied': False, 'needs': 'unregistered_denied', 'requester': requester_id}