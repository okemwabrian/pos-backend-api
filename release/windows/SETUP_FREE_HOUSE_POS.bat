@echo off
setlocal
title FREE HOUSE POS Setup

where py >nul 2>nul
if errorlevel 1 (
    echo Python 3.12 or newer was not found. Install it from https://www.python.org/downloads/
    pause
    exit /b 1
)

py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)"
if errorlevel 1 (
    echo Python 3.12 or newer is required. Install it from https://www.python.org/downloads/
    pause
    exit /b 1
)

py -3 "%~dp0setup_local_pos.py"
if errorlevel 1 (
    echo.
    echo FREE HOUSE POS setup or startup failed. Review the error above.
    pause
    exit /b 1
)
