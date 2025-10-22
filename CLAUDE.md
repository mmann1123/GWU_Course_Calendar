# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a single-file Python web scraper that fetches GWU course schedule data and generates an interactive HTML calendar with a Google Calendar-style interface. The scraper uses regex-based parsing to extract course information from GWU's course schedule website and creates a standalone HTML file with embedded JavaScript for interactivity.

## Common Commands

### Running the Scraper

```bash
# Default: Scrape Geography courses for current term
python gwu_scraper.py

# Scrape specific subject (change subjId parameter)
python gwu_scraper.py --url "https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=CSCI"

# Parse from saved HTML file (useful when authentication required)
python gwu_scraper.py --text-file gwu_courses.html

# Custom output filenames
python gwu_scraper.py --output my_calendar.html --json my_data.json

# Show help and all options
python gwu_scraper.py --help
```

### Installing Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Or use automated scripts
./run_scraper.sh      # Linux/Mac
run_scraper.bat       # Windows
```

### Testing the Installation

```bash
# Verify packages are installed
pip list | grep beautifulsoup4

# Test scraper (should show help)
python gwu_scraper.py --help
```

## Architecture

### Single-File Design

The entire application is in `gwu_scraper.py` with three main components:

1. **CourseScraper class** - Handles web scraping and data extraction
   - `detect_total_pages()` - Finds number of result pages
   - `parse_page_html()` - Parses courses from a single page
   - `scrape()` - Main method that orchestrates pagination
2. **generate_html_calendar() function** - Creates standalone HTML calendar
3. **main() function** - CLI argument parsing and orchestration

### Data Flow

```
URL/HTML File → CourseScraper.scrape() → Course dictionaries → JSON export
                                                              ↓
                                                    generate_html_calendar()
                                                              ↓
                                                    Interactive HTML file
```

### Course Data Structure

Each course is represented as a dictionary:

```python
{
    'status': 'OPEN',           # OPEN, CLOSED, or WAITLIST
    'crn': '43716',             # Course Registration Number
    'subject': 'GEOG',          # Subject code
    'section': '10',            # Section number
    'title': 'Introduction to Human Geography',
    'credits': '3.00',
    'instructor': 'Chacko, E',  # Last name, First initial
    'days': 'TR',               # M, T, W, R, F combinations
    'time': {
        'start': '02:20PM',
        'end': '03:35PM',
        'raw': '02:20PM - 03:35PM'
    },
    'dates': '01/12/26 - 04/27/26',
    'building': 'Not specified',
    'room': 'Not specified',
    'course_number': 'GEOG 10'
}
```

## Parsing Strategy

### HTML Table Parsing with Pagination

The scraper automatically handles multi-page results:

1. **Detect pagination**: Searches for `goToPage('N')` JavaScript calls to find total pages
2. **Fetch all pages**: Loops through pages using `&pageNum=2`, `&pageNum=3`, etc.
3. **Parse tables**: For each page, finds tables with class `courseListing`
4. **Extract rows**: Finds rows with class containing `crseRow1`
5. **Combine results**: Aggregates courses from all pages into single list

### Pagination Implementation

```python
# Detect total pages from first page HTML
total_pages = self.detect_total_pages(response.text)

# Fetch remaining pages
for page_num in range(2, total_pages + 1):
    page_url = f"{self.url}&pageNum={page_num}"
    # Parse and add to courses list
```

**Example**: GEOG has 3 pages (32 + 31 + 18 = 81 courses total)

### Table Cell Structure

| Cell Index | Content | Example |
|------------|---------|---------|
| 0 | Status | OPEN, CLOSED, WAITLIST |
| 1 | CRN | 46234 |
| 2 | Subject & Course # | GEOG 1001 (with nested spans/links) |
| 3 | Section | 10 |
| 4 | Title | Introduction to Human Geography |
| 5 | Credits | 3.00 |
| 6 | Instructor | Chacko, E |
| 7 | Building/Room | 1957 E B12 |
| 8 | Day/Time | TR<br>02:20PM - 03:35PM |
| 9 | Date Range | 01/12/26 - 04/27/26 |

### Key Parsing Details

**Subject and Course Number (Cell 2)**:
```python
# Cell 2 has nested structure:
# <span style="font-weight:bold;">GEOG</span>
# <a><span>1001</span></a>
subject = subject_cell.find('span', style=lambda x: x and 'font-weight:bold' in x)
course_num = subject_cell.find('a').find('span')
```

**Day/Time Parsing (Cell 8)**:
```python
# Format: "TR\n02:20PM - 03:35PM" (newline-separated)
# Split on newline, extract days and time separately
day_time_parts = day_time.split('\n')
days = day_time_parts[0].strip()  # "TR"
time_str = day_time_parts[1].strip()  # "02:20PM - 03:35PM"
```

**Building/Room Parsing (Cell 7)**:
```python
# Format: "1957 E B12" → building="1957 E", room="B12"
# Last token is room, everything else is building
```

### Time Parsing

Times are converted to minutes since midnight for positioning:

```python
# "02:20PM" → 14*60 + 20 = 860 minutes
# Used for: calculating course block positions, detecting overlaps
```

## Calendar Generation

### HTML Template Structure

The generated HTML is a complete standalone file with:

- **CSS**: Embedded styles for Google Calendar-like appearance
- **JavaScript**: Client-side rendering logic (no server needed)
- **Data**: JSON array of courses embedded in `<script>` tag

### Layout Algorithm

The calendar uses a grid-based layout:

1. **Time slots**: 9 AM to 9 PM (12 hours = 720 minutes)
2. **Pixel calculation**: 1 pixel per minute (scalable via `pixelsPerMinute`)
3. **Position**: `top = (course_start_minutes - 540) * pixelsPerMinute`
4. **Height**: `height = (end_minutes - start_minutes) * pixelsPerMinute`

### Overlap Detection

When multiple courses meet at overlapping times on the same day:

1. Sort courses by start time
2. For each course, find all courses with overlapping time ranges
3. Calculate: `width = 100% / number_of_overlapping_courses`
4. Position each course horizontally: `left = column_index * width`

Example:
- Course A: 2:00-3:15 PM
- Course B: 2:20-3:35 PM
- Both rendered at 50% width, positioned side-by-side

## GWU URL Format

### Course Schedule URL Structure

```
https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=GEOG
                                        ↑         ↑            ↑
                                     Campus     Term       Subject
```

**Parameters:**
- `campId=1`: Main campus (usually always 1)
- `termId=YYYYMM`: Year + month code
  - `01` = Spring semester
  - `06` = Summer semester
  - `08` = Fall semester
  - Example: `202601` = Spring 2026
- `subjId=XXXX`: Subject code (GEOG, CSCI, MATH, BADM, etc.)

### Common Subject Codes

- `GEOG` - Geography
- `CSCI` - Computer Science
- `MATH` - Mathematics
- `BADM` - Business Administration
- `PSYC` - Psychology
- `ECON` - Economics
- `PSC` - Political Science

## Authentication and Access

### Public Access

As of 2025-2026, GWU's course schedule website is publicly accessible and does not require authentication for most subjects. The scraper should work directly with URLs.

### If Authentication Issues Occur

If you encounter 401/403 errors in the future (authentication required):

1. Open URL in browser
2. Log in to GWU portal
3. Save page as HTML (Ctrl+S / Cmd+S)
4. Run: `python gwu_scraper.py --text-file gwu_courses.html`

The scraper detects failed requests and prints detailed instructions for this workflow.

## Output Files

### gwu_course_calendar.html

Interactive calendar with:
- Click-to-view course details in modal
- Automatic overlap handling
- Responsive design
- No external dependencies (works offline)

### courses_data.json

Raw JSON array of all courses for:
- Data analysis
- Integration with other tools
- Backup/archival

## Modifying the Scraper

### Updating HTML Table Parsing

If GWU changes their HTML format, key areas to update:

1. **Pagination detection** (gwu_scraper.py:23-28): Regex pattern `goToPage\('(\d+)'\)`
2. **Table class name** (gwu_scraper.py:58): `soup.find_all('table', class_='courseListing')`
3. **Row class name** (gwu_scraper.py:62): `class_=lambda x: x and 'crseRow1' in x`
4. **Cell structure** (gwu_scraper.py:66-122): Adjust cell indices if table columns change
5. **Subject/course parsing** (gwu_scraper.py:75-85): If nested span/link structure changes

To debug parsing issues:
- Save HTML: `wget -O test.html "URL"` or save via browser
- Inspect table structure in browser DevTools
- Test with saved file: `python gwu_scraper.py --text-file test.html`
- Check pagination: Look for "Result Page:" section and `goToPage()` JavaScript calls

### Adjusting Calendar Appearance

Key CSS selectors in the HTML template (gwu_scraper.py:143-186):
- `.course-block` - Course block styling
- `.calendar-header` - Header colors/fonts
- `.modal-content` - Modal dialog appearance

### Modifying Time Range

Change `startHour` and `endHour` in JavaScript (gwu_scraper.py:264-265):
```javascript
const startHour = 9;   // 9 AM
const endHour = 21;    // 9 PM
```

## Dependencies

- `beautifulsoup4>=4.9.0` - HTML parsing (BeautifulSoup)
- `requests>=2.25.0` - HTTP requests

Both are lightweight and widely used. The scraper uses BeautifulSoup primarily for `.get_text()` extraction, then relies on regex for parsing (not DOM traversal).
