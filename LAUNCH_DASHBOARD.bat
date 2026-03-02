@echo off
REM =============================================================================
REM  AiPi-MemoryCore Dashboard Launcher (Windows)
REM  Double-click this file or create a desktop shortcut to launch the dashboard
REM =============================================================================

title AiPi-MemoryCore Dashboard
color 0A

echo.
echo  ============================================================
echo   AiPi-MemoryCore Dashboard Launcher
echo   Phase 1-5 Memory Architecture
echo  ============================================================
echo.

REM Change to the script's directory (repo root)
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH.
    echo.
    echo Please install Python 3.11+ from https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Check if dependencies are installed
if not exist "venv" (
    echo [INFO] Virtual environment not found.
    echo [INFO] Run 'pip install -r requirements.txt' first.
    echo.
    pause
    exit /b 1
)

echo [INFO] Launching dashboard...
echo.

REM Launch the Python launcher script
python launch_dashboard.py

REM Keep console open if there was an error
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Dashboard failed to start.
    pause
)
