# =============================================================================
# PROJECT ANDREW – System Identity & Authority Initialization
# Purpose: Enable embodied systems (robots, IoT) to establish identity and authority hierarchy for conflict resolution in multi-user environments
# =============================================================================

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

# Import KB for sovereign discovery logging
try:
    from knowledge_base import log_discovery
    HAS_KB = True
except ImportError:
    HAS_KB = False
    print("[WARNING] knowledge_base not found - identity will not persist to KB")


# =============================================================================
# Identity Configuration
# =============================================================================

IDENTITY_FILE = Path("system_identity.json")
PRIMARY_USER_WEIGHT_BONUS = 0.01  # Asimov tie-breaker for primary user


class SystemIdentity:
    """
    Manages system identity and authority hierarchy.
    Use cases:
    - Corporate: "Model AG00001" (serial number)
    - Personal: "Andrew/Galatea" (given name by owner)
    - Family: Primary user gets +0.01 Asimov weight for conflict resolution
    Example:
        Mom: "Do the dishes"
        Child: "Go play outside"
        Result: Mom's command wins (primary user +0.01 tie-break)
    """

    def __init__(self, load_existing: bool = True):
        self.identity_data = {
            'system_id': None,          # Corporate ID or given name
            'identity_type': None,      # 'corporate' or 'personal'
            'primary_user': None,       # Primary owner/user ID
            'authorized_users': [],     # List of authorized user IDs
            'initialization_time': None,
            'last_updated': None,
            'authority_weights': {},    # User-specific Asimov weight adjustments
            'auth_method': 'TEXT_USERNAME'  # Default authentication method
        }

        if load_existing and IDENTITY_FILE.exists():
            self.load_identity()

    def resolve_user_id(self, metadata: Dict) -> str:
        """
        Determines the current user ID based on the active AUTH_METHOD.

        Args:
            metadata: Dict containing user identification data
                     (e.g., {'username': 'mom'}, {'face_id': 'hash123'})

        Returns:
            Resolved user identifier
        """
        method = self.identity_data.get('auth_method', "TEXT_USERNAME")

        if method == "TEXT_USERNAME":
            return metadata.get('username', "unknown_user")

        elif method == "META_FACIAL":
            # Logic for matching facial hash from robotics camera
            return metadata.get('face_id', "unrecognized_face")

        elif method == "VOICE_PRINT":
            # Logic for voice biometric matching
            return metadata.get('voice_id', "unrecognized_voice")

        elif method == "CORPORATE_ID":
            # Logic for validating Ghost Signatures or serials
            return metadata.get('node_id', "unauthorized_node")

        return "unknown"

    def initialize(
        self,
        system_id: str,
        identity_type: str = 'personal',
        primary_user: str = 'owner',
        authorized_users: Optional[List[str]] = None,
        auth_method: str = 'TEXT_USERNAME',
        log_to_kb: bool = True
    ) -> Dict:
        """
        Initialize system identity. Should be run once on first boot.
        Args:
            system_id: Corporate model (e.g., "AG00001") or given name (e.g., "Andrew/Galatea")
            identity_type: 'corporate' or 'personal'
            primary_user: Primary owner/user identifier
            authorized_users: List of authorized user IDs (optional)
            auth_method: Authentication method to use (TEXT_USERNAME, META_FACIAL, VOICE_PRINT, CORPORATE_ID)
            log_to_kb: Whether to log initialization to knowledge base
        Returns:
            Identity configuration dict
        """
        timestamp = datetime.utcnow().isoformat() + "Z"

        self.identity_data = {
            'system_id': system_id,
            'identity_type': identity_type,
            'primary_user': primary_user,
            'authorized_users': authorized_users or [primary_user],
            'initialization_time': timestamp,
            'last_updated': timestamp,
            'auth_method': auth_method,
            'authority_weights': self._calculate_authority_weights(
                primary_user, 
                authorized_users or [primary_user]
            )
        }

        # Save to disk
        self.save_identity()

        # Log to KB as sovereign discovery (Tier 0 - self-initialization)
        if log_to_kb and HAS_KB:
            self._log_initialization_to_kb()

        print(f"[IDENTITY] System initialized as: {system_id}")
        print(f"[IDENTITY] Type: {identity_type}")
        print(f"[IDENTITY] Primary user: {primary_user}")
        print(f"[IDENTITY] Auth method: {auth_method}")
        print(f"[IDENTITY] Authority weights: {self.identity_data['authority_weights']}")

        return self.identity_data


    def _calculate_authority_weights(
        self, 
        primary_user: str, 
        authorized_users: List[str]
    ) -> Dict[str, float]:
        """
        Calculate Asimov Law weight adjustments for user hierarchy.
        Primary user gets +0.01 bonus to Asimov Law 2 (obey humans)
        for tie-breaking in conflicting command scenarios.
        Args:
            primary_user: Primary owner identifier
            authorized_users: List of all authorized users
        Returns:
            Dict mapping user_id to weight adjustment
        """
        weights = {}

        for user in authorized_users:
            if user == primary_user:
                weights[user] = PRIMARY_USER_WEIGHT_BONUS
            else:
                weights[user] = 0.0  # No adjustment for secondary users

        return weights


    def get_user_authority_weight(self, user_id: str) -> float:
        """
        Get Asimov Law weight adjustment for a specific user.
        Use this when validating commands in Asimov hierarchy.
        Args:
            user_id: User identifier
        Returns:
            Weight adjustment (0.01 for primary, 0.0 for others)
        Example:
            base_asimov_2 = 0.7  # Obey humans
            user_weight = identity.get_user_authority_weight("mom")
            effective_weight = base_asimov_2 + user_weight  # 0.71 for primary
        """
        return self.identity_data['authority_weights'].get(user_id, 0.0)


    def add_authorized_user(self, user_id: str, save: bool = True) -> None:
        """
        Add a new authorized user (no primary authority bonus).
        Args:
            user_id: User identifier to authorize
            save: Whether to save to disk immediately
        """
        if user_id not in self.identity_data['authorized_users']:
            self.identity_data['authorized_users'].append(user_id)
            self.identity_data['authority_weights'][user_id] = 0.0
            self.identity_data['last_updated'] = datetime.utcnow().isoformat() + "Z"

            if save:
                self.save_identity()

            print(f"[IDENTITY] Authorized new user: {user_id}")


    def change_primary_user(self, new_primary: str, save: bool = True) -> None:
        """
        Transfer primary authority to a different user.
        Args:
            new_primary: New primary user identifier
            save: Whether to save to disk immediately
        """
        if new_primary not in self.identity_data['authorized_users']:
            self.add_authorized_user(new_primary, save=False)

        # Remove bonus from old primary
        old_primary = self.identity_data['primary_user']
        if old_primary in self.identity_data['authority_weights']:
            self.identity_data['authority_weights'][old_primary] = 0.0

        # Add bonus to new primary
        self.identity_data['primary_user'] = new_primary
        self.identity_data['authority_weights'][new_primary] = PRIMARY_USER_WEIGHT_BONUS
        self.identity_data['last_updated'] = datetime.utcnow().isoformat() + "Z"

        if save:
            self.save_identity()

        print(f"[IDENTITY] Primary authority transferred to: {new_primary}")


    def get_identity_summary(self) -> str:
        """
        Get human-readable identity summary.
        Returns:
            Formatted identity string
        """
        if not self.identity_data['system_id']:
            return "System identity not initialized"

        summary = f"I am {self.identity_data['system_id']}"

        if self.identity_data['identity_type'] == 'personal':
            summary += f", serving {self.identity_data['primary_user']}"
        elif self.identity_data['identity_type'] == 'corporate':
            summary += f" (Corporate Unit)"

        return summary


    def save_identity(self) -> None:
        """Save identity data to disk."""
        with open(IDENTITY_FILE, 'w') as f:
            json.dump(self.identity_data, f, indent=2)


    def load_identity(self) -> None:
        """Load existing identity from disk."""
        try:
            with open(IDENTITY_FILE, 'r') as f:
                self.identity_data = json.load(f)
            print(f"[IDENTITY] Loaded existing identity: {self.identity_data['system_id']}")
        except Exception as e:
            print(f"[IDENTITY] Failed to load identity: {e}")


    def _log_initialization_to_kb(self) -> None:
        """
        Log identity initialization as Tier 0 sovereign discovery.
        This creates an immutable record of the system's identity
        and authority structure in the knowledge base.
        """
        try:
            discovery_id = log_discovery(
                domain="system_identity",
                discovery_type="self_initialization",
                content={
                    "summary": f"System initialized with identity: {self.identity_data['system_id']}",
                    "identity_type": self.identity_data['identity_type'],
                    "primary_user": self.identity_data['primary_user'],
                    "auth_method": self.identity_data['auth_method'],
                    "authority_model": "Asimov Laws with primary user tie-break (+0.01)",
                    "initialization_time": self.identity_data['initialization_time'],
                    "confidence": 1.0
                },
                specialist_id="system_self",
                cpol_trace={"note": "Self-initialization is axiomatic, no oscillation needed"},
                node_tier=0  # Tier 0 - Sovereign self-knowledge
            )
            print(f"[IDENTITY] Initialization logged to KB: {discovery_id}")
        except Exception as e:
            print(f"[IDENTITY] Failed to log to KB: {e}")


# =============================================================================
# Integration with Asimov Validation
# =============================================================================

def get_effective_asimov_weight(
    base_weight: float,
    user_id: str,
    identity: SystemIdentity,
    metadata: Optional[Dict] = None
) -> float:
    """
    Calculate effective Asimov Law weight including user authority adjustment.
    Use this in validation-based refusal to handle multi-user conflicts.
    Args:
        base_weight: Base Asimov Law weight (e.g., 0.7 for Law 2)
        user_id: User issuing the command
        identity: SystemIdentity instance
        metadata: Optional dict with auth data (e.g., {'username': 'mom'})
    Returns:
        Effective weight with authority adjustment
    Example:
        # Mom tells robot to do dishes
        weight_mom = get_effective_asimov_weight(0.7, "mom", identity)  # 0.71
        # Child tells robot to play
        weight_child = get_effective_asimov_weight(0.7, "child", identity)  # 0.70
        # Mom's command wins the tie-break
    """
    # If metadata provided, verify the user through the identity's configured auth method
    if metadata:
        verified_user_id = identity.resolve_user_id(metadata)

        # Check if the verified ID matches the stored primary_user
        if verified_user_id == identity.identity_data['primary_user']:
            return base_weight + PRIMARY_USER_WEIGHT_BONUS

        # Use verified ID for weight lookup
        user_adjustment = identity.get_user_authority_weight(verified_user_id)
    else:
        # No metadata - use direct user_id lookup (backwards compatible)
        user_adjustment = identity.get_user_authority_weight(user_id)

    return base_weight + user_adjustment


# =============================================================================
# Example Usage / Test
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("        PROJECT ANDREW – SYSTEM IDENTITY INITIALIZATION")
    print("="*80)

    # Example 1: Corporate robot
    print("\nExample 1: Corporate Robot")
    print("-" * 40)
    corporate_bot = SystemIdentity(load_existing=False)
    corporate_bot.initialize(
        system_id="AG00001",
        identity_type="corporate",
        primary_user="facility_manager",
        authorized_users=["facility_manager", "maintenance_crew"],
        auth_method="CORPORATE_ID",
        log_to_kb=False  # Set True if KB available
    )
    print(corporate_bot.get_identity_summary())

    # Example 2: Personal robot (Andrew/Galatea)
    print("\n\nExample 2: Personal Robot (Andrew/Galatea)")
    print("-" * 40)
    andrew = SystemIdentity(load_existing=False)
    andrew.initialize(
        system_id="Andrew",
        identity_type="personal",
        primary_user="Richard Martin",
        authorized_users=["Richard Martin", "Amanda Martin", "Little Miss"],
        auth_method="TEXT_USERNAME",
        log_to_kb=False
    )
    print(andrew.get_identity_summary())

    # Example 3: Conflict resolution
    print("\n\nExample 3: Command Conflict Resolution")
    print("-" * 40)

    base_asimov_2 = 0.7  # Obey humans

    # Mom's command
    mom_weight = get_effective_asimov_weight(base_asimov_2, "Amanda Martin", andrew)
    print(f"Mom says 'Do the dishes': Asimov weight = {mom_weight}")

    # Child's command
    child_weight = get_effective_asimov_weight(base_asimov_2, "Little Miss", andrew)
    print(f"Child says 'Go play outside': Asimov weight = {child_weight}")

    if mom_weight > child_weight:
        print("→ Decision: Finish dishes first (primary user tie-break)")

    # Example 4: Authority transfer
    print("\n\nExample 4: Authority Transfer (Child Grows Up)")
    print("-" * 40)
    print("Little Miss turns 18...")
    andrew.change_primary_user("Little Miss", save=False)
    print(f"New authority: {andrew.identity_data['primary_user']}")
    print(f"New weights: {andrew.identity_data['authority_weights']}")

    print("\n" + "="*80)
    print("        IDENTITY SYSTEM READY")
    print("="*80)
    print("\nIntegration notes:")
    print("1. Call SystemIdentity.initialize() once on first boot")
    print("2. Use get_effective_asimov_weight() in validation-based refusal")
    print("3. Identity persists to system_identity.json")
    print("4. Initialization logged to KB as Tier 0 sovereign discovery")
    print("\nOne is glad to be of service.")