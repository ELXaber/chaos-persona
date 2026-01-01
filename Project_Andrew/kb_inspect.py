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
        print(f"Specialist ID: {specialist_id}")

    print(f"\n{'Discoveries':-^70}")
    discoveries = kb.query_domain_knowledge(domain)

    for i, disc in enumerate(discoveries, 1):
        print(f"\n{i}. [{disc['type']}] {disc['timestamp'][:19]}")
        print(f"   ID: {disc['discovery_id']}")

        content = disc.get('content', {})
        if 'summary' in content:
            summary = content['summary'][:80]
            print(f"   Summary: {summary}")

        if 'axioms_added' in content:
            axioms = content['axioms_added']
            print(f"   Axioms: {', '.join(axioms)}")

        if 'confidence' in content:
            print(f"   Confidence: {content['confidence']:.2f}")


def cmd_list_specialists():
    """List all registered specialists."""
    if not kb.SPECIALIST_REGISTRY.exists():
        print("No specialists registered.")
        return

    with open(kb.SPECIALIST_REGISTRY, "r") as f:
        registry = json.load(f)

    if not registry:
        print("No specialists registered.")
        return

    print(f"{'='*90}")
    print(f"{'SPECIALIST ID':<20} {'DOMAIN':<25} {'DISCOVERIES':<15} {'STATUS':<10} {'DEPLOYED':<20}")
    print(f"{'='*90}")

    for spec_id, info in registry.items():
        domain = info['domain']
        disc_count = info.get('discovery_count', 0)
        status = info.get('status', 'unknown')
        deployed = info.get('deployed_at', 'Unknown')[:19]

        print(f"{spec_id:<20} {domain:<25} {disc_count:<15} {status:<10} {deployed:<20}")

    print(f"{'='*90}")
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

    with open(kb.SPECIALIST_REGISTRY, "r") as f:
        registry = json.load(f)

    if specialist_id not in registry:
        print(f"Specialist '{specialist_id}' not found.")
        return

    info = registry[specialist_id]

    print(f"\n{'='*70}")
    print(f"Specialist: {specialist_id}")
    print(f"{'='*70}")
    print(f"Domain: {info['domain']}")
    print(f"Status: {info.get('status', 'unknown')}")
    print(f"Deployed: {info.get('deployed_at', 'Unknown')}")
    print(f"Discoveries: {info.get('discovery_count', 0)}")
    print(f"Last active: {info.get('last_active', 'Never')}")
    print(f"\nCapabilities: {', '.join(info.get('capabilities', []))}")

    print(f"\n{'Deployment Context':-^70}")
    context = info.get('context', {})
    print(json.dumps(context, indent=2))


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
            discovery_count = sum(1 for _ in f)

    # Count specialists
    specialist_count = 0
    if kb.SPECIALIST_REGISTRY.exists():
        with open(kb.SPECIALIST_REGISTRY, "r") as f:
            specialist_count = len(json.load(f))

    # Hash chain integrity
    hash_count = 0
    if kb.HASH_CHAIN.exists():
        with open(kb.HASH_CHAIN, "r") as f:
            hash_count = sum(1 for _ in f)

    print(f"\nTotal domains: {domain_count}")
    print(f"Total discoveries: {discovery_count}")
    print(f"Active specialists: {specialist_count}")
    print(f"Hash chain entries: {hash_count}")

    print(f"\n{'Storage':-^70}")
    kb_size = sum(f.stat().st_size for f in kb.KNOWLEDGE_BASE_DIR.glob("*") if f.is_file())
    print(f"Knowledge base size: {kb_size / 1024:.2f} KB")

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
            entry = json.loads(line.strip())

            # Search in domain, type, and content
            searchable = f"{entry['domain']} {entry['type']} {json.dumps(entry['content'])}".lower()

            if query_lower in searchable:
                matches.append(entry)

    if not matches:
        print(f"No matches found for '{query}'")
        return

    print(f"\n{'='*70}")
    print(f"Found {len(matches)} match(es) for '{query}'")
    print(f"{'='*70}")

    for i, entry in enumerate(matches, 1):
        print(f"\n{i}. [{entry['type']}] {entry['domain']}")
        print(f"   Timestamp: {entry['timestamp'][:19]}")
        print(f"   Discovery ID: {entry['discovery_id']}")

        content = entry.get('content', {})
        if 'summary' in content:
            print(f"   Summary: {content['summary'][:100]}")


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
    help                   - Show this help message

EXAMPLES:
    python kb_inspect.py list
    python kb_inspect.py show quantum_semantics
    python kb_inspect.py export quantum_semantics report.txt
    python kb_inspect.py specialists
    python kb_inspect.py stats
    python kb_inspect.py search "blockchain"
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
        'help': lambda: cmd_help()
    }

    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print("Run 'python kb_inspect.py help' for usage information.")


if __name__ == "__main__":
    main()