@rem V06062026
@echo off
setlocal EnableDelayedExpansion
title CAIOS — Update Check

echo.
echo ============================================================
echo   CAIOS — Update Check  ^|  github.com/ELXaber/chaos-persona
echo ============================================================
echo.

set REPO_RAW=https://raw.githubusercontent.com/ELXaber/chaos-persona/main/Project_Andrew
set UPDATED=0
set CHECKED=0
set SKIPPED=0
set ERRORS=0

rem ── Requires Python (already a CAIOS dependency) ─────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Run run_caios.bat first.
    pause
    exit /b 1
)

rem ── File manifest — add new files here as they're created ────
rem    Format: filename (relative to Project_Andrew root)
set FILES=^
    orchestrator.py ^
    paradox_oscillator.py ^
    adaptive_reasoning.py ^
    agent_designer.py ^
    curiosity_engine.py ^
    knowledge_base.py ^
    kb_inspect.py ^
    os_control.py ^
    abstraction_selector.py ^
    axiom_manager.py ^
    system_identity.py ^
    ollama_config.py ^
    caios_chat.py ^
    caios_bridge.py ^
    caios_mcp_client.py ^
    tool_dispatcher.py ^
    mesh_network.py ^
    chaos_encryption.py ^
    master_init.py ^
    user_profile_kb.py ^
    manager_users.py ^
    caios_chat_ui.html ^
    run_caios.bat ^
    run_caios.sh ^
    readme.txt ^
    SETUP.md

echo Checking for updates against GitHub...
echo.

rem ── Call Python to do the actual version comparison ──────────
rem    (batch string manipulation with dates is painful)
python "%~dp0update_helper.py" %REPO_RAW%
set EXIT_CODE=%errorlevel%

if %EXIT_CODE% == 0 (
    echo.
    echo ============================================================
    echo   All files are up to date.
    echo ============================================================
) else if %EXIT_CODE% == 1 (
    echo.
    echo ============================================================
    echo   Updates applied. Restart CAIOS to use new versions.
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo   Update check encountered errors. See output above.
    echo ============================================================
)

echo.
pause
