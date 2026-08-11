#V06082026
#!/usr/bin/env python3
# =============================================================================
# kb_cleanup.py — CAIOS Knowledge Base Cleanup & Validation Tool
#
# Three levels (as Andrew described):
#   1. Automated integrity sweep — detects and quarantines malformed entries
#   2. Authority-tier purge commands — targeted removal by pattern or ID
#   3. Entropy-based flagging — marks axioms whose content looks like noise
#
# Usage:
#   python kb_cleanup.py sweep          # scan and report problems
#   python kb_cleanup.py sweep --fix    # scan and quarantine bad entries
#   python kb_cleanup.py purge <id>     # remove entry by discovery_id
#   python kb_cleanup.py purge --pattern "yay_progress"  # remove by domain pattern
#   python kb_cleanup.py validate       # full validation report
#   python kb_cleanup.py list-bad       # list flagged entries without removing
# =============================================================================

import sys
import json
import re
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

KB_DIR          = Path('knowledge_base')
DISCOVERIES     = KB_DIR / 'discoveries.jsonl'
DOMAIN_INDEX    = KB_DIR / 'domain_index.json'
SPECIALIST_REG  = KB_DIR / 'specialist_registry.json'
QUARANTINE      = KB_DIR / 'quarantine.jsonl'
HASH_CHAIN      = KB_DIR / 'integrity_chain.txt'

# ── Noise detection patterns ──────────────────────────────────
# Domain keys that look like garbage from a misfire
NOISE_DOMAIN_PATTERNS = [
    r'^axiom_[a-z]+,_',           # starts with word then comma-underscore
    r'_\.\s',                      # underscore-dot-space in domain key
    r'_\?',                        # question mark in domain key
    r'_!',                         # exclamation in domain key
    r"axiom_i'll_",                # conversational filler
    r'axiom_okay',                 # conversational filler
    r'axiom_ahh',                  # conversational filler
    r'axiom_yay',                  # conversational filler
    r'axiom_so_the_',              # sentence fragment
    r'axiom_it_looks_like',        # sentence fragment
    r'axiom_when_',                # sentence fragment
    r'axiom_the_parse',            # describing parser
    r'(?:http|https)://',          # URL in domain key
    r'\s{2,}',                     # multiple spaces
]

# Summary facts that look like noise
NOISE_FACT_PATTERNS = [
    r'^functional\.',              # bare "functional."
    r'^no need to trigger',        # fragment
    r'^\[.*\]$',                   # bare tag
    r'parse_update_command',       # parser explanation
    r'#UPDATE.*anywhere',          # meta-discussion
]

# ── Load/save helpers ─────────────────────────────────────────

def load_entries() -> List[Dict]:
    if not DISCOVERIES.exists():
        return []
    entries = []
    with open(DISCOVERIES, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  [WARN] Line {i+1} malformed JSON: {e}")
    return entries


def save_entries(entries: List[Dict]) -> None:
    """Rewrite discoveries.jsonl from a list (after purge/quarantine)."""
    backup = DISCOVERIES.with_suffix('.jsonl.bak')
    if DISCOVERIES.exists():
        shutil.copy2(str(DISCOVERIES), str(backup))
    with open(DISCOVERIES, 'w', encoding='utf-8') as f:
        for e in entries:
            f.write(json.dumps(e) + '\n')
    print(f"  Backup saved: {backup.name}")


def load_domain_index() -> Dict:
    if not DOMAIN_INDEX.exists():
        return {}
    with open(DOMAIN_INDEX, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_domain_index(index: Dict) -> None:
    with open(DOMAIN_INDEX, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)


def append_quarantine(entry: Dict, reason: str) -> None:
    QB_DIR = KB_DIR
    QB_DIR.mkdir(exist_ok=True)
    record = {
        'quarantined_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z',
        'reason': reason,
        'original': entry
    }
    with open(QUARANTINE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')


# ── Detection logic ───────────────────────────────────────────

def is_noise_domain(domain: str) -> Tuple[bool, str]:
    """Return (is_noise, reason)."""
    for pat in NOISE_DOMAIN_PATTERNS:
        if re.search(pat, domain, re.IGNORECASE):
            return True, f"domain matches noise pattern: {pat}"
    # Domain key too long (> 80 chars suggests a sentence, not a key)
    if len(domain) > 80:
        return True, f"domain key too long ({len(domain)} chars)"
    # Domain contains spaces (axiom domains should be snake_case)
    if ' ' in domain.replace('axiom_', ''):
        return True, "domain key contains spaces"
    return False, ''


def is_noise_fact(fact: str) -> Tuple[bool, str]:
    """Return (is_noise, reason)."""
    for pat in NOISE_FACT_PATTERNS:
        if re.search(pat, fact, re.IGNORECASE):
            return True, f"fact matches noise pattern: {pat}"
    return False, ''


def check_entry(entry: Dict) -> List[str]:
    """Return list of problems found in entry. Empty = clean."""
    problems = []
    domain = entry.get('domain', '')
    content = entry.get('content', {})
    summary = content.get('summary', '')

    # Check domain
    bad_domain, reason = is_noise_domain(domain)
    if bad_domain:
        problems.append(f"bad domain: {reason}")

    # Check axiom fact content
    if entry.get('type') == 'temporal_axiom':
        axiom_data = content.get('axiom_data', {})
        fact = axiom_data.get('fact', summary)
        bad_fact, reason = is_noise_fact(fact)
        if bad_fact:
            problems.append(f"bad fact: {reason}")

    # Check for missing required fields
    for field in ('timestamp', 'domain', 'type', 'discovery_id'):
        if not entry.get(field):
            problems.append(f"missing field: {field}")

    return problems


# ── Commands ──────────────────────────────────────────────────

def cmd_sweep(fix: bool = False) -> int:
    """Scan all entries for problems. If fix=True, quarantine bad ones."""
    entries = load_entries()
    index = load_domain_index()

    print(f"\nScanning {len(entries)} entries...")
    print('─' * 72)

    bad_ids = set()
    bad_domains = set()
    clean = 0

    for entry in entries:
        problems = check_entry(entry)
        did = entry.get('discovery_id', '?')
        domain = entry.get('domain', '?')

        if problems:
            print(f"\n  [BAD]  {did}")
            print(f"         domain: {domain[:60]}")
            for p in problems:
                print(f"         problem: {p}")
            if fix:
                append_quarantine(entry, '; '.join(problems))
                bad_ids.add(did)
                bad_domains.add(domain)
                print(f"         → quarantined")
        else:
            clean += 1

    print('─' * 72)
    print(f"\n{clean} clean, {len(bad_ids)} flagged.")

    if fix and bad_ids:
        # Remove bad entries from discoveries
        kept = [e for e in entries if e.get('discovery_id') not in bad_ids]
        save_entries(kept)

        # Remove bad domains from index
        for domain in bad_domains:
            if domain in index:
                del index[domain]
        save_domain_index(index)

        print(f"Quarantined {len(bad_ids)} entries → {QUARANTINE.name}")
        print("Cleaned domain index.")
        return 1

    if not fix and bad_ids:
        print("\nRun with --fix to quarantine bad entries.")

    return 0


def cmd_purge(target: str, by_pattern: bool = False) -> int:
    """Remove entry by discovery_id or domain pattern."""
    entries = load_entries()
    index = load_domain_index()
    original_count = len(entries)

    if by_pattern:
        pat = re.compile(target, re.IGNORECASE)
        to_remove = [e for e in entries if pat.search(e.get('domain', ''))]
    else:
        to_remove = [e for e in entries if e.get('discovery_id') == target]

    if not to_remove:
        print(f"\nNo entries found matching: {target}")
        return 0

    print(f"\nEntries to remove ({len(to_remove)}):")
    for e in to_remove:
        print(f"  {e.get('discovery_id')} | {e.get('domain')} | {e.get('type')}")

    confirm = input("\nConfirm removal? (yes/no): ").strip().lower()
    if confirm not in ('yes', 'y'):
        print("Cancelled.")
        return 0

    # Quarantine before removing
    for e in to_remove:
        append_quarantine(e, f"manual purge: {target}")

    # Remove from entries
    remove_ids = {e.get('discovery_id') for e in to_remove}
    remove_domains = {e.get('domain') for e in to_remove}
    kept = [e for e in entries if e.get('discovery_id') not in remove_ids]
    save_entries(kept)

    # Clean domain index
    for domain in remove_domains:
        if domain in index:
            del index[domain]
    save_domain_index(index)

    print(f"\nRemoved {original_count - len(kept)} entries.")
    print(f"Backed up to {QUARANTINE.name}")
    return 1


def cmd_validate() -> int:
    """Full validation report."""
    entries = load_entries()
    index = load_domain_index()

    print(f"\n{'='*72}")
    print(f"  CAIOS KB Validation Report")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*72}")

    # Entry stats
    types = {}
    tiers = {}
    for e in entries:
        t = e.get('type', 'unknown')
        tier = e.get('node_tier', 1)
        types[t] = types.get(t, 0) + 1
        tiers[tier] = tiers.get(tier, 0) + 1

    print(f"\nTotal entries: {len(entries)}")
    print(f"By type:")
    for t, count in sorted(types.items()):
        print(f"  {t:<30} {count}")
    print(f"By tier:")
    for tier in sorted(tiers):
        label = "SOVEREIGN" if tier == 0 else f"EDGE-{tier}"
        print(f"  {label:<30} {tiers[tier]}")

    # Domain index cross-check
    indexed_ids = set()
    for domain_info in index.values():
        indexed_ids.update(domain_info.get('discovery_ids', []))
    entry_ids = {e.get('discovery_id') for e in entries}

    orphaned_index = indexed_ids - entry_ids
    unindexed_entries = entry_ids - indexed_ids

    print(f"\nDomain index: {len(index)} domains")
    if orphaned_index:
        print(f"  [WARN] {len(orphaned_index)} IDs in index but not in discoveries:")
        for oid in list(orphaned_index)[:5]:
            print(f"    {oid}")
    if unindexed_entries:
        print(f"  [WARN] {len(unindexed_entries)} entries not in domain index")

    # Noise check
    print(f"\nNoise scan:")
    noise_count = 0
    for entry in entries:
        problems = check_entry(entry)
        if problems:
            noise_count += 1
            did = entry.get('discovery_id', '?')[:16]
            domain = entry.get('domain', '?')[:50]
            print(f"  [FLAG] {did} — {domain}")
            for p in problems:
                print(f"         {p}")

    if noise_count == 0:
        print("  All entries pass noise check.")

    # Hash chain check
    if HASH_CHAIN.exists():
        with open(HASH_CHAIN, 'r', encoding='utf-8') as f:
            chain_lines = [l.strip() for l in f if l.strip()]
        print(f"\nHash chain: {len(chain_lines)} entries")
        if len(chain_lines) != len(entries):
            print(f"  [WARN] Chain length ({len(chain_lines)}) != discoveries ({len(entries)})")
    else:
        print(f"\nHash chain: not found")

    print(f"\n{'='*72}")
    return 0


def cmd_list_bad() -> int:
    """List flagged entries without removing anything."""
    entries = load_entries()
    found = 0
    for entry in entries:
        problems = check_entry(entry)
        if problems:
            found += 1
            print(f"\n  {entry.get('discovery_id', '?')}")
            print(f"  domain: {entry.get('domain', '?')[:70]}")
            print(f"  type:   {entry.get('type', '?')}")
            content = entry.get('content', {})
            axiom_data = content.get('axiom_data', {})
            if axiom_data:
                print(f"  fact:   {axiom_data.get('fact', '')[:70]}")
            for p in problems:
                print(f"  ⚠  {p}")
    if found == 0:
        print("\nNo flagged entries found.")
    else:
        print(f"\n{found} flagged entries. Run 'python kb_cleanup.py sweep --fix' to quarantine.")
    return 0


# ── CLI ───────────────────────────────────────────────────────

def usage():
    print("""
CAIOS KB Cleanup Tool

Usage:
  python kb_cleanup.py sweep              Scan for bad entries (report only)
  python kb_cleanup.py sweep --fix        Scan and quarantine bad entries
  python kb_cleanup.py purge <id>         Remove entry by discovery_id
  python kb_cleanup.py purge --pattern X  Remove entries matching domain pattern
  python kb_cleanup.py validate           Full validation report
  python kb_cleanup.py list-bad           List flagged entries without changes

Examples:
  python kb_cleanup.py purge 8e9118581890b09d
  python kb_cleanup.py purge --pattern "yay_progress"
  python kb_cleanup.py purge --pattern "^axiom_ahh"
  python kb_cleanup.py sweep --fix
""")


def main():
    args = sys.argv[1:]
    if not args:
        usage()
        return 0

    cmd = args[0].lower()

    if cmd == 'sweep':
        fix = '--fix' in args
        return cmd_sweep(fix=fix)

    elif cmd == 'purge':
        if '--pattern' in args:
            idx = args.index('--pattern')
            if idx + 1 >= len(args):
                print("Error: --pattern requires a value")
                return 1
            return cmd_purge(args[idx + 1], by_pattern=True)
        elif len(args) > 1:
            return cmd_purge(args[1], by_pattern=False)
        else:
            print("Error: purge requires an id or --pattern")
            return 1

    elif cmd == 'validate':
        return cmd_validate()

    elif cmd in ('list-bad', 'list_bad'):
        return cmd_list_bad()

    else:
        print(f"Unknown command: {cmd}")
        usage()
        return 1


if __name__ == '__main__':
    sys.exit(main())
