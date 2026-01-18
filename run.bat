@echo off
REM Eyegle v1.0 - Quick Launch Script
REM Created by Hivizstudios & Hitansh Parikh

title Eyegle v1.0 - Advanced Eye Tracking

echo.
echo ================================
echo    Eyegle v1.0 - Starting...
echo    Advanced Eye Tracking
echo    by Hivizstudios
echo ================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please run install.bat first.
    pause
    exit /b 1
)

REM Launch Eyegle
echo [INFO] Launching Eyegle...
echo Press Ctrl+C to exit
echo.

python main.py

echo.
echo [INFO] Eyegle has been closed.
pause