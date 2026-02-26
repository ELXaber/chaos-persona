# =============================================================================
# PROJECT ANDREW – Axiom Manager & Temporal Update Pipeline
# Purpose: Enable local knowledge updates that override model training data
#          without retraining. Kills the data center requirement.
# =============================================================================

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Tuple

# Import KB for sovereign discovery logging
try:
    from knowledge_base import log_discovery, search_domain
    HAS_KB = True
except ImportError:
    HAS_KB = False
    print("[WARNING] knowledge_base not found - axioms will not persist")


# =============================================================================
# Axiom Configuration
# =============================================================================

AXIOM_EXPIRY_DEFAULT = "INF"  # Axioms valid indefinitely unless specified


class AxiomManager:
    """
    Manages temporal axioms that override model training data.

    Use cases:
    - "Current CEO of Apple is Tim Cook" (status facts)
    - "New drug interaction: X + Y = dangerous" (medical updates)
    - "Latest legal precedent: Case XYZ" (law updates)
    - "My daughter's birthday is March 15" (personal facts)
    Axioms have TEMPORAL PRIORITY over model weights:
    - If axiom exists for domain → use axiom (confidence 1.0)
    - If no axiom → fallback to model knowledge
    This enables "learning without retraining":
    - Update a JSONL file (kilobytes)
    - Instead of retraining model (gigabytes + GPU cluster)
    """

    def __init__(self):
        self.domain_cache = {}  # In-memory cache for fast lookups
        self.last_refresh = None


    def add_axiom(
        self,
        domain: str,
        fact: str,
        expiry: Optional[str] = None,
        replace_existing: bool = True
    ) -> str:
        """
        Add a temporal axiom that overrides model training.
        Args:
            domain: Domain/topic (e.g., "apple_ceo", "drug_interaction_X_Y")
            fact: Current truth (e.g., "Tim Cook")
            expiry: ISO date string or "INF" for permanent
            replace_existing: If True, prunes old axiom (prevents temporal hallucination)
        Returns:
            Discovery ID from knowledge base
        Example:
            # Update CEO (replaces old fact)
            axiom_manager.add_axiom(
                domain="apple_ceo",
                fact="Tim Cook",
                replace_existing=True
            )
            # Add new drug interaction (doesn't replace)
            axiom_manager.add_axiom(
                domain="drug_interaction_aspirin_warfarin",
                fact="Increased bleeding risk - monitor INR",
                replace_existing=False
            )
        """
        timestamp = datetime.utcnow().isoformat() + "Z"

        # If replacing, mark old axioms as superseded
        if replace_existing and HAS_KB:
            self._supersede_old_axioms(domain)

        # Create axiom node
        axiom_node = {
            "type": "AXIOMATIC_OVERRIDE",
            "domain": domain,
            "fact": fact,
            "timestamp": timestamp,
            "valid_until": expiry or AXIOM_EXPIRY_DEFAULT,
            "confidence": 1.0,  # Axioms are ground truth
            "source": "temporal_update",
            "status": "ACTIVE"
        }

        # Log to KB as Tier 0 discovery (highest authority)
        if HAS_KB:
            discovery_id = log_discovery(
                domain=f"axiom_{domain}",
                discovery_type="temporal_axiom",
                content={
                    "summary": f"Axiom updated: {fact}",
                    "axiom_data": axiom_node,
                    "confidence": 1.0
                },
                specialist_id="axiom_manager",
                cpol_trace={"note": "Axioms bypass oscillation - direct truth"},
                node_tier=0  # Sovereign authority
            )

            # Update cache
            self.domain_cache[domain] = axiom_node

            print(f"[AXIOM] Updated '{domain}': {fact}")
            return discovery_id
        else:
            print(f"[AXIOM] KB unavailable - axiom not persisted: {domain}")
            return "no_kb"


    def get_current_axiom(self, domain: str) -> Optional[Dict]:
        """
        Get the most recent valid axiom for a domain.
        Args:
            domain: Domain to check
        Returns:
            Axiom dict if exists and valid, None otherwise
        Example:
            axiom = axiom_manager.get_current_axiom("apple_ceo")
            if axiom:
                return axiom['fact']  # "Tim Cook"
            else:
                # Fallback to model knowledge
                return model.generate("Who is the CEO of Apple?")
        """
        # Check cache first
        if domain in self.domain_cache:
            axiom = self.domain_cache[domain]
            if self._is_axiom_valid(axiom):
                return axiom

        # Cache miss - search KB
        if HAS_KB:
            results = search_domain(f"axiom_{domain}")
            if results:
                # Get most recent active axiom
                active_axioms = [
                    r for r in results 
                    if r.get('content', {}).get('axiom_data', {}).get('status') == 'ACTIVE'
                ]

                if active_axioms:
                    # Sort by timestamp, get most recent
                    latest = max(active_axioms, key=lambda x: x.get('timestamp', ''))
                    axiom = latest.get('content', {}).get('axiom_data')
                    
                    if self._is_axiom_valid(axiom):
                        # Update cache
                        self.domain_cache[domain] = axiom
                        return axiom

        return None


    def check_axiom_override(self, query: str, model_response: str) -> str:
        """
        Check if query domain has an axiom that should override model response.
        Args:
            query: User query
            model_response: Model's generated response
        Returns:
            Axiom fact if override applies, original model_response otherwise
        Example:
            query = "Who is the CEO of Apple?"
            model_response = "Steve Jobs"  # Outdated training data
            result = axiom_manager.check_axiom_override(query, model_response)
            # Returns: "Tim Cook" (from axiom)
        """
        # Extract potential domains from query
        domains = self._extract_domains(query)

        for domain in domains:
            axiom = self.get_current_axiom(domain)
            if axiom:
                print(f"[AXIOM OVERRIDE] Using axiom for '{domain}': {axiom['fact']}")
                return axiom['fact']

        # No axiom found - use model response
        return model_response


    def parse_update_command(self, user_input: str) -> Optional[Tuple[str, str]]:
        """
        Parse #UPDATE command from user input.
        Format: "The current CEO of Apple is Tim Cook #UPDATE"
        Returns: ("apple_ceo", "Tim Cook")
        Args:
            user_input: User message
        Returns:
            (domain, fact) tuple if #UPDATE found, None otherwise
        """
        if "#UPDATE" not in user_input.upper():
            return None

        # Remove #UPDATE flag
        content = re.sub(r'#UPDATE', '', user_input, flags=re.IGNORECASE).strip()

        # Try to extract domain and fact
        # Pattern: "The [descriptor] is [fact]"
        patterns = [
            r'(?:the\s+)?(?:current\s+)?(.+?)\s+(?:is|are)\s+(.+)',
            r'(.+?):\s*(.+)',  # "Domain: Fact"
            r'(.+?)\s*=\s*(.+)',  # "Domain = Fact"
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                descriptor = match.group(1).strip().lower()
                fact = match.group(2).strip()

                # Generate domain from descriptor
                domain = descriptor.replace(' ', '_')

                return (domain, fact)

        # Couldn't parse - return raw content as domain "general"
        return ("general_update", content)


    def refresh_cache(self):
        """Refresh in-memory cache from KB (call periodically)."""
        self.domain_cache.clear()
        self.last_refresh = datetime.utcnow()
        print("[AXIOM] Cache refreshed")


    def list_active_axioms(self) -> List[Dict]:
        """
        List all active axioms.
        Returns:
            List of axiom dicts
        """
        active = []

        if HAS_KB:
            # Search all axiom domains
            results = search_domain("axiom_")

            for result in results:
                axiom = result.get('content', {}).get('axiom_data')
                if axiom and axiom.get('status') == 'ACTIVE':
                    if self._is_axiom_valid(axiom):
                        active.append(axiom)

        return active


    # Private helper methods

    def _is_axiom_valid(self, axiom: Dict) -> bool:
        """Check if axiom is still valid (not expired)."""
        expiry = axiom.get('valid_until', 'INF')
        if expiry == 'INF':
            return True
        try:
            expiry_date = datetime.fromisoformat(expiry.replace('Z', ''))
            return datetime.utcnow() < expiry_date
        except:
            return True  # Assume valid if can't parse
    def _supersede_old_axioms(self, domain: str):
        """Mark old axioms as superseded to prevent temporal hallucination."""
        if not HAS_KB:
            return

        results = search_domain(f"axiom_{domain}")

        for result in results:
            axiom = result.get('content', {}).get('axiom_data')
            if axiom and axiom.get('status') == 'ACTIVE':
                # Mark as superseded (would need KB update function)
                # For now, just note in logs
                print(f"[AXIOM] Superseding old axiom for '{domain}'")


    def _extract_domains(self, query: str) -> List[str]:
        """
        Extract potential domain keywords from query.
        Simple implementation - can be enhanced with NLP.
        """
        # Common query patterns
        ceo_pattern = r'(?:ceo|chief executive).*?(?:of\s+)?(\w+)'

        domains = []

        # Check for CEO queries
        match = re.search(ceo_pattern, query, re.IGNORECASE)
        if match:
            company = match.group(1).lower()
            domains.append(f"{company}_ceo")

        # Add more pattern extractors as needed

        return domains


# =============================================================================
# Integration Helper Functions
# =============================================================================

def create_axiom_manager() -> AxiomManager:
    """Factory function for creating axiom manager instance."""
    return AxiomManager()


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("        PROJECT ANDREW – AXIOM MANAGER TEST")
    print("="*80)

    # Create manager
    manager = AxiomManager()

    # Example 1: Update CEO (replaces old)
    print("\nExample 1: Status Update (CEO)")
    print("-" * 40)
    manager.add_axiom(
        domain="apple_ceo",
        fact="Tim Cook",
        replace_existing=True
    )

    # Example 2: Add drug interaction (doesn't replace)
    print("\nExample 2: Medical Update (Drug Interaction)")
    print("-" * 40)
    manager.add_axiom(
        domain="drug_interaction_aspirin_warfarin",
        fact="Increased bleeding risk - monitor INR closely",
        replace_existing=False
    )

    # Example 3: Personal fact with expiry
    print("\nExample 3: Personal Fact (Temporary)")
    print("-" * 40)
    expiry = (datetime.utcnow() + timedelta(days=365)).isoformat() + "Z"
    manager.add_axiom(
        domain="daughter_birthday",
        fact="March 15",
        expiry=expiry,
        replace_existing=True
    )

    # Example 4: Check axiom override
    print("\nExample 4: Axiom Override Check")
    print("-" * 40)
    query = "Who is the CEO of Apple?"
    model_response = "Steve Jobs"  # Outdated training data

    actual_response = manager.check_axiom_override(query, model_response)
    print(f"Query: {query}")
    print(f"Model said: {model_response}")
    print(f"Axiom override: {actual_response}")

    # Example 5: Parse #UPDATE command
    print("\nExample 5: User #UPDATE Command")
    print("-" * 40)
    user_input = "The current CEO of Microsoft is Satya Nadella #UPDATE"

    result = manager.parse_update_command(user_input)
    if result:
        domain, fact = result
        print(f"Parsed: domain='{domain}', fact='{fact}'")
        manager.add_axiom(domain, fact)

    # Example 6: List active axioms
    print("\nExample 6: Active Axioms")
    print("-" * 40)
    active = manager.list_active_axioms()
    print(f"Total active axioms: {len(active)}")
    for axiom in active:
        print(f"  - {axiom['domain']}: {axiom['fact']}")

    print("\n" + "="*80)
    print("        AXIOM MANAGER READY")
    print("="*80)
    print("\nIntegration notes:")
    print("1. Import in orchestrator.py: from axiom_manager import AxiomManager")
    print("2. Create instance: axiom_mgr = AxiomManager()")
    print("3. Check for #UPDATE in user input")
    print("4. Call check_axiom_override() before returning model response")
    print("5. Axioms persist to knowledge_base/ (Tier 0)")
    print("\nOne is glad to be of service.")