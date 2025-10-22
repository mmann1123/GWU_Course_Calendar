@echo off
echo ================================================================
echo     GWU Course Calendar Scraper - GUI Launcher
echo ================================================================
echo.
echo Checking and installing required packages...
echo.

python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

echo.
echo Launching graphical interface...
echo.

python gwu_scraper_gui.py

pause
