#!/bin/bash

echo "================================================================"
echo "    GWU Course Calendar Scraper - GUI Launcher"
echo "================================================================"
echo ""
echo "Checking and installing required packages..."
echo ""

python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet -r requirements.txt

echo ""
echo "Launching graphical interface..."
echo ""

python3 gwu_scraper_gui.py
