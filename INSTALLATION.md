# 🔧 Installation Guide

## Quick Install (Windows)

### Option 1: Use the Automated Script (EASIEST)
1. Double-click **run_scraper.bat**
2. The script will automatically install all requirements and run the scraper
3. Done! 🎉

### Option 2: Manual Installation
Open Command Prompt and run:
```batch
pip install -r requirements.txt
```

Or install packages individually:
```batch
pip install beautifulsoup4
pip install requests
```

---

## Quick Install (Mac/Linux)

### Option 1: Use the Automated Script (EASIEST)
1. Open Terminal in the folder containing the files
2. Run: `chmod +x run_scraper.sh` (first time only)
3. Run: `./run_scraper.sh`
4. The script will automatically install all requirements and run the scraper
5. Done! 🎉

### Option 2: Manual Installation
Open Terminal and run:
```bash
pip3 install -r requirements.txt
```

Or install packages individually:
```bash
pip3 install beautifulsoup4
pip3 install requests
```

---

## Detailed Step-by-Step (Windows)

### Step 1: Install Python (if not already installed)
1. Go to https://www.python.org/downloads/
2. Download Python 3.8 or higher
3. Run the installer
4. ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation
5. Click "Install Now"

### Step 2: Verify Python Installation
1. Open Command Prompt (press Windows key, type "cmd", press Enter)
2. Type: `python --version`
3. You should see something like: `Python 3.12.0`

### Step 3: Install Required Packages
Choose one method:

**Method A - Automatic (RECOMMENDED)**
```batch
cd C:\Users\YourUsername\Downloads\files
pip install -r requirements.txt
```

**Method B - Manual**
```batch
pip install beautifulsoup4
pip install requests
```

**Method C - Use the run_scraper.bat script** (it does everything for you)

### Step 4: Verify Installation
```batch
pip list
```
You should see `beautifulsoup4` and `requests` in the list.

### Step 5: Run the Scraper
```batch
python gwu_scraper.py
```

---

## Detailed Step-by-Step (Mac/Linux)

### Step 1: Verify Python Installation
Most Mac/Linux systems come with Python pre-installed.
Open Terminal and type:
```bash
python3 --version
```
You should see Python 3.8 or higher.

If Python is not installed:
- **Mac**: Install from https://www.python.org/downloads/ or use Homebrew: `brew install python3`
- **Linux**: `sudo apt install python3 python3-pip` (Ubuntu/Debian) or `sudo yum install python3` (RedHat/CentOS)

### Step 2: Install Required Packages
Navigate to the folder with the files:
```bash
cd ~/Downloads/files
```

Then install:
```bash
pip3 install -r requirements.txt
```

Or manually:
```bash
pip3 install beautifulsoup4
pip3 install requests
```

### Step 3: Make Scripts Executable (first time only)
```bash
chmod +x run_scraper.sh
chmod +x gwu_scraper.py
```

### Step 4: Run the Scraper
```bash
python3 gwu_scraper.py
```

Or use the automated script:
```bash
./run_scraper.sh
```

---

## Troubleshooting

### "python is not recognized" (Windows)
**Problem**: Python not in PATH

**Solution**:
1. Reinstall Python and check "Add Python to PATH"
2. Or manually add to PATH:
   - Search for "Environment Variables" in Windows
   - Edit "Path" variable
   - Add: `C:\Users\YourUsername\AppData\Local\Programs\Python\Python312\`

### "pip is not recognized" (Windows)
**Solution**:
```batch
python -m pip install beautifulsoup4
python -m pip install requests
```

### "command not found: pip3" (Mac/Linux)
**Solution**:
```bash
python3 -m pip install beautifulsoup4
python3 -m pip install requests
```

### "Permission denied" (Mac/Linux)
**Solution**: Add `--user` flag:
```bash
pip3 install --user beautifulsoup4
pip3 install --user requests
```

### Packages install but script still fails
**Solution**: Make sure you're using the same Python version:
```bash
# Windows
where python
python -m pip list

# Mac/Linux
which python3
python3 -m pip list
```

### SSL Certificate Errors
**Solution**: Update pip first:
```bash
# Windows
python -m pip install --upgrade pip

# Mac/Linux
python3 -m pip install --upgrade pip
```

---

## Alternative: Virtual Environment (Advanced)

If you want to keep packages isolated:

### Windows
```batch
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python gwu_scraper.py
```

### Mac/Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 gwu_scraper.py
```

---

## Verification Checklist

After installation, verify everything works:

```bash
# Check Python
python --version   # or python3 --version

# Check pip
pip --version      # or pip3 --version

# Check installed packages
pip list | grep beautifulsoup4
pip list | grep requests

# Test the scraper (should run without errors)
python gwu_scraper.py --help
```

You should see the help message with all available options.

---

## What Each Package Does

### beautifulsoup4
- **Purpose**: Parse HTML from websites
- **Used for**: Extracting course information from GWU's schedule page
- **Size**: ~500 KB

### requests
- **Purpose**: Make HTTP requests to websites
- **Used for**: Downloading the GWU course schedule webpage
- **Size**: ~500 KB

Total disk space needed: ~1-2 MB

---

## Still Having Issues?

### Option 1: Use the Pre-Generated Calendar
If you're having trouble with installation, you can still use the calendar!
Just open **gwu_course_calendar.html** in your browser - it's already generated and ready to use.

### Option 2: Manual Package Download
If pip isn't working, you can download packages manually:
1. Go to https://pypi.org/project/beautifulsoup4/#files
2. Download the .whl file
3. Install: `pip install beautifulsoup4-X.X.X-py3-none-any.whl`

### Option 3: Use Anaconda
If you have Anaconda installed:
```bash
conda install beautifulsoup4
conda install requests
```

---

## Success! ✅

Once installed, you can:
1. Run the scraper anytime: `python gwu_scraper.py`
2. Generate calendars for different subjects
3. Keep your course schedules organized

**Remember**: You only need to install packages once! After that, just run the scraper whenever you need an updated calendar.

---

## Quick Reference

```bash
# Install (do once)
pip install -r requirements.txt

# Run scraper (do anytime)
python gwu_scraper.py

# For different subjects
python gwu_scraper.py --url "https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=CSCI"

# Get help
python gwu_scraper.py --help
```

Happy scraping! 🎓
