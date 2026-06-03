#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================"
echo "    GWU Course Calendar Scraper - GUI Launcher"
echo "================================================================"
echo ""

# Create virtual environment if it doesn't exist
VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment."
        echo "Make sure python3-venv is installed:"
        echo "  Ubuntu/Debian: sudo apt install python3-venv"
        echo "  Fedora:        sudo dnf install python3-venv"
        echo "  Homebrew:      (should work out of the box)"
        exit 1
    fi
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

echo "Checking and installing required packages..."
echo ""
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Check for tkinter availability
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: tkinter is not available for your Python installation."
    echo ""
    echo "To fix this, install the tkinter system package:"
    echo "  Ubuntu/Debian:  sudo apt install python3-tk"
    echo "  Fedora/RHEL:    sudo dnf install python3-tkinter"
    echo "  Arch Linux:     sudo pacman -S tk"
    echo "  Homebrew/Linuxbrew: brew install python-tk@3.14"
    echo "    (replace 3.14 with your Python version)"
    echo ""
    echo "After installing, delete .venv and re-run this script:"
    echo "  rm -rf .venv && ./launch_gui.sh"
    deactivate
    exit 1
fi

echo ""
echo "Launching graphical interface..."
echo ""

python3 gwu_scraper_gui.py

deactivate
