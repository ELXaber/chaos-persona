@rem V06122026
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

:: ── 2. Check Ollama ──────────────────────────────────────────
ollama --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Ollama not found.
    echo.
    echo   Please install Ollama from:
    echo   https://ollama.com/download
    echo.
    echo   Then re-run this script.
    pause
    exit /b 1
)
echo [OK] Ollama detected

:: ── 3. Install Python dependencies ───────────────────────────
echo.
echo [SETUP] Installing Python packages...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet numpy pyzmq cryptography flask ollama

:: Optional packages — failures are non-fatal
python -m pip install --quiet windows-mcp 2>nul && echo [OK] windows-mcp installed || echo [SKIP] windows-mcp unavailable ^(optional^)
python -m pip install --quiet pyyaml 2>nul && echo [OK] pyyaml installed || echo [SKIP] pyyaml unavailable ^(optional^)
python -m pip install --quiet uv 2>nul && echo [OK] uv installed || echo [SKIP] uv unavailable ^(optional^)

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

:: ── 7. Pull model if not present ─────────────────────────────
echo.
echo [SETUP] Checking for Qwen 27B model...
ollama list 2>nul | findstr "qwen" >nul
if errorlevel 1 (
    echo.
    echo   Qwen 27B not found. Pulling now — this is a large download.
    echo   Progress will appear below. This may take 10-30 minutes
    echo   depending on your connection.
    echo.
    ollama pull qwen3:27b
    if errorlevel 1 (
        echo.
        echo [WARN] qwen3:27b pull failed. Trying smaller fallback...
        ollama pull qwen2.5:7b
    )
) else (
    echo [OK] Qwen model already downloaded
)

:: ── 8. Launch ─────────────────────────────────────────────────
echo.
echo ============================================================
echo   Setup complete. Launching CAIOS...
echo ============================================================
echo.
echo   Web UI: http://localhost:5000
echo   Press Ctrl+C to stop.
echo.

:: Start Ollama in background if not running
ollama list >nul 2>&1 || start /B ollama serve

:: Start windows-mcp if installed
windows-mcp --version >nul 2>&1
if not errorlevel 1 (
    start /B windows-mcp serve --transport sse --host localhost --port 8000
    echo [OK] windows-mcp started on port 8000
)

:: Start MCP filesystem server if Node available
node --version >nul 2>&1
if not errorlevel 1 (
    npm list -g @modelcontextprotocol/server-filesystem >nul 2>&1
    if not errorlevel 1 (
        start /B npx @modelcontextprotocol/server-filesystem --port 3000 "%CD%"
        echo [OK] MCP filesystem server started on port 3000
    )
)

:: Small delay to let background services start
timeout /t 2 /nobreak >nul

:: Launch the bridge (blocking — stays open)
python caios_bridge.py
