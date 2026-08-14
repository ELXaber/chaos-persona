#!/usr/bin/env python3
#V06062026
# =============================================================================
# update_helper.py — CAIOS GitHub update checker
# Called by update.bat and update.sh
# Compares local #V date tags against GitHub, downloads newer files.
#
# Version format: #V06062026  (DDMMYYYY — day/month/year, no separators)
# Exits: 0 = up to date, 1 = updates applied, 2 = errors occurred
# =============================================================================

import sys
import os
import re
import shutil
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

REPO_RAW = sys.argv[1] if len(sys.argv) > 1 else \
    'https://raw.githubusercontent.com/ELXaber/chaos-persona/main/Project_Andrew'

# ── File manifest ─────────────────────────────────────────────
# Add new files here as they're created in the repo.
# Paths are relative to the directory containing this script.
MANIFEST = [
    # Core system
    'orchestrator.py',
    'paradox_oscillator.py',
    'adaptive_reasoning.py',
    'agent_designer.py',
    'curiosity_engine.py',
    'knowledge_base.py',
    'kb_inspect.py',
    # OS and tool layer
    'os_control.py',
    'tool_dispatcher.py',
    'caios_mcp_client.py',
    # Identity, users, abstraction
    'system_identity.py',
    'abstraction_selector.py',
    'user_profile_kb.py',
    'axiom_manager.py',
    'manager_users.py',
    # Inference and config
    'ollama_config.py',
    'caios_chat.py',
    'caios_bridge.py',
    # Encryption and mesh
    'chaos_encryption.py',
    'mesh_network.py',
    # Initialisation
    'master_init.py',
    # UI and scripts
    'caios_chat_ui.html',
    'run_caios.bat',
    'run_caios.sh',
    'update.bat',
    'update.sh',
    # Docs
    'readme.txt',
    'SETUP.md',
]

# Files to never overwrite automatically (user-configured)
PROTECTED = {
    'system_identity.json',
    'users.json',
    'api_clients.json',
    'CAIOS.txt',          # User may have custom edits
}

# ── Version parsing ───────────────────────────────────────────

VERSION_PATTERN = re.compile(
    r'^(?:#|rem|<!--)\s*V?(\d{2})(\d{2})(\d{4})',
    re.IGNORECASE | re.MULTILINE
)

def parse_version(text: str) -> tuple:
    """
    Extract version date from file content.
    Format: #V06062026 = MMDDYYYY → month=06, day=06, year=2026.
    Returns (0, 0, 0) if no version tag found.
    """
    m = VERSION_PATTERN.search(text[:500])  # only check first 500 chars
    if not m:
        return (0, 0, 0)
    month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return (year, month, day)  # YYYY, MM, DD for correct comparison

def version_str(v: tuple) -> str:
    if v == (0, 0, 0):
        return 'no version tag'
    return f"{v[2]:02d}/{v[1]:02d}/{v[0]}"

# ── File fetching ─────────────────────────────────────────────

def fetch_remote(filename: str) -> tuple[str | None, str]:
    """
    Fetch file content from GitHub.
    Returns (content, error_message). content is None on failure.
    """
    url = f"{REPO_RAW.rstrip('/')}/{filename}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'CAIOS-Updater/1.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode('utf-8', errors='replace'), ''
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, f'not found on GitHub (404)'
        return None, f'HTTP {e.code}'
    except urllib.error.URLError as e:
        return None, f'network error: {e.reason}'
    except Exception as e:
        return None, str(e)

# ── Main ──────────────────────────────────────────────────────

def main():
    script_dir = Path(__file__).parent
    updated = 0
    errors = 0
    skipped = 0

    col_file  = 32
    col_local = 12
    col_remote= 12

    print(f"{'File':<{col_file}} {'Local':<{col_local}} {'Remote':<{col_remote}} Status")
    print('─' * 72)

    for filename in MANIFEST:
        local_path = script_dir / filename

        # Read local version
        local_ver = (0, 0, 0)
        if local_path.exists():
            try:
                local_text = local_path.read_text(encoding='utf-8', errors='replace')
                local_ver = parse_version(local_text)
            except Exception:
                pass

        # Fetch remote
        remote_text, err = fetch_remote(filename)

        if remote_text is None:
            # 404 = file doesn't exist on GitHub yet, not an error
            status = f'skip ({err})'
            skipped += 1
            print(f"{filename:<{col_file}} {version_str(local_ver):<{col_local}} {'—':<{col_remote}} {status}")
            continue

        remote_ver = parse_version(remote_text)

        # Compare
        if remote_ver == (0, 0, 0):
            status = 'no version tag on remote — skipped'
            skipped += 1
        elif remote_ver <= local_ver:
            status = 'up to date'
        else:
            # Remote is newer — back up local and download
            if local_path.exists():
                backup = local_path.with_suffix(local_path.suffix + '.bak')
                shutil.copy2(str(local_path), str(backup))

            try:
                local_path.write_text(remote_text, encoding='utf-8')
                status = '✓ UPDATED'
                updated += 1
            except Exception as e:
                status = f'write error: {e}'
                errors += 1

        print(f"{filename:<{col_file}} {version_str(local_ver):<{col_local}} {version_str(remote_ver):<{col_remote}} {status}")

    # Summary
    print('─' * 72)
    print(f"\nChecked {len(MANIFEST)} files: "
          f"{updated} updated, {skipped} skipped, {errors} errors.")

    if updated > 0:
        print("\nBackups of replaced files saved as <filename>.bak")
        print("Restart CAIOS (run_caios.bat / run_caios.sh) to apply updates.")

    if errors > 0:
        return 2
    if updated > 0:
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
