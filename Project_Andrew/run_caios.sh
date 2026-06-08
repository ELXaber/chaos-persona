#V06062026
#!/usr/bin/env bash
# CAIOS — Andrew One  |  First-Time Setup & Launch
# Works on macOS (Intel + Apple Silicon) and Linux (Ubuntu/Debian/Arch)
set -euo pipefail

BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

ok()   { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn() { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
info() { echo -e "${BOLD}[SETUP]${RESET} $*"; }
fail() { echo -e "${RED}[ERROR]${RESET} $*"; exit 1; }

echo ""
echo "============================================================"
echo "  CAIOS — Andrew One  |  First-Time Setup"
echo "============================================================"
echo ""

# ── Detect OS ────────────────────────────────────────────────
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
elif [[ "$OSTYPE" == "linux"* ]]; then
    OS="linux"
fi

# ── 1. Check Python 3.11+ ────────────────────────────────────
PYTHON=""
for cmd in python3.13 python3.12 python3.11 python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        MAJOR=${VER%%.*}
        MINOR=${VER##*.}
        if [[ "$MAJOR" -eq 3 && "$MINOR" -ge 11 ]]; then
            PYTHON="$cmd"
            ok "Python $VER ($cmd)"
            break
        fi
    fi
done

if [[ -z "$PYTHON" ]]; then
    echo ""
    fail "Python 3.11+ not found.

  macOS:   brew install python@3.12
           or download from https://www.python.org/downloads/

  Ubuntu:  sudo apt install python3.12 python3.12-pip
  Arch:    sudo pacman -S python

  Then re-run this script."
fi

# ── 2. Check Ollama ──────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
    echo ""
    info "Ollama not found. Installing..."
    if [[ "$OS" == "mac" ]]; then
        if command -v brew &>/dev/null; then
            brew install ollama
        else
            fail "Please install Ollama from https://ollama.com/download
       (or install Homebrew first: https://brew.sh)"
        fi
    else
        # Official Linux install script
        curl -fsSL https://ollama.com/install.sh | sh
    fi
fi
ok "Ollama $(ollama --version 2>/dev/null | head -1)"

# ── 3. Install Python dependencies ───────────────────────────
echo ""
info "Installing Python packages..."
"$PYTHON" -m pip install --quiet --upgrade pip
"$PYTHON" -m pip install --quiet numpy pyzmq cryptography flask ollama

# Optional
"$PYTHON" -m pip install --quiet pyyaml 2>/dev/null && ok "pyyaml" || warn "pyyaml unavailable (optional)"

# Playwright for browser control (optional)
"$PYTHON" -m pip install --quiet playwright 2>/dev/null \
    && playwright install chromium --with-deps 2>/dev/null \
    && ok "playwright + chromium" \
    || warn "playwright unavailable (optional — needed for browser tools)"

ok "Python packages ready"

# ── 4. Check Node.js ─────────────────────────────────────────
echo ""
if command -v node &>/dev/null; then
    ok "Node.js $(node --version)"
    if ! npm list -g @modelcontextprotocol/server-filesystem &>/dev/null; then
        info "Installing MCP filesystem server..."
        npm install -g @modelcontextprotocol/server-filesystem --silent \
            && ok "MCP filesystem server installed" \
            || warn "MCP filesystem server install failed (optional)"
    else
        ok "MCP filesystem server already installed"
    fi
else
    warn "Node.js not found — MCP filesystem server unavailable.
         Andrew can still use [TOOL:read_file] without it.
         To install Node.js: https://nodejs.org  or  brew install node"
fi

# ── 5. Create directories ─────────────────────────────────────
mkdir -p knowledge_base logs agents plugins
ok "Directories ready"

# ── 6. First boot ────────────────────────────────────────────
echo ""
if [[ ! -f "system_identity.json" ]]; then
    echo "============================================================"
    echo "  FIRST BOOT — Identity setup required"
    echo "============================================================"
    "$PYTHON" master_init.py || fail "Setup failed. Check output above."
else
    ok "Identity already configured"
fi

# ── 7. Pull model ─────────────────────────────────────────────
echo ""
info "Checking for Qwen model..."
if ! ollama list 2>/dev/null | grep -q "qwen"; then
    echo ""
    echo "  Qwen 27B not found. Pulling now."
    echo "  This is a large download — may take 10-30 minutes."
    echo ""
    if ! ollama pull qwen3:27b; then
        warn "qwen3:27b failed. Trying smaller fallback..."
        ollama pull qwen2.5:7b || warn "Model pull failed — set one up manually with: ollama pull <model>"
    fi
else
    ok "Qwen model already downloaded"
fi

# ── 8. Launch ────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  Setup complete. Launching CAIOS..."
echo "============================================================"
echo ""
echo "  Web UI: http://localhost:5000"
echo "  Press Ctrl+C to stop."
echo ""

# Start Ollama if not running
if ! pgrep -x ollama &>/dev/null; then
    ollama serve &>/dev/null &
    OLLAMA_PID=$!
    sleep 2
    ok "Ollama started (pid $OLLAMA_PID)"
else
    ok "Ollama already running"
fi

# Start MCP filesystem server if available
if command -v node &>/dev/null && npm list -g @modelcontextprotocol/server-filesystem &>/dev/null; then
    npx @modelcontextprotocol/server-filesystem --port 3000 "$(pwd)" &>/dev/null &
    ok "MCP filesystem server started on port 3000"
fi

# windows-mcp is Windows-only — skip on Mac/Linux
# Use playwright/os_control.py for browser automation on these platforms

# Launch bridge (blocking)
"$PYTHON" caios_bridge.py
