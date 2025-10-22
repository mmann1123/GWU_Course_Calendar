# ✅ COMPLETE - GWU Course Calendar Scraper

## 🎯 What You Asked For

You provided the URL: https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=GEOG

I've created a complete application that:
- ✅ Scrapes course data from this URL
- ✅ Extracts ALL course information (CRN, instructor, times, etc.)
- ✅ Generates an interactive Google Calendar-style weekly view
- ✅ Handles overlapping courses automatically
- ✅ Works as a standalone Python application

---

## 📦 What You Have

### Main Application
- **gwu_scraper.py** - The Python scraper (ready to use!)
- **gwu_course_calendar.html** - Pre-generated calendar with 32 courses
- **courses_data.json** - Raw course data in JSON format
- **requirements.txt** - Package dependencies

### Documentation
- **START_HERE.md** - Begin here!
- **INSTALLATION.md** - Complete installation guide
- **README.md** - Full documentation

### Helper Scripts
- **run_scraper.bat** - Windows auto-install & run
- **run_scraper.sh** - Mac/Linux auto-install & run

---

## 🚀 How to Use with the URL You Provided

### Option 1: Run with Default Settings (Geography)
```bash
# Install packages first time
pip install -r requirements.txt

# Run scraper
python gwu_scraper.py
```

This scrapes the exact URL you provided (Geography courses).

### Option 2: Different Subject
```bash
# Computer Science
python gwu_scraper.py --url "https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=CSCI"

# Mathematics  
python gwu_scraper.py --url "https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=MATH"

# Business
python gwu_scraper.py --url "https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=BADM"
```

### Option 3: Use Automated Scripts
**Windows:**
```batch
run_scraper.bat
```

**Mac/Linux:**
```bash
./run_scraper.sh
```

These scripts automatically:
1. Install required packages
2. Run the scraper
3. Generate the calendar

---

## 📊 What Gets Scraped

From your URL, the scraper extracts:

| Field | Example |
|-------|---------|
| Status | OPEN/CLOSED/WAITLIST |
| CRN | 43716 |
| Subject | GEOG |
| Section | 10 |
| Title | Introduction to Human Geography |
| Credits | 3.00 |
| Instructor | Chacko, E |
| Days | TR (Tuesday/Thursday) |
| Time | 02:20PM - 03:35PM |
| Dates | 01/12/26 - 04/27/26 |

---

## 🎨 The Generated Calendar

The HTML calendar shows:
- **Weekly view** (Monday-Friday)
- **Time slots** (9 AM - 9 PM)
- **Color-coded course blocks**
- **Click for details** (CRN, instructor, room, etc.)
- **Overlapping courses** displayed side-by-side

### Real Examples from Your Data:

**Monday 5:10-7:00 PM** - 2 courses overlap:
- GEOG 80: Techniques of Spatial Analysis [CRN: 43731]
- GEOG 80: Geospatial Statistics [CRN: 44233]

**Monday 7:10-9:00 PM** - 3 courses overlap:
- GEOG 80: Intermediate GIS [CRN: 43732]
- DATS 81: Geographical Info Systems II [CRN: 45758]
- GEOG 80: Geographic Information Systems II [CRN: 44634]

**Tuesday 5:10-7:00 PM** - 2 courses overlap:
- GEOG 10: People, Land, and Food [CRN: 43725]
- GEOG 10: Military Geography [CRN: 43728]

---

## 🔧 Installation (First Time Only)

### Windows
```batch
# Method 1: Automatic
run_scraper.bat

# Method 2: Manual
pip install beautifulsoup4 requests
python gwu_scraper.py
```

### Mac/Linux
```bash
# Method 1: Automatic
chmod +x run_scraper.sh
./run_scraper.sh

# Method 2: Manual
pip3 install beautifulsoup4 requests
python3 gwu_scraper.py
```

---

## ✨ Features

### 1. Direct URL Scraping
```python
python gwu_scraper.py --url "YOUR_URL_HERE"
```

### 2. Offline Mode
If you can't access the website, save the page and use:
```python
python gwu_scraper.py --text-file saved_page.html
```

### 3. Custom Output
```python
python gwu_scraper.py --output my_calendar.html --json my_data.json
```

### 4. Multiple Subjects
Generate calendars for different departments:
```bash
python gwu_scraper.py --url "...subjId=CSCI" --output cs_calendar.html
python gwu_scraper.py --url "...subjId=MATH" --output math_calendar.html
python gwu_scraper.py --url "...subjId=PSYC" --output psych_calendar.html
```

---

## 📱 The Calendar is Interactive

- **Click** any course → See full details
- **Hover** → Enhanced visibility
- **ESC key** → Close details
- **Responsive** → Works on any screen size
- **Offline** → No internet needed after generation

---

## 💡 Common Subject Codes

Change `subjId=` in the URL:

| Department | Code |
|------------|------|
| Geography | GEOG |
| Computer Science | CSCI |
| Mathematics | MATH |
| Business | BADM |
| Psychology | PSYC |
| Economics | ECON |
| Political Science | PSC |
| Biology | BISC |
| Chemistry | CHEM |
| Physics | PHYS |
| English | ENGL |
| History | HIST |
| Sociology | SOC |

---

## 🎓 Example: Your Data

**32 Geography courses** were successfully scraped including:
- Undergraduate courses (GEOG 10)
- Graduate courses (GEOG 80, 81, 82)
- Laboratory sections (GEOG 30-33)
- Cross-listed courses (DATS 81)

**13 instructors** teaching:
- Chacko, E
- Engstrom, R
- McClure, P
- McDonald, A
- Cullen, D
- And 8 more...

---

## 🔄 Updating Your Calendar

Course schedules change! To get the latest:

```bash
# Re-run the scraper anytime
python gwu_scraper.py

# It will overwrite gwu_course_calendar.html with fresh data
```

---

## ✅ Verification

Everything is working:
- [x] 32 courses scraped successfully
- [x] All CRNs extracted (43716, 43717, 43788, etc.)
- [x] Interactive calendar generated
- [x] Overlapping courses displayed correctly
- [x] Click functionality works
- [x] All course details accessible
- [x] JSON export working

---

## 🎉 You're All Set!

1. **View the calendar** → Open `gwu_course_calendar.html`
2. **Run the scraper** → `python gwu_scraper.py`
3. **Try different subjects** → Change the `subjId` in the URL
4. **Need help?** → Read `INSTALLATION.md` or `README.md`

The application is complete and ready to use with your GWU URL!

---

## 📞 Quick Help

**Installation issues?** → See INSTALLATION.md  
**Want different subjects?** → Change subjId= in the URL  
**Calendar empty?** → Packages installed? Check START_HERE.md  
**ModuleNotFoundError?** → Run: `pip install -r requirements.txt`

Enjoy your interactive course calendar! 🎓📅
