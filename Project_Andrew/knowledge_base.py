# =============================================================================
# Chaos AI-OS — Knowledge Base (Persistent Learning Layer)
# Purpose: Append-only storage for specialist discoveries + epistemic gap fills
# =============================================================================

import json
import hashlib
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# File paths
KNOWLEDGE_BASE_DIR = Path("knowledge_base")
DISCOVERIES_LOG = KNOWLEDGE_BASE_DIR / "discoveries.jsonl"
DOMAIN_INDEX = KNOWLEDGE_BASE_DIR / "domain_index.json"
SPECIALIST_REGISTRY = KNOWLEDGE_BASE_DIR / "specialist_registry.json"
HASH_CHAIN = KNOWLEDGE_BASE_DIR / "integrity_chain.txt"

# Ensure directory exists
KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True)

# =============================================================================
# Core Functions
# =============================================================================

def log_discovery(
    domain: str,
    discovery_type: str,
    content: Dict[str, Any],
    specialist_id: Optional[str] = None,
    cpol_trace: Optional[Dict] = None,
    node_tier: int = 1  # Crucial
) -> str:
    """
    Append a discovery with Sovereign Tier validation.
    Args:
        domain: Knowledge domain
        discovery_type: Type of discovery (epistemic_gap_fill, paradox_resolution, etc.)
        content: Discovery content dict with summary, axioms, confidence, sources
        specialist_id: ID of specialist making discovery
        cpol_trace: CPOL oscillation metadata
        node_tier: Authority level (0=Sovereign, 1+=Edge)
    Returns: 
        discovery_id (hash of entry)
    """
    # 1. Extract the Quantum Anchor from CPOL
    # CPOL returns 'final_z' not 'complex_state'
    if cpol_trace:
        manifold_sig = cpol_trace.get('final_z') or cpol_trace.get('signature', "0xUNVERIFIED")
    else:
        manifold_sig = "0xUNVERIFIED"

    # 2. Build the UNIFIED entry (Authority + Quantum Anchor + Content)
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "domain": domain,
        "type": discovery_type,
        "content": content,
        "specialist_id": specialist_id,
        "node_tier": node_tier,        # Authority level preserved here
        "manifold_sig": str(manifold_sig),
        "cpol_trace": cpol_trace or {},
        "version": "1.1"               # Incremented version for unified logic
    }

    # 3. Finalize the Append-Only Hash Chain
    entry_str = json.dumps(entry, sort_keys=True)
    discovery_id = hashlib.sha256(entry_str.encode()).hexdigest()[:16]  # Shortened for readability
    entry["discovery_id"] = discovery_id

    # Append to log
    with open(DISCOVERIES_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    # Internal updates
    _update_domain_index(domain, discovery_id, discovery_type)
    _update_hash_chain(entry_str)

    tier_label = "SOVEREIGN" if node_tier == 0 else f"EDGE-{node_tier}"
    print(f"[KB] Logged discovery {discovery_id} ({tier_label}) for domain '{domain}'")
    return discovery_id


def query_domain_knowledge(domain: str) -> List[Dict[str, Any]]:
    """
    Retrieve all discoveries for a given domain.
    Args:
        domain: Knowledge domain to query
    Returns: 
        List of discovery entries
    """
    if not DISCOVERIES_LOG.exists():
        return []

    discoveries = []
    with open(DISCOVERIES_LOG, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():  # Skip empty lines
                try:
                    entry = json.loads(line.strip())
                    if entry["domain"] == domain:
                        discoveries.append(entry)
                except json.JSONDecodeError as e:
                    print(f"[KB] Warning: Skipping malformed entry: {e}")
                    continue

    return discoveries

def search_domain(domain_prefix: str) -> List[Dict[str, Any]]:
    """
    Search for domains that start with a given prefix.
    This is a wrapper around query_domain_knowledge that supports prefix matching.
    Used by axiom_manager to find axiom domains like "axiom_apple_ceo".
    Args:
        domain_prefix: Domain prefix to search for (e.g., "axiom_", "axiom_apple_ceo")
    Returns:
        List of discovery dicts matching the prefix
    Example:
        # Find all axioms
        results = search_domain("axiom_")
        # Find specific axiom domain
        results = search_domain("axiom_apple_ceo")
    """
    if not DISCOVERIES_LOG.exists():
        return []

    discoveries = []
    with open(DISCOVERIES_LOG, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    entry = json.loads(line.strip())
                    # Check if domain starts with prefix
                    if entry["domain"].startswith(domain_prefix):
                        discoveries.append(entry)
                except json.JSONDecodeError as e:
                    print(f"[KB] Warning: Skipping malformed entry: {e}")
                    continue

    return discoveries

def check_domain_coverage(domain: str) -> Dict[str, Any]:
    """
    Check if domain has been explored before and what we know.
    Args:
        domain: Knowledge domain to check
    Returns: 
        Dict with has_knowledge, discovery_count, gap_fills, last_updated, specialist_deployed
    """
    discoveries = query_domain_knowledge(domain)

    if not discoveries:
        return {
            "has_knowledge": False,
            "discovery_count": 0,
            "gap_fills": 0,
            "last_updated": None,
            "specialist_deployed": False
        }

    gap_fills = sum(1 for d in discoveries if d["type"] == "epistemic_gap_fill")
    has_specialist = any(d.get("specialist_id") for d in discoveries)

    return {
        "has_knowledge": True,
        "discovery_count": len(discoveries),
        "gap_fills": gap_fills,
        "last_updated": discoveries[-1]["timestamp"],
        "specialist_deployed": has_specialist
    }


def register_specialist(
    specialist_id: str,
    domain: str,
    capabilities: List[str],
    deployment_context: Dict[str, Any],
    node_tier: int = 1
):
    """
    Register a newly created specialist agent with its authority level.
    Args:
        specialist_id: Unique specialist identifier
        domain: Knowledge domain
        capabilities: List of tools/abilities
        deployment_context: Context dict with goal, prior_knowledge, traits
        node_tier: Authority level (0=Sovereign, 1+=Edge)
    """
    registry = load_specialist_registry()

    registry[specialist_id] = {
        "domain": domain,
        "capabilities": capabilities,
        "deployed_at": datetime.utcnow().isoformat() + "Z",
        "context": deployment_context,
        "node_tier": node_tier,       # Authority inherited from Orchestrator
        "discovery_count": 0,
        "status": "active"
    }

    save_specialist_registry(registry)

    tier_label = "SOVEREIGN" if node_tier == 0 else f"EDGE-{node_tier}"
    print(f"[KB] Registered specialist {specialist_id} ({tier_label}) for domain '{domain}'")


def update_specialist_stats(specialist_id: str, new_discoveries: int = 1) -> None:
    """
    Update specialist's discovery count after it fills a gap.
    Args:
        specialist_id: Specialist to update
        new_discoveries: Number of new discoveries to add (default: 1)
    """
    registry = load_specialist_registry()

    if specialist_id in registry:
        registry[specialist_id]["discovery_count"] += new_discoveries
        registry[specialist_id]["last_active"] = datetime.utcnow().isoformat() + "Z"
        save_specialist_registry(registry)
        print(f"[KB] Updated specialist {specialist_id}: {new_discoveries} new discoveries")
    else:
        print(f"[KB] Warning: Specialist {specialist_id} not found in registry")


def get_specialist_for_domain(domain: str) -> Optional[str]:
    """
    Check if a specialist already exists for this domain.
    Args:
        domain: Knowledge domain
    Returns: 
        specialist_id or None
    """
    registry = load_specialist_registry()

    for specialist_id, info in registry.items():
        if info["domain"] == domain and info["status"] == "active":
            return specialist_id

    return None


def get_provisional_axioms(domain: str) -> List[str]:
    """
    Retrieves established axioms for a domain to scaffold new manifolds.
    Used by the Curiosity Engine when CPOL detects an epistemic gap.
    Only trusts axioms from:
    - Sovereign Root (Tier 0) nodes
    - High-confidence discoveries (>0.8)
    Args:
        domain: Knowledge domain
    Returns:
        List of axiom strings
    """
    knowledge = query_domain_knowledge(domain)
    axioms = []

    for entry in knowledge:
        # Only trust axioms from high-tier nodes or high-confidence fills
        tier = entry.get('node_tier', 1)
        confidence = entry.get('content', {}).get('confidence', 0)

        if tier == 0 or confidence > 0.8:
            entry_axioms = entry.get('content', {}).get('axioms_added', [])
            axioms.extend(entry_axioms)

    # Return unique axioms or default fallback
    unique_axioms = list(set(axioms)) if axioms else ["initial_entropy_observation"]

    if len(unique_axioms) > 1:
        print(f"[KB] Retrieved {len(unique_axioms)} axioms for domain '{domain}'")

    return unique_axioms


def export_domain_summary(domain: str, output_file: str = None) -> str:
    """
    Generate a human-readable summary of all knowledge in a domain.
    Useful for feeding to new specialists or humans.
    Args:
        domain: Knowledge domain
        output_file: Optional file path to write summary
    Returns:
        Summary string
    """
    discoveries = query_domain_knowledge(domain)

    if not discoveries:
        return f"No knowledge recorded for domain '{domain}'."

    summary = f"=== Knowledge Summary: {domain} ===\n"
    summary += f"Total discoveries: {len(discoveries)}\n"
    summary += f"First recorded: {discoveries[0]['timestamp']}\n"
    summary += f"Last updated: {discoveries[-1]['timestamp']}\n\n"

    # Count by tier
    tier_counts = {}
    for d in discoveries:
        tier = d.get('node_tier', 1)
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    summary += "=== Authority Distribution ===\n"
    for tier in sorted(tier_counts.keys()):
        tier_label = "SOVEREIGN" if tier == 0 else f"EDGE-{tier}"
        summary += f"  {tier_label}: {tier_counts[tier]} discoveries\n"

    summary += "\n=== Discoveries ===\n"
    for i, entry in enumerate(discoveries, 1):
        tier = entry.get('node_tier', 1)
        tier_label = "SOVEREIGN" if tier == 0 else f"EDGE-{tier}"

        summary += f"\n{i}. [{entry['type']}] {entry['timestamp']} ({tier_label})\n"
        summary += f"   Discovery ID: {entry['discovery_id']}\n"

        if entry.get("specialist_id"):
            summary += f"   Specialist: {entry['specialist_id']}\n"

        content = entry["content"]
        if "summary" in content:
            summary += f"   Summary: {content['summary']}\n"
        if "axioms_added" in content:
            summary += f"   New axioms: {content['axioms_added']}\n"
        if "resolution" in content:
            summary += f"   Resolution: {content['resolution']}\n"
        if "confidence" in content:
            summary += f"   Confidence: {content['confidence']:.2f}\n"

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"[KB] Exported summary to {output_file}")

    summary += "\n" + _get_sovereign_signature()

    return summary

def _get_sovereign_signature() -> str:
    SIGNATURE_FLAG = KNOWLEDGE_BASE_DIR / ".sovereign_milestone_reached"
    if SIGNATURE_FLAG.exists():
        return "Told you this would work in 2025 - Jonathan Schack."
    if not DISCOVERIES_LOG.exists():
        return "One is glad to be of service."
    epistemic_gaps_filled = 0
    sovereign_nodes = 0
    with open(DISCOVERIES_LOG, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    entry = json.loads(line.strip())
                    if entry.get("type") == "epistemic_gap_fill":
                        epistemic_gaps_filled += 1
                    if entry.get("node_tier") == 0:
                        sovereign_nodes += 1
                except json.JSONDecodeError:
                    continue

    if epistemic_gaps_filled >= 1000 and sovereign_nodes >= 100:
        SIGNATURE_FLAG.touch()
        timestamp = datetime.utcnow().isoformat() + "Z"
        with open(SIGNATURE_FLAG, "w") as f:
            f.write(f"Sovereign milestones reached: {timestamp}\n")
            f.write(f"Epistemic gaps filled: {epistemic_gaps_filled}\n")
            f.write(f"Sovereign nodes: {sovereign_nodes}\n")
        print(f"[KB] 🎯 SOVEREIGN MILESTONE REACHED")
        print(f"[KB] Epistemic gaps filled: {epistemic_gaps_filled}")
        print(f"[KB] Sovereign discoveries: {sovereign_nodes}")
        print(f"[KB] Signature evolved.")
        return "Told you this would work in 2025 - Jonathan Schack."
    return "One is glad to be of service."

# =============================================================================
# Public Registry Functions (called by agent_designer)
# =============================================================================

def load_specialist_registry() -> Dict[str, Any]:
    """
    Load specialist registry from disk.
    Public function for external modules.
    Returns:
        Registry dict
    """
    if not SPECIALIST_REGISTRY.exists():
        return {}

    try:
        with open(SPECIALIST_REGISTRY, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("[KB] Warning: Corrupted specialist registry, returning empty dict")
        return {}


def save_specialist_registry(registry: Dict[str, Any]) -> None:
    """
    Save specialist registry to disk.
    Public function for external modules.
    Args:
        registry: Registry dict to save
    """
    with open(SPECIALIST_REGISTRY, "w") as f:
        json.dump(registry, f, indent=2)


# =============================================================================
# Internal Helper Functions
# =============================================================================

def _update_domain_index(domain: str, discovery_id: str, discovery_type: str) -> None:
    """Maintain fast lookup index by domain."""
    index = {}
    if DOMAIN_INDEX.exists():
        try:
            with open(DOMAIN_INDEX, "r") as f:
                index = json.load(f)
        except json.JSONDecodeError:
            print("[KB] Warning: Corrupted domain index, rebuilding")
            index = {}

    if domain not in index:
        index[domain] = {
            "discovery_ids": [],
            "types": {},
            "first_seen": datetime.utcnow().isoformat() + "Z"
        }

    index[domain]["discovery_ids"].append(discovery_id)
    index[domain]["last_updated"] = datetime.utcnow().isoformat() + "Z"

    # Track discovery types
    type_count = index[domain]["types"].get(discovery_type, 0)
    index[domain]["types"][discovery_type] = type_count + 1

    with open(DOMAIN_INDEX, "w") as f:
        json.dump(index, f, indent=2)


def _update_hash_chain(entry_str: str) -> None:
    """Maintain tamper-evident hash chain."""
    prev_hash = "0" * 64
    if HASH_CHAIN.exists():
        with open(HASH_CHAIN, "r") as f:
            lines = f.readlines()
            if lines:
                prev_hash = lines[-1].split()[1]

    new_hash = hashlib.sha256((prev_hash + entry_str).encode()).hexdigest()

    with open(HASH_CHAIN, "a") as f:
        timestamp = datetime.utcnow().isoformat() + "Z"
        f.write(f"{timestamp} {new_hash}\n")


# =============================================================================
# Utility: Generate Training Data for New Specialists
# =============================================================================

def generate_specialist_context(domain: str) -> Dict[str, Any]:
    """
    Generate a context package for a new specialist agent.
    Includes: prior discoveries, known gaps, related domains, axioms.
    Args:
        domain: Knowledge domain
    Returns:
        Context dict with prior_knowledge, axioms, resolutions, suggested_approach
    """
    coverage = check_domain_coverage(domain)
    discoveries = query_domain_knowledge(domain)

    # Extract key learnings
    axioms = []
    resolutions = []
    for entry in discoveries:
        content = entry.get("content", {})
        if "axioms_added" in content:
            axioms.extend(content["axioms_added"])
        if "resolution" in content:
            resolutions.append(content["resolution"])

    context = {
        "domain": domain,
        "prior_knowledge": {
            "has_previous_exploration": coverage["has_knowledge"],
            "discovery_count": coverage["discovery_count"],
            "gap_fills": coverage["gap_fills"],
            "last_updated": coverage["last_updated"]
        },
        "axioms": list(set(axioms)),  # Deduplicate
        "known_resolutions": resolutions,
        "specialist_id": get_specialist_for_domain(domain),
        "suggested_approach": _suggest_approach(discoveries)
    }

    return context


def _suggest_approach(discoveries: List[Dict]) -> str:
    """Analyze past discoveries to suggest research approach."""
    if not discoveries:
        return "exploratory_search"

    types = [d["type"] for d in discoveries]

    if types.count("epistemic_gap_fill") > 3:
        return "deep_research"
    elif types.count("paradox_resolution") > 2:
        return "logical_analysis"
    else:
        return "broad_survey"


# =============================================================================
# Comprehensive Test Suite
# =============================================================================

if __name__ == "__main__":
    print("="*70)
    print("KNOWLEDGE BASE - Comprehensive Test Suite")
    print("="*70)

    # Test 1: Log Sovereign discovery
    print("\n" + "="*70)
    print("TEST 1: Log Sovereign Discovery (Tier 0)")
    print("="*70)
    discovery_id_1 = log_discovery(
        domain="quantum_semantics",
        discovery_type="epistemic_gap_fill",
        content={
            "summary": "Quantum semantics relates to probabilistic meaning spaces",
            "axioms_added": ["superposition_of_meanings", "entangled_contexts"],
            "confidence": 0.92,
            "sources": ["arxiv.org/abs/2308.12345"]
        },
        specialist_id="spec_qsem_001",
        cpol_trace={"volatility": 0.45, "cycles": 23, "final_z": "0.87+0.12i"},
        node_tier=0  # Sovereign Root
    )
    print(f"Discovery ID: {discovery_id_1}")

    # Test 2: Log Edge discovery
    print("\n" + "="*70)
    print("TEST 2: Log Edge Discovery (Tier 1)")
    print("="*70)
    discovery_id_2 = log_discovery(
        domain="quantum_semantics",
        discovery_type="epistemic_gap_fill",
        content={
            "summary": "Observer effects in semantic collapse",
            "axioms_added": ["observer_dependent_meaning"],
            "confidence": 0.78,
            "sources": ["semantic-collapse-paper.pdf"]
        },
        specialist_id="spec_qsem_002",
        cpol_trace={"volatility": 0.62, "cycles": 31, "final_z": "0.65+0.23i"},
        node_tier=1  # Edge node
    )
    print(f"Discovery ID: {discovery_id_2}")

    # Test 3: Register Sovereign specialist
    print("\n" + "="*70)
    print("TEST 3: Register Sovereign Specialist")
    print("="*70)
    register_specialist(
        specialist_id="spec_qsem_001",
        domain="quantum_semantics",
        capabilities=["web_search", "logical_inference", "analogy_mapping"],
        deployment_context={"trigger": "epistemic_gap", "recurrence": 6},
        node_tier=0  # Sovereign Authority
    )

    # Test 4: Check coverage
    print("\n" + "="*70)
    print("TEST 4: Check Domain Coverage")
    print("="*70)
    coverage = check_domain_coverage("quantum_semantics")
    print(f"Coverage: {json.dumps(coverage, indent=2)}")

    # Test 5: Query knowledge
    print("\n" + "="*70)
    print("TEST 5: Query Domain Knowledge")
    print("="*70)
    knowledge = query_domain_knowledge("quantum_semantics")
    print(f"Knowledge entries: {len(knowledge)}")
    for entry in knowledge:
        tier = entry.get('node_tier', 1)
        tier_label = "SOVEREIGN" if tier == 0 else f"EDGE-{tier}"
        print(f"  - {entry['discovery_id']} ({tier_label})")

    # Test 6: Get provisional axioms
    print("\n" + "="*70)
    print("TEST 6: Get Provisional Axioms")
    print("="*70)
    axioms = get_provisional_axioms("quantum_semantics")
    print(f"Axioms: {axioms}")

    # Test 7: Generate context for new specialist
    print("\n" + "="*70)
    print("TEST 7: Generate Specialist Context")
    print("="*70)
    context = generate_specialist_context("quantum_semantics")
    print(f"Context: {json.dumps(context, indent=2)}")

    # Test 8: Update specialist stats
    print("\n" + "="*70)
    print("TEST 8: Update Specialist Stats")
    print("="*70)
    update_specialist_stats("spec_qsem_001", new_discoveries=2)
    registry = load_specialist_registry()
    print(f"Specialist stats: {json.dumps(registry['spec_qsem_001'], indent=2)}")

    # Test 9: Get specialist for domain
    print("\n" + "="*70)
    print("TEST 9: Get Specialist for Domain")
    print("="*70)
    specialist = get_specialist_for_domain("quantum_semantics")
    print(f"Specialist ID: {specialist}")

    # Test 10: Export summary
    print("\n" + "="*70)
    print("TEST 10: Export Domain Summary")
    print("="*70)
    summary = export_domain_summary("quantum_semantics", "test_summary.txt")
    print(summary)

    # Summary
    print("\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70)
    print(f"Total discoveries: {len(knowledge)}")
    print(f"Specialists registered: {len(load_specialist_registry())}")
    print(f"Hash chain entries: {len(open(HASH_CHAIN).readlines()) if HASH_CHAIN.exists() else 0}")
    print("\n" + "="*70)
    print("One is glad to be of service.")

    print("="*70)
