#!/bin/bash

# Eyegle v1.0 - Unix Installation Script
# Created by Hivizstudios & Hitansh Parikh

echo
echo "========================================"
echo "   Eyegle v1.0 - Installation Script"
echo "   Advanced Eye Tracking Software"
echo "   Created by Hivizstudios"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.11+ from your package manager"
    echo
    exit 1
fi

echo "[INFO] Python 3 detected successfully"
echo

# Check Python version
python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[ERROR] Python 3.11+ is required"
    echo "Please upgrade your Python installation"
    echo
    exit 1
fi

echo "[INFO] Python version is compatible"
echo

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "[ERROR] pip3 is not installed"
    echo "Please install pip3 for Python package management"
    echo
    exit 1
fi

# Install dependencies
echo "[INFO] Installing Eyegle dependencies..."
echo "This may take a few minutes..."
echo

pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo
    echo "[ERROR] Failed to install dependencies"
    echo "Please check your internet connection and try again"
    echo
    exit 1
fi

echo
echo "[SUCCESS] Installation completed successfully!"
echo
echo "To start Eyegle:"
echo "  python3 main.py"
echo
echo "First-time setup:"
echo "  1. Allow camera access when prompted"
echo "  2. Complete calibration (Ctrl+C)"
echo "  3. Customize gestures in Settings"
echo
echo "For help and documentation:"
echo "  - README.md - Complete guide"
echo "  - docs/USER_GUIDE.md - Detailed instructions"
echo "  - docs/GESTURE_MAP.md - Available gestures"
echo
echo "Made with ♥ by Hivizstudios & Hitansh Parikh"
echo