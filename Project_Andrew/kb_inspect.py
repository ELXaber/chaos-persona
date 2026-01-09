#!/usr/bin/env python3
# =============================================================================
# Knowledge Base Inspector - CLI Tool
# Usage: python kb_inspect.py [command] [args]
# =============================================================================

import sys
import json
from pathlib import Path
import knowledge_base as kb
from datetime import datetime

def cmd_list_domains():
    """List all domains in the knowledge base."""
    if not kb.DOMAIN_INDEX.exists():
        print("No domains found. Knowledge base is empty.")
        return

    with open(kb.DOMAIN_INDEX, "r") as f:
        index = json.load(f)

    print(f"{'='*70}")
    print(f"{'DOMAIN':<30} {'DISCOVERIES':<15} {'LAST UPDATED':<25}")
    print(f"{'='*70}")

    for domain, info in sorted(index.items()):
        disc_count = len(info['discovery_ids'])
        last_updated = info.get('last_updated', 'Unknown')[:19]
        print(f"{domain:<30} {disc_count:<15} {last_updated:<25}")

    print(f"{'='*70}")
    print(f"Total domains: {len(index)}")


def cmd_show_domain(domain: str):
    """Show detailed information for a specific domain."""
    coverage = kb.check_domain_coverage(domain)

    if not coverage["has_knowledge"]:
        print(f"No knowledge found for domain '{domain}'")
        return

    print(f"\n{'='*70}")
    print(f"Domain: {domain}")
    print(f"{'='*70}")
    print(f"Total discoveries: {coverage['discovery_count']}")
    print(f"Gap fills: {coverage['gap_fills']}")
    print(f"Last updated: {coverage['last_updated']}")
    print(f"Has specialist: {coverage['specialist_deployed']}")

    specialist_id = kb.get_specialist_for_domain(domain)
    if specialist_id:
        registry = kb.load_specialist_registry()
        spec_info = registry.get(specialist_id, {})
        spec_tier = spec_info.get('node_tier', 1)
        tier_label = "SOVEREIGN" if spec_tier == 0 else f"EDGE-{spec_tier}"
        print(f"Specialist ID: {specialist_id} ({tier_label})")

    # Get axioms for this domain
    axioms = kb.get_provisional_axioms(domain)
    if axioms and axioms != ["initial_entropy_observation"]:
        print(f"\n{'Established Axioms':-^70}")
        for axiom in axioms:
            print(f"  • {axiom}")

    print(f"\n{'Discoveries':-^70}")
    discoveries = kb.query_domain_knowledge(domain)

    for i, disc in enumerate(discoveries, 1):
        # Determine the Sovereign Label based on node_tier
        tier = disc.get('node_tier', 1)
        tier_label = "SOVEREIGN" if tier == 0 else f"EDGE-{tier}"

        # Get confidence if available
        confidence = disc.get('content', {}).get('confidence', 0)
        conf_str = f" | Conf: {confidence:.2f}" if confidence > 0 else ""

        print(f"\n{i}. [{disc['type']}] {disc['timestamp'][:19]} | {tier_label}{conf_str}")
        print(f"   ID: {disc['discovery_id']}")

        # Show the Manifold Signature if present
        if 'manifold_sig' in disc and disc['manifold_sig'] != "0xUNVERIFIED":
            sig = disc['manifold_sig']
            # Handle complex number format
            if isinstance(sig, str) and ('+' in sig or '-' in sig[-5:]):
                print(f"   Manifold Sig: {sig[:20]}...")
            else:
                print(f"   Manifold Sig: {sig[:15]}...")

        content = disc.get('content', {})
        if 'summary' in content:
            summary = content['summary'][:80]
            print(f"   Summary: {summary}")

        if 'axioms_added' in content:
            axioms = content['axioms_added']
            print(f"   Axioms: {', '.join(axioms)}")

        if 'sources' in content:
            sources = content['sources']
            if sources:
                print(f"   Sources: {sources[0]}" + (f" (+{len(sources)-1} more)" if len(sources) > 1 else ""))


def cmd_list_specialists():
    """List all registered specialists."""
    if not kb.SPECIALIST_REGISTRY.exists():
        print("No specialists registered.")
        return

    registry = kb.load_specialist_registry()

    if not registry:
        print("No specialists registered.")
        return

    print(f"{'='*100}")
    print(f"{'SPECIALIST ID':<20} {'DOMAIN':<25} {'TIER':<12} {'DISCOVERIES':<12} {'STATUS':<10} {'DEPLOYED':<20}")
    print(f"{'='*100}")

    for spec_id, info in sorted(registry.items()):
        domain = info['domain']
        disc_count = info.get('discovery_count', 0)
        status = info.get('status', 'unknown')
        deployed = info.get('deployed_at', 'Unknown')[:19]
        tier = info.get('node_tier', 1)
        tier_label = "SOVEREIGN" if tier == 0 else f"EDGE-{tier}"

        print(f"{spec_id:<20} {domain:<25} {tier_label:<12} {disc_count:<12} {status:<10} {deployed:<20}")

    print(f"{'='*100}")
    print(f"Total specialists: {len(registry)}")


def cmd_export_domain(domain: str, output_file: str = None):
    """Export domain summary to file."""
    if not output_file:
        output_file = f"knowledge_export_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    summary = kb.export_domain_summary(domain, output_file)
    print(summary)


def cmd_show_specialist(specialist_id: str):
    """Show details for a specific specialist."""
    if not kb.SPECIALIST_REGISTRY.exists():
        print("No specialists registered.")
        return

    registry = kb.load_specialist_registry()

    if specialist_id not in registry:
        print(f"Specialist '{specialist_id}' not found.")
        return

    info = registry[specialist_id]

    # Determine authority for THIS specialist
    tier = info.get('node_tier', 1)
    tier_label = "SOVEREIGN ROOT (Tier 0)" if tier == 0 else f"EDGE (Tier {tier})"

    print(f"\n{'='*70}")
    print(f"Specialist: {specialist_id}")
    print(f"Authority: {tier_label}")
    print(f"{'='*70}")
    print(f"Domain: {info['domain']}")
    print(f"Status: {info.get('status', 'unknown')}")
    print(f"Deployed: {info.get('deployed_at', 'Unknown')}")
    print(f"Discoveries: {info.get('discovery_count', 0)}")
    print(f"Last active: {info.get('last_active', 'Never')}")
    print(f"\nCapabilities: {', '.join(info.get('capabilities', []))}")

    # Show deployment context
    print(f"\n{'Deployment Context':-^70}")
    context = info.get('deployment_context', {})

    # Pretty print context
    if 'goal' in context:
        print(f"Goal: {context['goal']}")
    if 'traits' in context:
        print(f"Traits: {json.dumps(context['traits'], indent=2)}")
    if 'prior_knowledge' in context:
        pk = context['prior_knowledge']
        print(f"\nPrior Knowledge:")
        print(f"  Axioms: {len(pk.get('axioms', []))}")
        print(f"  Discovery count: {pk.get('prior_knowledge', {}).get('discovery_count', 0)}")

    # Show discoveries made by this specialist
    print(f"\n{'Discoveries by this Specialist':-^70}")
    discoveries = kb.query_domain_knowledge(info['domain'])
    specialist_discoveries = [d for d in discoveries if d.get('specialist_id') == specialist_id]

    if specialist_discoveries:
        for i, disc in enumerate(specialist_discoveries, 1):
            tier_disc = disc.get('node_tier', 1)
            tier_label_disc = "SOVEREIGN" if tier_disc == 0 else f"EDGE-{tier_disc}"
            print(f"\n{i}. [{disc['type']}] {disc['timestamp'][:19]} | {tier_label_disc}")
            print(f"   ID: {disc['discovery_id']}")
            content = disc.get('content', {})
            if 'summary' in content:
                print(f"   Summary: {content['summary'][:60]}...")
    else:
        print("  No discoveries yet")


def cmd_stats():
    """Show overall knowledge base statistics."""
    print(f"\n{'='*70}")
    print(f"{'CAIOS Knowledge Base Statistics':^70}")
    print(f"{'='*70}")

    # Count domains
    domain_count = 0
    if kb.DOMAIN_INDEX.exists():
        with open(kb.DOMAIN_INDEX, "r") as f:
            domain_count = len(json.load(f))

    # Count discoveries
    discovery_count = 0
    if kb.DISCOVERIES_LOG.exists():
        with open(kb.DISCOVERIES_LOG, "r") as f:
            discovery_count = sum(1 for line in f if line.strip())

    # Count specialists
    specialist_count = 0
    sovereign_specialists = 0
    edge_specialists = 0
    if kb.SPECIALIST_REGISTRY.exists():
        registry = kb.load_specialist_registry()
        specialist_count = len(registry)
        for spec_info in registry.values():
            if spec_info.get('node_tier', 1) == 0:
                sovereign_specialists += 1
            else:
                edge_specialists += 1

    # Hash chain integrity
    hash_count = 0
    if kb.HASH_CHAIN.exists():
        with open(kb.HASH_CHAIN, "r") as f:
            hash_count = sum(1 for _ in f)

    # Sovereign vs Edge distribution audit
    sovereign_count = 0
    edge_count = 0
    tier_distribution = {}

    if kb.DISCOVERIES_LOG.exists():
        with open(kb.DISCOVERIES_LOG, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line.strip())
                    tier = entry.get('node_tier', 1)
                    tier_distribution[tier] = tier_distribution.get(tier, 0) + 1

                    if tier == 0:
                        sovereign_count += 1
                    else:
                        edge_count += 1
                except json.JSONDecodeError:
                    continue

    # Display authority distribution
    print(f"\n{'Authority Distribution':-^70}")
    print(f"Sovereign Truths (Tier 0):  {sovereign_count} discoveries | {sovereign_specialists} specialists")
    print(f"Edge Discoveries (Tier 1+): {edge_count} discoveries | {edge_specialists} specialists")

    if tier_distribution:
        print(f"\n{'Detailed Tier Breakdown':-^70}")
        for tier in sorted(tier_distribution.keys()):
            tier_label = "SOVEREIGN" if tier == 0 else f"EDGE-{tier}"
            print(f"  {tier_label}: {tier_distribution[tier]} discoveries")

    # Overall stats
    print(f"\n{'Overall Statistics':-^70}")
    print(f"Total domains: {domain_count}")
    print(f"Total discoveries: {discovery_count}")
    print(f"Active specialists: {specialist_count}")
    print(f"Hash chain entries: {hash_count}")

    # Calculate integrity ratio
    if discovery_count > 0:
        integrity_ratio = hash_count / discovery_count
        print(f"Chain integrity: {integrity_ratio:.2%}")

    # Storage info
    print(f"\n{'Storage':-^70}")
    if kb.KNOWLEDGE_BASE_DIR.exists():
        kb_size = sum(f.stat().st_size for f in kb.KNOWLEDGE_BASE_DIR.glob("*") if f.is_file())
        print(f"Knowledge base size: {kb_size / 1024:.2f} KB")
        print(f"Average discovery size: {kb_size / max(discovery_count, 1):.2f} bytes")

    print(f"{'='*70}")


def cmd_search(query: str):
    """Search for discoveries matching a query."""
    if not kb.DISCOVERIES_LOG.exists():
        print("No discoveries to search.")
        return

    matches = []
    query_lower = query.lower()

    with open(kb.DISCOVERIES_LOG, "r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line.strip())

                # Search in domain, type, and content
                searchable = f"{entry['domain']} {entry['type']} {json.dumps(entry['content'])}".lower()

                if query_lower in searchable:
                    matches.append(entry)
            except json.JSONDecodeError:
                continue

    if not matches:
        print(f"No matches found for '{query}'")
        return

    print(f"\n{'='*70}")
    print(f"Found {len(matches)} match(es) for '{query}'")
    print(f"{'='*70}")

    for i, entry in enumerate(matches, 1):
        tier = entry.get('node_tier', 1)
        tier_label = "SOVEREIGN" if tier == 0 else f"EDGE-{tier}"

        print(f"\n{i}. [{entry['type']}] {entry['domain']} | {tier_label}")
        print(f"   Timestamp: {entry['timestamp'][:19]}")
        print(f"   Discovery ID: {entry['discovery_id']}")

        content = entry.get('content', {})
        if 'summary' in content:
            print(f"   Summary: {content['summary'][:100]}")
        if 'confidence' in content:
            print(f"   Confidence: {content['confidence']:.2f}")


def cmd_verify_integrity():
    """Verify hash chain integrity."""
    if not kb.HASH_CHAIN.exists():
        print("No hash chain found.")
        return

    print(f"\n{'='*70}")
    print(f"Verifying Hash Chain Integrity...")
    print(f"{'='*70}")

    with open(kb.HASH_CHAIN, "r") as f:
        entries = f.readlines()

    if not entries:
        print("Hash chain is empty.")
        return

    print(f"Total chain entries: {len(entries)}")

    # Verify first entry
    first_entry = entries[0].split()
    if len(first_entry) < 2:
        print("❌ Malformed first entry")
        return

    print(f"✓ Genesis hash: {first_entry[1][:16]}...")

    # Verify chain continuity (spot check every 10th entry)
    errors = 0
    for i in range(1, len(entries), max(1, len(entries) // 10)):
        curr_parts = entries[i].split()
        prev_parts = entries[i-1].split()

        if len(curr_parts) < 2 or len(prev_parts) < 2:
            print(f"❌ Malformed entry at position {i}")
            errors += 1

    if errors == 0:
        print(f"✓ Chain continuity verified")
        print(f"✓ Integrity: INTACT")
    else:
        print(f"❌ Found {errors} errors")
        print(f"❌ Integrity: COMPROMISED")

    print(f"{'='*70}")


def cmd_axioms(domain: str = None):
    """Show axioms for a domain or all domains."""
    if domain:
        # Show axioms for specific domain
        axioms = kb.get_provisional_axioms(domain)

        print(f"\n{'='*70}")
        print(f"Axioms for domain: {domain}")
        print(f"{'='*70}")

        if axioms == ["initial_entropy_observation"]:
            print("No established axioms yet (default fallback active)")
        else:
            for i, axiom in enumerate(axioms, 1):
                print(f"{i}. {axiom}")
    else:
        # Show all domains with their axioms
        if not kb.DOMAIN_INDEX.exists():
            print("No domains found.")
            return

        with open(kb.DOMAIN_INDEX, "r") as f:
            index = json.load(f)

        print(f"\n{'='*70}")
        print(f"{'Axioms by Domain':^70}")
        print(f"{'='*70}")

        for domain_name in sorted(index.keys()):
            axioms = kb.get_provisional_axioms(domain_name)
            if axioms != ["initial_entropy_observation"]:
                print(f"\n{domain_name}:")
                for axiom in axioms:
                    print(f"  • {axiom}")


def cmd_help():
    """Show help message."""
    print("""
CAIOS Knowledge Base Inspector

USAGE:
    python kb_inspect.py [command] [args]

COMMANDS:
    list                    - List all domains
    show <domain>          - Show details for a domain
    export <domain> [file] - Export domain summary to file
    specialists            - List all specialists
    specialist <id>        - Show specialist details
    stats                  - Show knowledge base statistics
    search <query>         - Search discoveries
    verify                 - Verify hash chain integrity
    axioms [domain]        - Show axioms (all or specific domain)
    help                   - Show this help message

EXAMPLES:
    python kb_inspect.py list
    python kb_inspect.py show quantum_semantics
    python kb_inspect.py export quantum_semantics report.txt
    python kb_inspect.py specialists
    python kb_inspect.py specialist spec_qsem_001
    python kb_inspect.py stats
    python kb_inspect.py search "blockchain"
    python kb_inspect.py verify
    python kb_inspect.py axioms quantum_semantics
    python kb_inspect.py axioms

TIER LABELS:
    SOVEREIGN   - Tier 0 (Sovereign Root authority)
    EDGE-N      - Tier N (Edge node, N ≥ 1)
    """)


def main():
    if len(sys.argv) < 2:
        cmd_help()
        return

    command = sys.argv[1].lower()

    commands = {
        'list': lambda: cmd_list_domains(),
        'show': lambda: cmd_show_domain(sys.argv[2]) if len(sys.argv) > 2 else print("Usage: show <domain>"),
        'export': lambda: cmd_export_domain(
            sys.argv[2],
            sys.argv[3] if len(sys.argv) > 3 else None
        ) if len(sys.argv) > 2 else print("Usage: export <domain> [file]"),
        'specialists': lambda: cmd_list_specialists(),
        'specialist': lambda: cmd_show_specialist(sys.argv[2]) if len(sys.argv) > 2 else print("Usage: specialist <id>"),
        'stats': lambda: cmd_stats(),
        'search': lambda: cmd_search(' '.join(sys.argv[2:])) if len(sys.argv) > 2 else print("Usage: search <query>"),
        'verify': lambda: cmd_verify_integrity(),
        'axioms': lambda: cmd_axioms(sys.argv[2] if len(sys.argv) > 2 else None),
        'help': lambda: cmd_help()
    }

    if command in commands:
        try:
            commands[command]()
        except Exception as e:
            print(f"Error executing command '{command}': {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"Unknown command: {command}")
        print("Run 'python kb_inspect.py help' for usage information.")


if __name__ == "__main__":
    main()