#V06062026
#!/usr/bin/env bash
# CAIOS — Update Check  |  github.com/ELXaber/chaos-persona

set -euo pipefail

REPO_RAW="https://raw.githubusercontent.com/ELXaber/chaos-persona/main/Project_Andrew"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "============================================================"
echo "  CAIOS — Update Check  |  github.com/ELXaber/chaos-persona"
echo "============================================================"
echo ""

# Find Python
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [[ -z "$PYTHON" ]]; then
    echo "[ERROR] Python not found. Run ./run_caios.sh first."
    exit 1
fi

cd "$SCRIPT_DIR"
"$PYTHON" update_helper.py "$REPO_RAW"
EXIT_CODE=$?

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "============================================================"
    echo "  All files are up to date."
    echo "============================================================"
elif [[ $EXIT_CODE -eq 1 ]]; then
    echo "============================================================"
    echo "  Updates applied. Restart CAIOS to use new versions."
    echo "============================================================"
else
    echo "============================================================"
    echo "  Update check encountered errors. See output above."
    echo "============================================================"
fi
echo ""
