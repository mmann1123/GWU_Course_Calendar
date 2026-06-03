#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================"
echo "    GWU Course Calendar Scraper - Setup and Run"
echo "================================================================"
echo ""
echo "This script will:"
echo "1. Install required Python packages (if needed)"
echo "2. Scrape GWU course schedules"
echo "3. Generate an interactive HTML calendar"
echo ""
echo "Default: Geography courses for Spring 2026"
echo ""
read -p "Press Enter to continue..."

# Create virtual environment if it doesn't exist
VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo ""
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

echo ""
echo "[Step 1/2] Installing required packages..."
echo "================================================================"
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "[Step 2/2] Running the scraper..."
echo "================================================================"
python3 gwu_scraper.py

deactivate

echo ""
echo "================================================================"
echo "Done! Check gwu_course_calendar.html to view your calendar."
echo "================================================================"
echo ""
read -p "Press Enter to exit..."
