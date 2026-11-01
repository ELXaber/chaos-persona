#V08312026
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

# ── 2. Check inference backend (Ollama and/or llama.cpp) ─────
HAVE_OLLAMA=0
HAVE_LLAMACPP=0
command -v ollama &>/dev/null && HAVE_OLLAMA=1

if command -v llama-server &>/dev/null \
   || "$PYTHON" -c "import urllib.request as u; u.urlopen('http://localhost:8080/health', timeout=2)" &>/dev/null \
   || [[ "${CAIOS_BACKEND:-}" == "llamacpp" ]]; then
    HAVE_LLAMACPP=1
fi

# Neither found: install Ollama as the default (existing behavior)
if [[ "$HAVE_OLLAMA" -eq 0 && "$HAVE_LLAMACPP" -eq 0 ]]; then
    echo ""
    info "No inference backend found. Installing Ollama (default)..."
    if [[ "$OS" == "mac" ]]; then
        if command -v brew &>/dev/null; then
            brew install ollama
        else
            fail "Please install Ollama from https://ollama.com/download
       (or install Homebrew first: https://brew.sh)"
        fi
    else
        curl -fsSL https://ollama.com/install.sh | sh
    fi
    HAVE_OLLAMA=1
fi

[[ "$HAVE_OLLAMA" -eq 1 ]] && ok "Ollama $(ollama --version 2>/dev/null | head -1)"
[[ "$HAVE_LLAMACPP" -eq 1 ]] && ok "llama.cpp backend detected"

# ── 3. Install Python dependencies ───────────────────────────
echo ""
info "Installing Python packages..."
"$PYTHON" -m pip install --quiet --upgrade pip
"$PYTHON" -m pip install --quiet numpy pyzmq cryptography flask ollama

# Optional
"$PYTHON" -m pip install --quiet pyyaml 2>/dev/null && ok "pyyaml" || warn "pyyaml unavailable (optional)"
"$PYTHON" -m pip install --quiet pymupdf 2>/dev/null && ok "pymupdf" || warn "pymupdf unavailable (optional)"
"$PYTHON" -m pip install --quiet tesseract 2>/dev/null && ok "tesseract" || warn "tesseract unavailable (optional)"

# Playwright for browser control (optional)
"$PYTHON" -m pip install --quiet playwright 2>/dev/null \
    && playwright install chromium --with-deps 2>/dev/null \
    && ok "playwright + chromium" \
    || warn "playwright unavailable (optional — needed for browser tools)"

# Tesseract OCR (optional — for image-to-text on attached screenshots/documents)
# Note for Linux sudo: If apt install -y tesseract-ocr prompts for a password mid-script and nothing's there to answer it (e.g. someone runs run_caios.sh non-interactively, or piped from something), it'll just hang rather than fail cleanly.
echo ""
info "Installing Tesseract OCR (optional)..."
if [[ "$OS" == "mac" ]]; then
    if command -v brew &>/dev/null; then
        brew install tesseract 2>/dev/null && ok "tesseract" || warn "tesseract install failed (optional)"
    else
        warn "Homebrew not found — skipping tesseract (optional, needed for image OCR)"
    fi
elif [[ "$OS" == "linux" ]]; then
    if command -v apt &>/dev/null; then
        sudo apt install -y tesseract-ocr 2>/dev/null && ok "tesseract-ocr" || warn "tesseract-ocr install failed (optional)"
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm tesseract 2>/dev/null && ok "tesseract" || warn "tesseract install failed (optional)"
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y tesseract 2>/dev/null && ok "tesseract" || warn "tesseract install failed (optional)"
    else
        warn "Unknown package manager — skipping tesseract (optional, needed for image OCR)"
    fi
fi
"$PYTHON" -m pip install --quiet pytesseract pillow 2>/dev/null && ok "pytesseract" || warn "pytesseract unavailable (optional)"

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

# ── 7. Model / backend check ─────────────────────────────────
echo ""
info "Checking inference backend..."

# Prefer llama.cpp if its server is already up
if "$PYTHON" -c "import urllib.request as u; u.urlopen('http://localhost:8080/health', timeout=2)" &>/dev/null \
   || "$PYTHON" -c "import urllib.request as u; u.urlopen('http://localhost:8080/v1/models', timeout=2)" &>/dev/null; then
    ok "llama.cpp server detected on :8080 — skipping Ollama model pull"
    echo "         (Start with e.g. llama-server -m your_model.gguf --ctx-size 32768 --port 8080)"
elif command -v ollama &>/dev/null; then
    info "Checking for Qwen model in Ollama..."
    if ! ollama list 2>/dev/null | grep -qi "qwen"; then
        echo ""
        echo "  Qwen model not found. Pulling qwen3.8:27b (large download, 10–30 min)..."
        echo ""
        if ! ollama pull qwen3.8:27b; then
            warn "qwen3.8:27b failed — trying smaller fallback..."
            ollama pull qwen2.5:7b || warn "Model pull failed. Set one up manually: ollama pull <model>"
        fi
    else
        ok "Qwen model already present in Ollama"
    fi
else
    warn "Neither llama.cpp server nor Ollama detected.
         - For llama.cpp: start the server, then re-run or just launch the bridge.
         - For Ollama: install from https://ollama.com then: ollama pull qwen3.8:27b"
fi

# ── 8. Launch ────────────────────────────────────────────────
# Ollama and the MCP filesystem server are now started by caios_bridge.py
# itself (start_services()), so this works the same whether you launch via
# this script or run `python3 caios_bridge.py` directly next time — see
# SETUP.md. windows-mcp is skipped automatically on Mac/Linux since
# start_services() only starts it when platform.system() == 'Windows'.
echo ""
echo "============================================================"
echo "  Setup complete. Launching CAIOS..."
echo "============================================================"
echo ""
echo "  Web UI: http://localhost:5000"
echo "  Press Ctrl+C to stop."
echo ""

"$PYTHON" caios_bridge.py
