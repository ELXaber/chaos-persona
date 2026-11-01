@rem V10312026
@echo off
setlocal EnableDelayedExpansion
title CAIOS — Andrew One Setup

echo.
echo ============================================================
echo   CAIOS — Andrew One  ^|  First-Time Setup
echo ============================================================
echo.

:: ── 1. Check Python ──────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo.
    echo   Please install Python 3.11 or newer from:
    echo   https://www.python.org/downloads/
    echo.
    echo   During install, check "Add Python to PATH"
    echo   then re-run this script.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK] Python %PY_VER%

:: ── 2. Check inference backend (Ollama and/or llama.cpp) ─────
set HAVE_OLLAMA=0
set HAVE_LLAMACPP=0

ollama --version >nul 2>&1
if not errorlevel 1 set HAVE_OLLAMA=1

where llama-server >nul 2>&1
if not errorlevel 1 set HAVE_LLAMACPP=1
python -c "import urllib.request as u; u.urlopen('http://localhost:8080/health', timeout=2)" >nul 2>&1
if not errorlevel 1 set HAVE_LLAMACPP=1
if /i "%CAIOS_BACKEND%"=="llamacpp" set HAVE_LLAMACPP=1

if "%HAVE_OLLAMA%"=="0" if "%HAVE_LLAMACPP%"=="0" (
    echo.
    echo [ERROR] No inference backend found.
    echo.
    echo   Install ONE of:
    echo     Ollama     https://ollama.com/download            ^(easiest, recommended^)
    echo     llama.cpp  https://github.com/ggerganov/llama.cpp ^(local GGUF models^)
    echo.
    echo   llama.cpp users: start the server first, for example:
    echo     llama-server -m your_model.gguf --ctx-size 32768 --port 8080
    echo   or run:  set CAIOS_BACKEND=llamacpp   then re-run this script.
    pause
    exit /b 1
)
if "%HAVE_OLLAMA%"=="1" echo [OK] Ollama detected
if "%HAVE_LLAMACPP%"=="1" echo [OK] llama.cpp detected

:: ── 3. Install Python dependencies ───────────────────────────
echo.
echo [SETUP] Installing Python packages...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet numpy pyzmq cryptography flask ollama

:: Optional packages — failures are non-fatal
python -m pip install --quiet windows-mcp 2>nul && echo [OK] windows-mcp installed || echo [SKIP] windows-mcp unavailable ^(optional^)
python -m pip install --quiet pyyaml 2>nul && echo [OK] pyyaml installed || echo [SKIP] pyyaml unavailable ^(optional^)
python -m pip install --quiet uv 2>nul && echo [OK] uv installed || echo [SKIP] uv unavailable ^(optional^)
python -m pip install --quiet winocr[cv2] 2>nul && echo [OK] winocr installed || echo [SKIP] winocr unavailable ^(optional^)
python -m pip install --quiet pymupdf 2>nul && echo [OK] pymupdf installed || echo [SKIP] pymupdf unavailable ^(optional^)
python -m pip install --quiet tesseract 2>nul && echo [OK] tesseract installed || echo [SKIP] tesseract unavailable ^(optional^)
echo [OK] Python packages ready

:: ── 4. Check Node.js (for MCP filesystem server) ─────────────
node --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARN] Node.js not found — MCP filesystem server unavailable.
    echo        Andrew can still read files via [TOOL:read_file] without it.
    echo        To enable full MCP access later, install from: https://nodejs.org
    echo.
) else (
    for /f %%v in ('node --version') do set NODE_VER=%%v
    echo [OK] Node.js %NODE_VER%
    :: Install filesystem MCP server globally if npm available
    npm list -g @modelcontextprotocol/server-filesystem >nul 2>&1
    if errorlevel 1 (
        echo [SETUP] Installing MCP filesystem server...
        npm install -g @modelcontextprotocol/server-filesystem --silent 2>nul
        echo [OK] MCP filesystem server installed
    ) else (
        echo [OK] MCP filesystem server already installed
    )
)

:: ── 5. Create knowledge_base directory ───────────────────────
if not exist "knowledge_base" (
    mkdir knowledge_base
    echo [OK] knowledge_base\ created
) else (
    echo [OK] knowledge_base\ exists
)

:: ── 6. First boot check ───────────────────────────────────────
if not exist "system_identity.json" (
    echo.
    echo ============================================================
    echo   FIRST BOOT — Identity setup required
    echo ============================================================
    python master_init.py
    if errorlevel 1 (
        echo [ERROR] Setup failed. Check the output above.
        pause
        exit /b 1
    )
) else (
    echo [OK] Identity already configured
)

:: ── 7. Pull model (Ollama only) ──────────────────────────────
echo.
if "%HAVE_OLLAMA%"=="0" (
    echo [SKIP] Ollama not installed - skipping model pull.
    echo        llama.cpp mode: make sure llama-server is running with a GGUF, for example:
    echo        llama-server -m your_model.gguf --ctx-size 32768 --port 8080
    goto :launch
)
python -c "import urllib.request as u; u.urlopen('http://localhost:8080/health', timeout=2)" >nul 2>&1
if not errorlevel 1 (
    echo [SKIP] llama.cpp server is running - skipping Qwen pull.
    echo        ^(Run "ollama pull qwen3.8:27b" later if you also want Ollama models^)
    goto :launch
)

:: --- existing code, unchanged ---
echo [SETUP] Checking for Qwen 27B model...
ollama list 2>nul | findstr "qwen" >nul
if errorlevel 1 (
    ... existing pull + fallback ...
) else (
    echo [OK] Qwen model already downloaded
)

:: ── 8. Launch ─────────────────────────────────────────────────
:: Ollama, windows-mcp, and the MCP filesystem server are now started
:: by caios_bridge.py itself (start_services()), so this works the same
:: whether you launch via this script or run `python caios_bridge.py`
:: directly next time — see SETUP.md.
echo.
echo ============================================================
echo   Setup complete. Launching CAIOS...
echo ============================================================
echo.
echo   Web UI: http://localhost:5000
echo   Press Ctrl+C to stop.
echo.

python caios_bridge.py
