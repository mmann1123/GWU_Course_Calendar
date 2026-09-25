# GWU Course Calendar

<a href="https://doi.org/10.5281/zenodo.22677063"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.22677063.svg" alt="DOI"></a>

Turn GWU course schedules into an interactive, Google Calendar-style weekly view, then plan and edit the schedule and send it back to the registrar.

![class scheduler demo](static/class_scheduler2.gif)

## What Does This Do?

- **See a whole subject at a glance.** Every section of a subject is laid out by day and time, with overlapping courses side by side.
- **Click a course for details.** You can see the instructor, room, CRN, credits and dates.
- **Spot problems.** Room conflicts and instructor double-bookings are flagged automatically.
- **Plan next semester.** Add, edit, duplicate and delete courses in Edit Mode.
- **Work with the registrar's spreadsheet.** Upload the registrar's `.xlsx` schedule, edit it on the calendar, and download it again in the same format.

There are two ways to use it. The website needs no installation. The desktop app runs on your own computer.

---

## Option 1: Use the Website (Easiest)

Go to **<https://courses.pygis.io/>**. Nothing to install.

The home page offers two ways to build a calendar:

1. **Scrape a subject.** Pick a year and semester, type a subject code such as `GEOG`, and click the button. The site pulls the current listings from GWU's public schedule.
2. **Upload a registrar spreadsheet.** Choose a registrar `.xlsx` schedule file (the *G&E Schedule* "Export" layout) to see it as a calendar.

The calendar opens in your browser. When you're done editing, click **📥 Export to Registrar (.xlsx)** in the Edit Schedule tab to download your changes in the registrar's format. This button only appears on the website.

Nothing you upload is stored. Each calendar is built in memory and sent straight back to you. The website uses Google Analytics to count visits.

---

## Option 2: Run the Desktop App

### Step 1: Install Python

#### **Windows Users**

1. Open the **Microsoft Store** (search for it in the Start menu)
2. Search for **"Python"**
3. Install **Python 3.12** (or the latest version)

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

Python is usually already installed. To check, open Terminal and type:
```bash
python3 --version
```
If you don't have it, install it with:
```bash
sudo apt install python3 python3-pip    # Ubuntu/Debian
sudo dnf install python3 python3-pip    # Fedora
```

### Step 2: Download This Project

![alt text](static/codebutton.png)
1. Click the green **"Code"** button at the top of this page
2. Click **"Download ZIP"**
3. Unzip the file to a folder on your computer (like your Desktop or Documents)

### Step 3: Run the Application

#### **Windows Users**

1. Open the folder where you unzipped the files
2. **Double-click** `launch_gui.bat`
3. If Windows shows a warning, choose to run it anyway
4. A window will open. That's the app!

#### **Mac/Linux Users**

1. Open **Terminal**
2. Go to the folder where you unzipped the files:
   ```bash
   cd ~/Desktop/GWU_Course_Calendar
   ```
   (Replace `~/Desktop/` with wherever you saved it)
3. Make the launcher executable (only needed once):
   ```bash
   chmod +x launch_gui.sh
   ```
4. Run the application:
   ```bash
   ./launch_gui.sh
   ```

The first run installs the packages the app needs. This only happens once.

### Using the Desktop App

1. **Year**: Enter the 4-digit year, such as 2026
2. **Semester**: Choose Spring 01, Summer 02 or Fall 03
3. **Subject Code**: Type the subject code, such as GEOG, CSCI, MATH or PSC
4. **Output File**: Optionally change the calendar's filename
5. Click **Scrape Courses**

The app shows its progress, saves the calendar as an HTML file, and opens it in your browser.

To work with a registrar spreadsheet instead, use the **Registrar Spreadsheet (.xlsx)** buttons:

- **📥 Import .xlsx → Calendar** loads a registrar schedule and shows it as a calendar.
- **📤 Export Calendar → .xlsx** writes the current schedule back out in the registrar's column layout.

The desktop app saves two files. `gwu_course_calendar.html` is the interactive calendar. It works offline and can be emailed or shared. `courses_data.json` holds the raw course data.

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

## The Calendar

The calendar has four tabs:

- **📅 All Courses**: The weekly grid. Filter by instructor, or show only some days.
- **📋 Class List**: Each instructor's schedule, for spotting double-bookings.
- **⚠️ Room Conflicts**: Courses booked in the same room at overlapping times. You can mark known conflicts as ignored, and your browser remembers that choice.
- **✏️ Edit Schedule**: Plan and change the schedule (see below).

---

## Edit Mode (For Department Admins)

![edit mode demo](static/editmode.gif)

1. Open the calendar and click the **✏️ Edit Schedule** tab
2. Make changes:
   - Click **➕ Add New Course** to create a course
   - Click any course block to edit it
   - In the edit window, use **📋 Duplicate** to make a new section, or **🗑️ Delete Course** to remove one
3. Save your work with one of the export buttons at the bottom

### What You Can Edit

- **Subject, course number and section**
- **CRN**
- **Title**: For special-topics courses, write it as `Course - Subtitle`, for example `Special Topics - Urban Heat`. The subtitle is exported to the registrar's Section Title column.
- **Credits**
- **Instructor**: Use `Last, F` format, for example `Chacko, E`
- **Days**: Tick any combination of Monday through Friday
- **Start and end time**: Chosen in 5-minute steps
- **Building and room**
- **Dates**: The semester date range, for example `01/12/26 - 04/27/26`

### Keeping Track of Changes

- A counter shows how many courses you've changed.
- Changed courses are highlighted, and their hover tooltip says **⚠️ Modified**.
- The **⚠️ Schedule Conflicts** list below the calendar updates as you edit.

### Saving Your Work

**Your edits live only in the open browser tab.** Closing or reloading the page loses them, so export before you leave.

- **📦 Export Schedule** downloads three files: an updated calendar (`.html`), a spreadsheet (`.csv`), and the raw data (`.json`). The `.html` file keeps working offline, Edit Mode included.
- **📥 Export to Registrar (.xlsx)** downloads the schedule in the registrar's format. This button only appears on the website.
- **📤 Import CSV** loads a `.csv` from a previous export, so you can pick up where you left off.

The CSV has these columns, sorted by instructor and then course number:

```csv
CRN, Subject, CourseNum, Section, Title, Credits, Instructor, Days, StartTime, EndTime, Building, Room, Dates
```

### Tips

- **Duplicate for efficiency**: Set up one section, duplicate it, then change only the section, time or room.
- **Check conflicts before exporting**: Review the conflicts list and the ⚠️ Room Conflicts tab.

---

## Registrar Spreadsheet Notes

The registrar import and export are **round-trip safe**. Registrar-only columns are kept, so a file you upload and download again loses nothing. Those columns are instructor GWID, enrollment counts, comments, special-topics section titles, and start and end dates.

- **Times** convert automatically between the registrar's 24-hour `HHMM` and the calendar's 12-hour display.
- **Arranged or TBA courses**, such as Thesis, Internship and Readings, have no meeting time. They are kept in the data and the export, but not drawn on the calendar.
- **Status** (Open or Closed) is worked out from enrollment versus capacity.
- **CRN, building and room** aren't in the registrar sheet. They show as *Not specified*, because rooms are assigned after this scheduling stage.
- **Changing a course's instructor** clears the old instructor's GWID in the export, since the ID belonged to the previous person.

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
- Check the subject code. It must be 2 to 5 letters, such as `PSC` or `GEOG`
- Check the semester and year. Courses may not be posted yet

### My edits disappeared

- Edits are kept only in the open browser tab. Use **📦 Export Schedule** or **📥 Export to Registrar (.xlsx)** before closing the page.

---

## For Developers

### Project Layout

- `app.py` - Flask web app behind courses.pygis.io
- `templates/` - Web app pages, including the shared Google Analytics snippet
- `gwu_scraper.py` - Scraper, calendar builder and command-line tool
- `registrar_io.py` - Registrar `.xlsx` reader and writer
- `gwu_scraper_gui.py` - Desktop app (Tkinter)
- `launch_gui.bat`, `launch_gui.sh` - Desktop launchers
- `Dockerfile` - Container image for Google Cloud Run
- `tests/` - Unit tests
- `.github/workflows/` - Continuous integration and deployment

### Command-Line Usage

```bash
# Default: scrape Geography courses
python gwu_scraper.py

# Scrape a specific subject
python gwu_scraper.py --url "https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=CSCI"

# Parse a saved page instead of fetching it
python gwu_scraper.py --text-file gwu_courses.html

# Custom output filenames
python gwu_scraper.py --output my_calendar.html --json my_data.json

# Import the registrar's .xlsx schedule instead of scraping
python gwu_scraper.py --xlsx-in "G&E Schedule - Spring 2027.xlsx"

# Export the schedule back to the registrar's .xlsx format
python gwu_scraper.py --xlsx-in schedule.xlsx --xlsx-out updated_schedule.xlsx

# Show all options
python gwu_scraper.py --help
```

### Running the Web App Locally

```bash
pip install -r requirements.txt
python app.py        # http://localhost:8080
```

Google Analytics is on by default. The measurement ID comes from the `GA_MEASUREMENT_ID` environment variable. Set it to an empty value to turn tracking off locally:

```bash
GA_MEASUREMENT_ID= python app.py
```

### Running the Tests

```bash
python -m unittest discover -s tests
```

The tests never touch the network. The Edit Mode tests run the calendar's own JavaScript in Node.js, and they are skipped if Node isn't installed.

### Deployment

The web app runs on Google Cloud Run as the `gwu-course-calendar` service in `us-east1`. The **Test and Deploy Web App** workflow handles it:

- **Pull requests into `main`** run the tests.
- **Merges into `main`** run the tests again. If they pass, the workflow builds the Docker image, deploys it to Cloud Run, and checks the site's `/health` endpoint.

GitHub signs in to Google Cloud with Workload Identity Federation, so no keys are stored in the repository. Only this repository's `main` branch can deploy.

To deploy by hand instead:

```bash
gcloud run deploy gwu-course-calendar --source . --region us-east1
```

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

This tool is provided as-is for educational purposes. Please use responsibly and in accordance with GWU's terms of service.

---

## Need Help?

1. Try the website first: <https://courses.pygis.io/>
2. Read the **Troubleshooting** section above
3. Use the **Report Issue** button in the desktop app, or open an issue on GitHub

**Have fun exploring GWU courses!** 🎓
