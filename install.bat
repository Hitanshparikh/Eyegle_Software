@echo off
REM Eyegle v1.0 - Windows Installation Script
REM Created by Hivizstudios & Hitansh Parikh

echo.
echo ========================================
echo    Eyegle v1.0 - Installation Script
echo    Advanced Eye Tracking Software
echo    Created by Hivizstudios
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    echo.
    pause
    exit /b 1
)

echo [INFO] Python detected successfully
echo.

REM Check Python version
echo [INFO] Checking Python version...
python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.11+ is required
    echo Please upgrade your Python installation
    echo.
    pause
    exit /b 1
)

echo [INFO] Python version is compatible
echo.

REM Install dependencies
echo [INFO] Installing Eyegle dependencies...
echo This may take a few minutes...
echo.

pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies
    echo Please check your internet connection and try again
    echo.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Installation completed successfully!
echo.
echo To start Eyegle:
echo   python main.py
echo.
echo First-time setup:
echo   1. Allow camera access when prompted
echo   2. Complete calibration (Ctrl+C)
echo   3. Customize gestures in Settings
echo.
echo For help and documentation:
echo   - README.md - Complete guide
echo   - docs/USER_GUIDE.md - Detailed instructions
echo   - docs/GESTURE_MAP.md - Available gestures
echo.
echo Made with ♥ by Hivizstudios & Hitansh Parikh
echo.
pause