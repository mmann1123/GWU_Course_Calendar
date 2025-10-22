#!/bin/bash

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

echo ""
echo "[Step 1/2] Installing required packages..."
echo "================================================================"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo ""
echo "[Step 2/2] Running the scraper..."
echo "================================================================"
python3 gwu_scraper.py

echo ""
echo "================================================================"
echo "Done! Check gwu_course_calendar.html to view your calendar."
echo "================================================================"
echo ""
read -p "Press Enter to exit..."
