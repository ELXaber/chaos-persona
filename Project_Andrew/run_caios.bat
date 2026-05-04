@echo off
title CAIOS - Andrew One

echo ================================================
echo        Launching CAIOS - Project Andrew
echo ================================================
echo.

:: Check for Ollama
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Ollama is not installed or not in PATH.
    echo Please install Ollama from https://ollama.com/download
    pause
    exit /b
)

echo ✓ Ollama detected.

:: Run master_init only if system_identity.json doesn't exist yet
if not exist "system_identity.json" (
    echo First boot detected. Running initial setup...
    python master_init.py
    echo.
)

echo Launching Andrew One...
echo.

:: Start the chat interface
python caios_chat.py

pause