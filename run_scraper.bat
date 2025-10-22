@echo off
echo ================================================================
echo     GWU Course Calendar Scraper - Setup and Run
echo ================================================================
echo.
echo This script will:
echo 1. Install required Python packages (if needed)
echo 2. Scrape GWU course schedules
echo 3. Generate an interactive HTML calendar
echo.
echo Default: Geography courses for Spring 2026
echo.
pause

echo.
echo [Step 1/2] Installing required packages...
echo ================================================================
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo [Step 2/2] Running the scraper...
echo ================================================================
python gwu_scraper.py

echo.
echo ================================================================
echo Done! Check gwu_course_calendar.html to view your calendar.
echo ================================================================
echo.
pause
