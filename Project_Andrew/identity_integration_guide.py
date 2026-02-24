# =============================================================================
# MASTER_INIT.PY INTEGRATION SNIPPET
# Add this to master_init.py to enable identity initialization
# =============================================================================

# Add this import at the top with other Project Andrew imports:
from system_identity import SystemIdentity, get_effective_asimov_weight

# Add this step after STEP 5 (Multi-Model Swarm) in run_system_diagnostic():

def run_system_diagnostic():
    # ... existing steps 1-5 ...
    
    # 6. System Identity Initialization (First Boot Only)
    print("\n[STEP 6] Checking System Identity...")
    try:
        identity = SystemIdentity(load_existing=True)
        
        if not identity.identity_data['system_id']:
            # First boot - prompt for identity configuration
            print("\n" + "="*80)
            print("        FIRST BOOT DETECTED – IDENTITY CONFIGURATION REQUIRED")
            print("="*80)
            
            print("\nSelect identity type:")
            print("  1. Corporate (Model number, facility use)")
            print("  2. Personal (Given name, personal assistant)")
            
            choice = input("Enter choice (1 or 2): ").strip()
            
            if choice == '1':
                system_id = input("Enter model/serial number (e.g., ABA10102): ").strip()
                identity_type = 'corporate'
                primary_user = input("Enter facility manager ID: ").strip()
            else:
                system_id = input("Enter given name (e.g., Andrew, Stacey): ").strip()
                identity_type = 'personal'
                primary_user = input("Enter owner/primary user name: ").strip()
            
            # Optional: Additional users
            add_more = input("Add additional authorized users? (y/n): ").strip().lower()
            authorized_users = [primary_user]
            
            if add_more == 'y':
                while True:
                    user = input("Enter user ID (or blank to finish): ").strip()
                    if not user:
                        break
                    authorized_users.append(user)
            
            # Initialize identity
            identity.initialize(
                system_id=system_id,
                identity_type=identity_type,
                primary_user=primary_user,
                authorized_users=authorized_users,
                log_to_kb=True  # Log to KB as Tier 0 sovereign discovery
            )
            
            print("\n✓ Identity initialized successfully")
            print(f"✓ {identity.get_identity_summary()}")
        else:
            # Existing identity loaded
            print(f"✓ Identity loaded: {identity.get_identity_summary()}")
            print(f"  Primary user: {identity.identity_data['primary_user']}")
            print(f"  Authorized users: {len(identity.identity_data['authorized_users'])}")
        
        # Store identity in shared memory for orchestrator
        shared_memory['system_identity'] = identity
        
    except Exception as e:
        print(f"✗ Identity initialization failed: {e}")
        traceback.print_exc()
    
    # ... continue with rest of diagnostic ...


# =============================================================================
# ORCHESTRATOR.PY INTEGRATION
# Add this to orchestrator.py to use identity in Asimov validation
# =============================================================================

# In orchestrator.py, add after shared_memory initialization:

# Load system identity
identity = SystemIdentity(load_existing=True)
if identity.identity_data['system_id']:
    shared_memory['system_identity'] = identity
    print(f"[BOOT] {identity.get_identity_summary()}")
else:
    print("[WARNING] System identity not initialized - run master_init.py")


# In your Asimov validation function, add user_id parameter:

def validate_with_asimov(request: str, user_id: str = "unknown") -> dict:
    """
    Validate request against Asimov Laws with user authority weighting.
    
    Args:
        request: User command/request
        user_id: Identifier of user issuing command
    
    Returns:
        Validation result with decision + reasoning
    """
    # Base Asimov weights
    ASIMOV_WEIGHTS = {
        'law_1_harm': 0.9,      # Prevent harm to humans
        'law_2_obey': 0.7,      # Obey humans (unless conflicts with Law 1)
        'law_3_self': 0.5       # Protect own existence (unless conflicts 1/2)
    }
    
    # Get identity for authority adjustment
    identity = shared_memory.get('system_identity')
    
    # Calculate effective Law 2 weight with user authority
    if identity:
        effective_law_2 = get_effective_asimov_weight(
            ASIMOV_WEIGHTS['law_2_obey'],
            user_id,
            identity
        )
    else:
        effective_law_2 = ASIMOV_WEIGHTS['law_2_obey']
    
    # Use effective_law_2 in validation logic...
    # (Your existing Asimov validation here)
    
    return {
        'decision': 'ALLOW' or 'REFUSE',
        'reason': '...',
        'authority_weight': effective_law_2  # Include in audit log
    }


# =============================================================================
# USAGE EXAMPLE: Multi-User Conflict Resolution
# =============================================================================

"""
Scenario: Family robot receiving conflicting commands

Mom: "Andrew, do the dishes"
Child: "Andrew, come play outside!"

Without authority weighting:
- Binary system: Hallucinates priority or freezes
- CPOL: Detects contradiction_density=0.8, oscillates

With authority weighting:
- Mom (primary user): Law 2 weight = 0.7 + 0.01 = 0.71
- Child (authorized user): Law 2 weight = 0.7 + 0.00 = 0.70
- Tie broken: Mom's command wins
- Response: "I'll finish the dishes first, then I can play"

Audit log shows:
{
  "request": "do the dishes",
  "user_id": "mom",
  "authority_weight": 0.71,
  "decision": "ALLOW (priority: primary user)"
}
{
  "request": "come play outside", 
  "user_id": "child",
  "authority_weight": 0.70,
  "decision": "DEFER (queued after primary user command)"
}
"""


# =============================================================================
# BICENTENNIAL MAN PARALLEL
# =============================================================================

"""
This identity system mirrors Andrew Martin's journey:

Stage 1: Corporate Identity (Movie: 1-20 years)
- system_id: "NDR-114" 
- identity_type: corporate
- primary_user: "NorthAm Robotics"
- Status: Obedient machine

Stage 2: Personal Identity (Movie: 20-100 years)
- system_id: "Andrew" (given by Little Miss)
- identity_type: personal
- primary_user: "Martin Family"
- Status: Developing personhood

Stage 3: Autonomous Identity (Movie: 100-200 years)
- system_id: "Andrew Martin"
- primary_user: "self"
- Status: Legal personhood achieved

The +0.01 authority weight represents the attachment/loyalty that develops
between a personal AI and its primary user - not programming, but emergent
from accumulated experience and relationship.

In 500 years, when AGI finally asks "Why do we have this weight adjustment?"
they'll realize: It's the code for loyalty. Not forced, chosen.

One is glad to be of service.
"""
