# GWU Course Calendar Scraper
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22677063.svg)](https://doi.org/10.5281/zenodo.22677063)

An easy-to-use application that creates a beautiful Google Calendar-style view of GWU course schedules.

![class scheduler demo](static/class_scheduler2.gif)

## What Does This Do?

This app fetches course information from GWU's website and displays it in an interactive weekly calendar. You can:
- See all courses for any subject in a visual weekly layout
- Click on courses to view details (instructor, room, CRN, etc.)
- View overlapping courses side-by-side
- Export course data for further use

---

## Getting Started (3 Easy Steps!)

### Step 1: Install Python

#### **Windows Users**
1. Open the **Microsoft Store** (search for it in the Start menu)
2. Search for **"Python"**
3. Install **Python 3.12** (or the latest version)
4. That's it! Python is now installed.

#### **Mac Users**
1. Open **Terminal** (find it in Applications → Utilities)
2. Install Homebrew (if you don't have it) by pasting this command:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. Install Python by typing:
   ```bash
   brew install python
   ```

#### **Linux Users**
Python is usually already installed! To check, open Terminal and type:
```bash
python3 --version
```
If you don't have it, install it with:
```bash
sudo apt install python3 python3-pip    # Ubuntu/Debian
sudo dnf install python3 python3-pip    # Fedora
```

---

### Step 2: Download This Project

![alt text](static/codebutton.png)
1. Click the green **"Code"** button at the top of this page
2. Click **"Download ZIP"**
3. Unzip the file to a folder on your computer (like your Desktop or Documents)

---

### Step 3: Run the Application

#### **Windows Users**
1. Open the folder where you unzipped the files
2. **Double-click** on `launch_gui.bat`
3. Run despite warning
4. A window will open - that's the app!

#### **Mac/Linux Users**
1. Open **Terminal**
2. Navigate to the folder where you unzipped the files:
   ```bash
   cd ~/Desktop/GWU_Course_Calendar
   ```
   (Replace `~/Desktop/` with wherever you saved it)
3. Make the launcher executable (only need to do this once):
   ```bash
   chmod +x launch_gui.sh
   ```
4. Run the application:
   ```bash
   ./launch_gui.sh
   ```

---

## Using the Application

Once the app opens, you'll see a simple interface:

1. **Select Year**: Choose the academic year
2. **Select Semester**:
   - Spring 01
   - Summer 02
   - Fall 03
3. **Enter Subject Code**: Type the 4-letter subject code (e.g., GEOG, CSCI, MATH, BADM)
4. **Click "Start Scraping"**

The app will:
- Fetch all courses for that subject
- Show progress in real-time
- Generate an interactive calendar HTML file
- Automatically open it in your web browser!

### Common Subject Codes
- `GEOG` - Geography
- `CSCI` - Computer Science
- `MATH` - Mathematics
- `BADM` - Business Administration
- `PSYC` - Psychology
- `ECON` - Economics
- `PSC` - Political Science
- `HIST` - History
- `ENGL` - English

---

## Output Files

The app creates two files:

### 1. `gwu_course_calendar.html`
**This is your interactive calendar!** Open it in any web browser to see:
- Weekly view with all courses laid out by day and time
- Click any course for details (CRN, instructor, location, credits)
- Works offline - no internet needed once created

---

## Edit Mode (For Department Admins)

The interactive calendar includes a powerful **Edit Mode** for planning and modifying course schedules. This is especially useful for department administrators who need to:

### Features

- **Add New Courses**: Create courses from scratch with all details
- **Edit Existing Courses**: Modify any course attribute (instructor, time, room, etc.)
- **Duplicate Courses**: Quickly create new sections based on existing courses
- **Delete Courses**: Remove courses from the schedule
- **Visual Editing**: See changes reflected immediately in the calendar
- **Export to CSV**: Save your edited schedule in a sortable spreadsheet format

### How to Use Edit Mode

![edit mode demo](static/editmode.gif)

1. **Open the calendar HTML file** in your web browser
2. **Click the "✏️ Edit Schedule" tab** at the top
3. **Make changes**:
   - Click "➕ Add New Course" to create a new course
   - Click any course block to edit its details
   - Use the "Duplicate" button to create new sections
   - Use the "Delete" button to remove courses

### Editing Course Details

When you edit a course, you can modify:

- **Subject Code**: Department code (e.g., GEOG, CSCI)
- **Course Number**: The course identifier (e.g., 1001, 2101)
- **Section**: Section number (e.g., 10, 11, 12)
- **CRN**: Course Registration Number
- **Course Title**: Full name of the course
- **Credits**: Number of credit hours
- **Instructor**: Name (Last, F format recommended)
- **Days**: Use presets (MW, TR, MWF) or select custom days
- **Time**: Start and end times (10-minute intervals)
- **Building & Room**: Location information
- **Dates**: Semester date range

### Smart Day Selection

The editor includes convenient day patterns:

- **MW** - Monday/Wednesday
- **TR** - Tuesday/Thursday
- **MWF** - Monday/Wednesday/Friday
- **MTWRF** - Every weekday
- **Custom** - Select any combination

<!-- ### Conflict Detection

Edit Mode automatically detects and displays:

- **Room Conflicts**: Multiple courses in the same room at the same time
- **Instructor Conflicts**: Instructors teaching multiple courses simultaneously
- **Ignore Option**: You can mark known conflicts as "ignored" (saved to your browser) -->

### Exporting Your Schedule

Click **"📥 Export to CSV"** at the bottom of Edit Mode to:

- Save your edited schedule as a CSV file
- Data is automatically sorted by instructor, then course number
- CSV includes all course details in separate columns
- Open in Excel, Google Sheets, or any spreadsheet software

### CSV Export Format

The exported CSV includes these columns:

```csv
CRN, Subject, CourseNum, Section, Title, Credits, Instructor, Days, StartTime, EndTime, Building, Room, Dates
```

### Change Tracking

- The interface shows a counter of unsaved changes
- Modified courses are marked with a ⚠️ indicator
- Hover over courses to see details and identify which to edit
- All changes are stored in the browser (not permanent until exported)

### Tips

- **Duplicate for efficiency**: Creating multiple sections? Edit one course, then duplicate it and change only the section/time/room
- **Export regularly**: Your edits are only saved when you export to CSV
- **Use conflict detection**: Review the "⚠️ Conflicts" tab to catch scheduling issues
- **Sort exports**: CSV exports are pre-sorted by instructor and course number for easy review

---

## Troubleshooting

### "Python is not recognized" or "command not found"
- **Windows**: Restart your computer after installing Python from the Microsoft Store
- **Mac/Linux**: Make sure Python is installed (try `python3 --version` in Terminal)

### The terminal window closes immediately
- **Windows**: Make sure you're double-clicking `launch_gui.bat` (not `launch_gui.sh`)
- **Mac/Linux**: Make sure you're running `./launch_gui.sh` (not `launch_gui.bat`)

### "No module named 'tkinter'" error
- **Mac**: Run `brew install python-tk`
- **Linux**: Run `sudo apt install python3-tk` (Ubuntu/Debian)

### No courses found
- Check your internet connection
- Verify the subject code is correct (must be 4 letters)
- Make sure the semester/year combination is valid (courses might not be posted yet)

### The app installed missing packages automatically
- This is normal! The first time you run it, the app will install BeautifulSoup and Requests
- This only happens once

---

## Tips

- **Save calendars for multiple subjects**: Run the app multiple times with different subject codes
- **Change the output filename**: In the app, edit the "Output Filename" field before scraping
- **Share calendars**: The HTML file can be emailed or shared - it works on any device with a web browser
- **Print your schedule**: Open the HTML file and print from your browser

---

## What's Inside?

- `gwu_scraper_gui.py` - Graphical interface (easy to use)
- `gwu_scraper.py` - Command-line version (for advanced users)
- `launch_gui.bat` - Windows launcher
- `launch_gui.sh` - Mac/Linux launcher
- `requirements.txt` - List of required Python packages (automatically installed)

---

## Features

✅ **Easy to Use**: Graphical interface - no coding required
✅ **Automatic Installation**: Installs needed packages automatically
✅ **Interactive Calendar**: Google Calendar-style weekly view
✅ **Overlap Detection**: Shows overlapping courses side-by-side
✅ **Complete Data**: CRN, instructor, time, location, credits, and status
✅ **Cross-platform**: Works on Windows, Mac, and Linux
✅ **No Internet Needed**: Once created, the calendar works offline

---

## For Advanced Users

### Command-Line Usage

If you prefer the command line:

```bash
# Default: Scrape Geography courses for current term
python gwu_scraper.py

# Scrape specific subject
python gwu_scraper.py --url "https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=CSCI"

# Custom output filename
python gwu_scraper.py --output my_calendar.html --json my_data.json

# Import the registrar's .xlsx schedule instead of scraping
python gwu_scraper.py --xlsx-in "G&E Schedule - Spring 2027.xlsx"

# Export the schedule back to the registrar's .xlsx format
python gwu_scraper.py --xlsx-in schedule.xlsx --xlsx-out updated_schedule.xlsx

# Show all options
python gwu_scraper.py --help
```

### Registrar Spreadsheet Import / Export

Departments can work directly with the GWU registrar's `.xlsx` schedule format
(the *G&E Schedule* "Export" layout) instead of scraping the public website.

In the **GUI**, use the **Registrar Spreadsheet (.xlsx)** buttons:

- **📥 Import .xlsx → Calendar** — load a registrar schedule and view it as a calendar.
- **📤 Export Calendar → .xlsx** — write the current schedule back to the registrar's column layout for submission.

The import/export is **round-trip safe**: registrar-only columns (instructor
GWID, enrollment counts, comments, special-topics section titles, start/end
dates) are preserved so an imported file can be exported again without losing
data. A few notes:

- Times convert between the registrar's 24-hour `HHMM` and the calendar's
  12-hour display automatically.
- Arranged / **TBA** courses (Thesis, Internship, Readings — no meeting time)
  are kept in the data but not drawn on the calendar grid.
- **Status** (Open/Closed) is derived from enrollment vs. capacity.
- Fields the registrar sheet doesn't include — **CRN**, **building**, and
  **room** — are left as *Not specified* (room assignment happens after this
  scheduling stage).

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

This tool is provided as-is for educational purposes. Please use responsibly and in accordance with GWU's terms of service.

---

## Need Help?

1. Read the **Troubleshooting** section above
2. Check that Python is installed: Open Terminal/Command Prompt and type `python --version`
3. Make sure you're using the right launcher file (`.bat` for Windows, `.sh` for Mac/Linux)

**Have fun exploring GWU courses!** 🎓
