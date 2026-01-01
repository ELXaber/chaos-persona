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
    discovery_type: str,  # "epistemic_gap_fill", "paradox_resolution", "new_axiom"
    content: Dict[str, Any],
    specialist_id: Optional[str] = None,
    cpol_trace: Optional[Dict] = None
) -> str:
    """
    Append a discovery to the knowledge base.
    Returns: discovery_id (hash of entry)
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "domain": domain,
        "type": discovery_type,
        "content": content,
        "specialist_id": specialist_id,
        "cpol_trace": cpol_trace or {},
        "version": "1.0"
    }

    # Generate unique ID
    entry_str = json.dumps(entry, sort_keys=True)
    discovery_id = hashlib.sha256(entry_str.encode()).hexdigest()[:16]
    entry["discovery_id"] = discovery_id

    # Append to log
    with open(DISCOVERIES_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    # Update domain index
    _update_domain_index(domain, discovery_id, discovery_type)

    # Update hash chain for integrity
    _update_hash_chain(entry_str)

    print(f"[KB] Logged discovery {discovery_id} for domain '{domain}'")
    return discovery_id


def query_domain_knowledge(domain: str) -> List[Dict[str, Any]]:
    """
    Retrieve all discoveries for a given domain.
    Returns: List of discovery entries
    """
    if not DISCOVERIES_LOG.exists():
        return []

    discoveries = []
    with open(DISCOVERIES_LOG, "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line.strip())
            if entry["domain"] == domain:
                discoveries.append(entry)

    return discoveries


def check_domain_coverage(domain: str) -> Dict[str, Any]:
    """
    Check if domain has been explored before and what we know.
    Returns: {
        "has_knowledge": bool,
        "discovery_count": int,
        "gap_fills": int,
        "last_updated": str,
        "specialist_deployed": bool
    }
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
    deployment_context: Dict[str, Any]
) -> None:
    """
    Register a newly created specialist agent.
    """
    registry = _load_specialist_registry()
    
    registry[specialist_id] = {
        "domain": domain,
        "capabilities": capabilities,
        "deployed_at": datetime.utcnow().isoformat() + "Z",
        "context": deployment_context,
        "discovery_count": 0,
        "status": "active"
    }

    _save_specialist_registry(registry)
    print(f"[KB] Registered specialist {specialist_id} for domain '{domain}'")


def update_specialist_stats(specialist_id: str, new_discoveries: int = 1) -> None:
    """
    Update specialist's discovery count after it fills a gap.
    """
    registry = _load_specialist_registry()
    
    if specialist_id in registry:
        registry[specialist_id]["discovery_count"] += new_discoveries
        registry[specialist_id]["last_active"] = datetime.utcnow().isoformat() + "Z"
        _save_specialist_registry(registry)


def get_specialist_for_domain(domain: str) -> Optional[str]:
    """
    Check if a specialist already exists for this domain.
    Returns: specialist_id or None
    """
    registry = _load_specialist_registry()

    for specialist_id, info in registry.items():
        if info["domain"] == domain and info["status"] == "active":
            return specialist_id

    return None


def export_domain_summary(domain: str, output_file: str = None) -> str:
    """
    Generate a human-readable summary of all knowledge in a domain.
    Useful for feeding to new specialists or humans.
    """
    discoveries = query_domain_knowledge(domain)

    if not discoveries:
        return f"No knowledge recorded for domain '{domain}'."

    summary = f"=== Knowledge Summary: {domain} ===\n"
    summary += f"Total discoveries: {len(discoveries)}\n"
    summary += f"First recorded: {discoveries[0]['timestamp']}\n"
    summary += f"Last updated: {discoveries[-1]['timestamp']}\n\n"

    summary += "=== Discoveries ===\n"
    for i, entry in enumerate(discoveries, 1):
        summary += f"\n{i}. [{entry['type']}] {entry['timestamp']}\n"
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

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"[KB] Exported summary to {output_file}")

    return summary


# =============================================================================
# Internal Helper Functions
# =============================================================================

def _update_domain_index(domain: str, discovery_id: str, discovery_type: str) -> None:
    """Maintain fast lookup index by domain."""
    index = {}
    if DOMAIN_INDEX.exists():
        with open(DOMAIN_INDEX, "r") as f:
            index = json.load(f)

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


def _load_specialist_registry() -> Dict[str, Any]:
    """Load specialist registry from disk."""
    if not SPECIALIST_REGISTRY.exists():
        return {}

    with open(SPECIALIST_REGISTRY, "r") as f:
        return json.load(f)


def _save_specialist_registry(registry: Dict[str, Any]) -> None:
    """Save specialist registry to disk."""
    with open(SPECIALIST_REGISTRY, "w") as f:
        json.dump(registry, f, indent=2)


# =============================================================================
# Utility: Generate Training Data for New Specialists
# =============================================================================

def generate_specialist_context(domain: str) -> Dict[str, Any]:
    """
    Generate a context package for a new specialist agent.
    Includes: prior discoveries, known gaps, related domains.
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
# Test
# =============================================================================

if __name__ == "__main__":
    print("=== Knowledge Base Test ===\n")
    
    # Test 1: Log a discovery
    discovery_id = log_discovery(
        domain="quantum_semantics",
        discovery_type="epistemic_gap_fill",
        content={
            "summary": "Quantum semantics relates to probabilistic meaning spaces",
            "axioms_added": ["superposition_of_meanings", "entangled_contexts"],
            "confidence": 0.82
        },
        specialist_id="spec_qsem_001",
        cpol_trace={"volatility": 0.45, "cycles": 23}
    )

    # Test 2: Register specialist
    register_specialist(
        specialist_id="spec_qsem_001",
        domain="quantum_semantics",
        capabilities=["web_search", "logical_inference", "analogy_mapping"],
        deployment_context={"trigger": "epistemic_gap", "recurrence": 6}
    )

    # Test 3: Check coverage
    coverage = check_domain_coverage("quantum_semantics")
    print(f"\nDomain coverage: {coverage}")

    # Test 4: Query knowledge
    knowledge = query_domain_knowledge("quantum_semantics")
    print(f"\nKnowledge entries: {len(knowledge)}")

    # Test 5: Generate context for new specialist
    context = generate_specialist_context("quantum_semantics")
    print(f"\nSpecialist context: {json.dumps(context, indent=2)}")

    # Test 6: Export summary
    summary = export_domain_summary("quantum_semantics", "test_summary.txt")
    print(f"\n{summary}")