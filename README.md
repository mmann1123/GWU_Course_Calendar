# GWU Course Calendar Scraper

An interactive Python application that scrapes course data from GWU's schedule website and generates a beautiful Google Calendar-style weekly view.

![class scheduler demo](static/class_scheduler2.gif)

## Features

✅ **Web Scraping**: Automatically fetches course data from GWU's course schedule  
✅ **Interactive Calendar**: Google Calendar-style weekly view with click-to-view details  
✅ **Overlap Detection**: Automatically displays overlapping courses side-by-side  
✅ **Complete Data**: Shows CRN, instructor, time, location, credits, and status  
✅ **JSON Export**: Saves raw course data in JSON format for further analysis  
✅ **Cross-platform**: Works on Windows, Mac, and Linux  

## Requirements

- Python 3.7 or higher
- Required packages:
  ```bash
  pip install beautifulsoup4 requests
  ```

## Installation

1. Ensure Python 3 is installed on your system
2. Install required packages:
   ```bash
   pip install beautifulsoup4 requests
   ```
3. Download `gwu_scraper.py` to your computer

## Usage

### Basic Usage (Scrape from URL)

```bash
python gwu_scraper.py
```

This will scrape the default GWU Geography courses URL and generate:
- `gwu_course_calendar.html` - Interactive calendar
- `courses_data.json` - Raw course data in JSON format

### Custom URL

```bash
python gwu_scraper.py --url "https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=MATH"
```

### Parse from Text File

If you have already saved the course data to a text file:

```bash
python gwu_scraper.py --text-file my_courses.txt
```

### Custom Output Filenames

```bash
python gwu_scraper.py --output my_calendar.html --json my_data.json
```

### Help

```bash
python gwu_scraper.py --help
```

## Output Files

### gwu_course_calendar.html
An interactive HTML calendar that you can open in any web browser. Features:
- Weekly view with time slots from 9 AM to 9 PM
- Color-coded course blocks
- Click any course to see full details (CRN, instructor, room, etc.)
- Automatic handling of overlapping courses
- Responsive design

### courses_data.json
Raw course data in JSON format containing:
- Course status (OPEN/CLOSED/WAITLIST)
- CRN (Course Registration Number)
- Subject and section
- Title and credits
- Instructor name
- Meeting days and times
- Building and room (if available)
- Semester dates

## Creating an Executable

To create a standalone executable that doesn't require Python to be installed:

### Using PyInstaller

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Create the executable:
   ```bash
   pyinstaller --onefile --name "GWU-Course-Scraper" gwu_scraper.py
   ```

3. Find your executable in the `dist/` folder

### Using cx_Freeze (Alternative)

1. Install cx_Freeze:
   ```bash
   pip install cx_Freeze
   ```

2. Create a `setup.py` file:
   ```python
   from cx_Freeze import setup, Executable

   setup(
       name="GWU Course Scraper",
       version="1.0",
       description="Scrape and visualize GWU course schedules",
       executables=[Executable("gwu_scraper.py")]
   )
   ```

3. Build the executable:
   ```bash
   python setup.py build
   ```

## Examples

### Scrape Current Term Courses

```bash
# Geography courses
python gwu_scraper.py --url "https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=GEOG"

# Computer Science courses
python gwu_scraper.py --url "https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=CSCI" --output cs_calendar.html

# Mathematics courses
python gwu_scraper.py --url "https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=MATH" --output math_calendar.html
```

## How It Works

1. **Scraping**: The script fetches the HTML from the GWU course schedule website
2. **Parsing**: Uses regex patterns to extract course information (status, CRN, title, instructor, times, etc.)
3. **Processing**: Organizes courses by day and detects overlapping time slots
4. **Generation**: Creates an interactive HTML calendar with embedded JavaScript for interactivity
5. **Export**: Saves both the HTML calendar and raw JSON data

## Features of the Interactive Calendar

### Visual Features
- Clean, modern Google Calendar-style design
- Color-coded course blocks with gradient backgrounds
- Hover effects for better visibility
- Smooth animations and transitions

### Interactive Features
- Click any course block to open a detailed modal
- Modal shows: CRN, instructor, full title, times, location, credits, status
- Press ESC or click outside to close modal
- Statistics bar showing total courses and instructors

### Smart Layout
- Automatically detects overlapping courses
- Displays overlapping courses side-by-side
- Time slots from 9 AM to 9 PM
- Responsive grid layout

## Troubleshooting

### No Courses Found
- Check your internet connection
- Verify the URL is correct
- Ensure the term ID is current (format: YYYYMM where MM is 01 for Spring, 06 for Summer, 08 for Fall)

### Import Errors
- Make sure you've installed the required packages:
  ```bash
  pip install beautifulsoup4 requests
  ```

### Calendar Not Displaying Correctly
- Ensure you're opening the HTML file in a modern web browser (Chrome, Firefox, Safari, Edge)
- Check that the HTML file is not corrupted

## Customization

You can modify the calendar appearance by editing the `<style>` section in the generated HTML file. Key elements:
- `.course-block` - Course block styling
- `.calendar-header` - Calendar header colors
- `.modal-content` - Modal dialog styling

## Data Format

The JSON export follows this structure:
```json
{
  "status": "OPEN",
  "crn": "43716",
  "subject": "GEOG",
  "section": "10",
  "title": "Introduction to Human Geography",
  "credits": "3.00",
  "instructor": "Chacko, E",
  "days": "TR",
  "time": {
    "start": "02:20PM",
    "end": "03:35PM",
    "raw": "02:20PM - 03:35PM"
  },
  "dates": "01/12/26 - 04/27/26",
  "building": "Not specified",
  "room": "Not specified",
  "course_number": "GEOG 10"
}
```

## Version History

- **v1.0** (2025): Initial release
  - Web scraping functionality
  - Interactive calendar generation
  - JSON export
  - Overlap detection

## License

This tool is provided as-is for educational purposes. Please use responsibly and in accordance with GWU's terms of service.

## Support

For issues or questions:
1. Check this README for common solutions
2. Verify your Python version: `python --version`
3. Verify package installation: `pip list | grep beautifulsoup4`

## Credits

Created using:
- Python 3
- BeautifulSoup4 for HTML parsing
- Requests for HTTP requests
- Pure HTML/CSS/JavaScript for the calendar interface

---

**Note**: This scraper was designed for GWU's course schedule format as of Spring 2026. If the website structure changes, the regex patterns in the script may need to be updated.
