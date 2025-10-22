#!/usr/bin/env python3
"""
GWU Course Calendar Scraper - Enhanced Version
Scrapes course data from GWU's schedule website and generates an interactive calendar
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import json
import sys
import argparse
from datetime import datetime


class CourseScraper:
    def __init__(self, url: str = None, text_content: str = None):
        self.url = url
        self.text_content = text_content
        self.courses = []
        
    def parse_time(self, time_str: str) -> Optional[Dict[str, str]]:
        """Parse time string like '02:20PM - 03:35PM'"""
        if not time_str or 'ARR' in time_str:
            return None
            
        time_pattern = r'(\d{1,2}:\d{2}[AP]M)\s*-\s*(\d{1,2}:\d{2}[AP]M)'
        match = re.search(time_pattern, time_str)
        
        if match:
            return {
                'start': match.group(1),
                'end': match.group(2),
                'raw': f"{match.group(1)} - {match.group(2)}"
            }
        return None
    
    def parse_days(self, days_str: str) -> Optional[str]:
        """Parse days string like 'MW', 'TR', etc."""
        if not days_str:
            return None
        days = ''.join(c for c in days_str.strip() if c in 'MTWRF')
        return days if days else None
    
    def scrape(self) -> List[Dict]:
        """Scrape course data from URL or text content"""

        soup = None
        if self.text_content:
            print("Using provided text content")
            soup = BeautifulSoup(self.text_content, 'html.parser')
        elif self.url:
            print(f"Fetching data from: {self.url}")
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(self.url, timeout=30, headers=headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
            except Exception as e:
                print(f"❌ Error fetching URL: {e}")
                print("\n" + "="*70)
                print("💡 THE GWU WEBSITE REQUIRES AUTHENTICATION")
                print("="*70)
                print("\n📋 SOLUTION: Save the webpage manually and use --text-file\n")
                print("Step 1: Open this URL in your browser:")
                print(f"        {self.url}")
                print("\nStep 2: Log in to GWU if needed")
                print("\nStep 3: Save the page:")
                print("        Windows: Press Ctrl+S")
                print("        Mac: Press Cmd+S")
                print("        Save as: gwu_courses.html")
                print("\nStep 4: Run the scraper with your saved file:")
                print("        python gwu_scraper.py --text-file gwu_courses.html")
                print("\n" + "="*70)
                print("📄 See CANT_ACCESS_WEBSITE.md for detailed instructions")
                print("="*70)
                print("\n✅ GOOD NEWS: gwu_course_calendar.html is already generated!")
                print("   Just open that file in your browser to view the calendar.\n")
                return []
        else:
            raise ValueError("Must provide either URL or text content")

        # Parse HTML tables - GWU uses table structure with class="courseListing"
        course_tables = soup.find_all('table', class_='courseListing')

        for table in course_tables:
            # Find all course rows (main data row has class containing "crseRow1")
            rows = table.find_all('tr', class_=lambda x: x and 'crseRow1' in x)

            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 10:
                        continue

                    # Extract data from table cells
                    status = cells[0].get_text(strip=True)
                    crn = cells[1].get_text(strip=True)

                    # Subject and course number are in cell 2
                    subject_cell = cells[2]
                    subject = subject_cell.find('span', style=lambda x: x and 'font-weight:bold' in x)
                    subject = subject.get_text(strip=True) if subject else ''

                    # Course number (e.g., 1001, 1002)
                    course_link = subject_cell.find('a')
                    if course_link:
                        course_num_text = course_link.find('span')
                        course_num = course_num_text.get_text(strip=True) if course_num_text else ''
                    else:
                        course_num = ''

                    section = cells[3].get_text(strip=True)
                    title = cells[4].get_text(strip=True)
                    credits = cells[5].get_text(strip=True)
                    instructor = cells[6].get_text(strip=True)
                    building_room = cells[7].get_text(strip=True)
                    day_time = cells[8].get_text(strip=True)
                    dates = cells[9].get_text(strip=True)

                    # Parse day/time (format: "TR<br>02:20PM - 03:35PM")
                    day_time_parts = day_time.split('\n')
                    if len(day_time_parts) >= 2:
                        days = day_time_parts[0].strip()
                        time_str = day_time_parts[1].strip()
                    else:
                        # Try to extract from single line
                        match = re.search(r'([MTWRF]+).*?(\d{1,2}:\d{2}[AP]M\s*-\s*\d{1,2}:\d{2}[AP]M)', day_time)
                        if match:
                            days = match.group(1)
                            time_str = match.group(2)
                        else:
                            continue

                    time_info = self.parse_time(time_str)
                    days_info = self.parse_days(days)

                    if not time_info or not days_info:
                        continue

                    # Parse building and room
                    building = 'Not specified'
                    room = 'Not specified'
                    if building_room and building_room != 'Not specified':
                        # Building/room format: "1957 E B12" or just building code
                        parts = building_room.strip().split()
                        if len(parts) >= 2:
                            building = ' '.join(parts[:-1])
                            room = parts[-1]
                        else:
                            building = building_room

                    course = {
                        'status': status,
                        'crn': crn,
                        'subject': subject,
                        'section': section,
                        'title': title,
                        'credits': credits,
                        'instructor': instructor,
                        'days': days_info,
                        'time': time_info,
                        'dates': dates if dates else '01/12/26 - 04/27/26',
                        'building': building,
                        'room': room,
                        'course_number': f"{subject} {course_num}" if course_num else f"{subject} {section}"
                    }

                    self.courses.append(course)
                    print(f"✓ {course['course_number']}: {course['title'][:45]}... ({course['days']} {course['time']['raw']}) [CRN: {crn}]")

                except Exception as e:
                    # Skip rows that don't match expected format
                    continue

        print(f"\n{'='*70}")
        print(f"✅ Total courses scraped: {len(self.courses)}")
        print(f"{'='*70}")
        return self.courses
    
    def save_to_json(self, filename: str):
        """Save scraped courses to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.courses, f, indent=2)
        print(f"✓ Saved raw data to: {filename}")


def generate_html_calendar(courses: List[Dict], output_file: str):
    """Generate interactive HTML calendar"""
    
    courses_json = json.dumps(courses, ensure_ascii=False)
    
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GWU Courses - Spring 2026</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1a73e8 0%, #4285f4 100%); color: white; padding: 25px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
        .header p {{ font-size: 14px; opacity: 0.95; }}
        .stats {{ background-color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex; gap: 40px; }}
        .stats-item {{ color: #5f6368; font-size: 14px; }}
        .stats-number {{ font-size: 32px; font-weight: 700; color: #1a73e8; display: block; margin-bottom: 5px; }}
        .calendar-container {{ background-color: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow-x: auto; }}
        .calendar-header {{ display: grid; grid-template-columns: 80px repeat(5, minmax(180px, 1fr)); border-bottom: 2px solid #e0e0e0; background-color: #f8f9fa; position: sticky; top: 0; z-index: 10; }}
        .day-header {{ padding: 15px 10px; text-align: center; font-weight: 600; font-size: 14px; color: #3c4043; border-right: 1px solid #e0e0e0; }}
        .day-header:last-child {{ border-right: none; }}
        .calendar-body {{ display: grid; grid-template-columns: 80px repeat(5, minmax(180px, 1fr)); position: relative; }}
        .time-column {{ border-right: 2px solid #e0e0e0; background-color: #fafafa; }}
        .time-slot {{ height: 60px; padding: 8px; font-size: 12px; font-weight: 500; color: #70757a; text-align: right; border-bottom: 1px solid #f0f0f0; }}
        .day-column {{ border-right: 1px solid #e0e0e0; position: relative; min-height: 100%; }}
        .day-column:last-child {{ border-right: none; }}
        .hour-line {{ position: absolute; width: 100%; height: 1px; background-color: #f0f0f0; left: 0; }}
        .course-block {{ position: absolute; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 5px; padding: 8px; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.15); overflow: hidden; z-index: 1; border: 1px solid rgba(255,255,255,0.3); }}
        .course-block:hover {{ transform: translateY(-2px) scale(1.02); box-shadow: 0 6px 16px rgba(0,0,0,0.25); z-index: 100; }}
        .course-number {{ font-weight: 700; color: white; font-size: 11px; margin-bottom: 3px; text-shadow: 0 1px 2px rgba(0,0,0,0.2); }}
        .course-name {{ color: rgba(255,255,255,0.95); font-size: 10px; line-height: 1.3; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; }}
        .course-time {{ color: rgba(255,255,255,0.85); font-size: 9px; margin-top: 4px; font-weight: 600; }}
        .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); z-index: 1000; animation: fadeIn 0.2s; }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        .modal-content {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background-color: white; border-radius: 12px; padding: 30px; max-width: 550px; width: 90%; max-height: 85vh; overflow-y: auto; box-shadow: 0 10px 40px rgba(0,0,0,0.3); animation: slideIn 0.3s; }}
        @keyframes slideIn {{ from {{ transform: translate(-50%, -60%); opacity: 0; }} to {{ transform: translate(-50%, -50%); opacity: 1; }} }}
        .modal-header {{ margin-bottom: 25px; padding-bottom: 20px; border-bottom: 2px solid #e0e0e0; }}
        .status-badge {{ display: inline-block; padding: 5px 12px; border-radius: 5px; font-size: 12px; font-weight: 600; margin-bottom: 12px; }}
        .status-open {{ background-color: #d4edda; color: #155724; }}
        .status-closed, .status-waitlist {{ background-color: #f8d7da; color: #721c24; }}
        .modal-course-number {{ font-size: 15px; color: #667eea; font-weight: 700; margin-bottom: 8px; }}
        .modal-course-name {{ font-size: 22px; font-weight: 700; color: #202124; line-height: 1.3; }}
        .modal-body {{ margin-bottom: 20px; }}
        .detail-row {{ display: flex; margin-bottom: 16px; align-items: flex-start; }}
        .detail-label {{ font-weight: 600; color: #5f6368; min-width: 120px; font-size: 14px; }}
        .detail-value {{ color: #202124; font-size: 14px; flex: 1; line-height: 1.5; }}
        .close-btn {{ position: absolute; top: 20px; right: 20px; font-size: 28px; color: #5f6368; cursor: pointer; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border-radius: 50%; transition: background-color 0.2s; }}
        .close-btn:hover {{ background-color: #f1f3f4; }}
        .legend {{ margin-top: 20px; padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .legend-title {{ font-weight: 700; margin-bottom: 12px; color: #202124; font-size: 16px; }}
        .legend-item {{ display: block; margin-bottom: 8px; font-size: 13px; color: #5f6368; line-height: 1.6; }}
        .color-box {{ display: inline-block; width: 18px; height: 18px; border-radius: 4px; margin-right: 8px; vertical-align: middle; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🗓️ GWU Courses - Spring 2026</h1>
        <p>Interactive Course Schedule | Scraped from GWU website on {datetime.now().strftime("%B %d, %Y")}</p>
    </div>

    <div class="stats">
        <div class="stats-item"><span class="stats-number" id="totalCourses">0</span><span>Total Courses</span></div>
        <div class="stats-item"><span class="stats-number" id="totalInstructors">0</span><span>Instructors</span></div>
    </div>

    <div class="calendar-container">
        <div class="calendar-header">
            <div class="day-header" style="background-color: white;"></div>
            <div class="day-header">Monday</div>
            <div class="day-header">Tuesday</div>
            <div class="day-header">Wednesday</div>
            <div class="day-header">Thursday</div>
            <div class="day-header">Friday</div>
        </div>

        <div class="calendar-body">
            <div class="time-column" id="timeColumn"></div>
            <div class="day-column" id="monday"></div>
            <div class="day-column" id="tuesday"></div>
            <div class="day-column" id="wednesday"></div>
            <div class="day-column" id="thursday"></div>
            <div class="day-column" id="friday"></div>
        </div>
    </div>

    <div class="legend">
        <div class="legend-title">📋 How to Use</div>
        <div class="legend-item"><span class="color-box"></span><strong>Click</strong> any course to view details (CRN, instructor, location)</div>
        <div class="legend-item">• <strong>Overlapping courses</strong> are displayed side-by-side</div>
        <div class="legend-item">• <strong>Hover</strong> over courses for better visibility</div>
    </div>

    <div id="modal" class="modal">
        <div class="modal-content">
            <span class="close-btn" onclick="closeModal()">&times;</span>
            <div class="modal-header">
                <div id="statusBadge"></div>
                <div class="modal-course-number" id="modalCourseNumber"></div>
                <div class="modal-course-name" id="modalCourseName"></div>
            </div>
            <div class="modal-body">
                <div class="detail-row"><div class="detail-label">CRN:</div><div class="detail-value" id="modalCRN"></div></div>
                <div class="detail-row"><div class="detail-label">Instructor:</div><div class="detail-value" id="modalInstructor"></div></div>
                <div class="detail-row"><div class="detail-label">Meeting Time:</div><div class="detail-value" id="modalTime"></div></div>
                <div class="detail-row"><div class="detail-label">Days:</div><div class="detail-value" id="modalDays"></div></div>
                <div class="detail-row"><div class="detail-label">Building:</div><div class="detail-value" id="modalBuilding"></div></div>
                <div class="detail-row"><div class="detail-label">Room:</div><div class="detail-value" id="modalRoom"></div></div>
                <div class="detail-row"><div class="detail-label">Credits:</div><div class="detail-value" id="modalCredits"></div></div>
                <div class="detail-row"><div class="detail-label">Semester:</div><div class="detail-value" id="modalDates"></div></div>
            </div>
        </div>
    </div>

    <script>
        const courses = {courses_json};
        const dayMap = {{ 'M': 'monday', 'T': 'tuesday', 'W': 'wednesday', 'R': 'thursday', 'F': 'friday' }};

        function timeToMinutes(timeStr) {{
            const match = timeStr.match(/(\\d{{1,2}}):(\\d{{2}})([AP]M)/);
            if (!match) return 0;
            let hours = parseInt(match[1]);
            const minutes = parseInt(match[2]);
            const period = match[3];
            if (period === 'PM' && hours !== 12) hours += 12;
            if (period === 'AM' && hours === 12) hours = 0;
            return hours * 60 + minutes;
        }}

        function createTimeSlots() {{
            const timeColumn = document.getElementById('timeColumn');
            const startHour = 9;
            const endHour = 21;
            for (let hour = startHour; hour <= endHour; hour++) {{
                const timeSlot = document.createElement('div');
                timeSlot.className = 'time-slot';
                const displayHour = hour > 12 ? hour - 12 : (hour === 0 ? 12 : hour);
                const period = hour >= 12 ? 'PM' : 'AM';
                timeSlot.textContent = `${{displayHour}}:00 ${{period}}`;
                timeColumn.appendChild(timeSlot);
            }}
            ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'].forEach(day => {{
                const dayColumn = document.getElementById(day);
                for (let i = 0; i <= endHour - startHour; i++) {{
                    const line = document.createElement('div');
                    line.className = 'hour-line';
                    line.style.top = `${{i * 60}}px`;
                    dayColumn.appendChild(line);
                }}
            }});
        }}

        function renderCourses() {{
            const startHour = 9;
            const pixelsPerMinute = 1;
            document.getElementById('totalCourses').textContent = courses.length;
            const instructors = new Set(courses.map(c => c.instructor));
            document.getElementById('totalInstructors').textContent = instructors.size;
            const coursesByDay = {{ monday: [], tuesday: [], wednesday: [], thursday: [], friday: [] }};
            courses.forEach(course => {{
                course.days.split('').forEach(day => {{
                    const dayId = dayMap[day];
                    if (dayId) coursesByDay[dayId].push(course);
                }});
            }});
            Object.keys(coursesByDay).forEach(dayId => {{
                const dayColumn = document.getElementById(dayId);
                const coursesForDay = coursesByDay[dayId];
                coursesForDay.sort((a, b) => timeToMinutes(a.time.start) - timeToMinutes(b.time.start));
                const processed = new Set();
                coursesForDay.forEach((course, index) => {{
                    if (processed.has(index)) return;
                    const startMinutes = timeToMinutes(course.time.start);
                    const endMinutes = timeToMinutes(course.time.end);
                    const duration = endMinutes - startMinutes;
                    const topPosition = (startMinutes - (startHour * 60)) * pixelsPerMinute;
                    const height = duration * pixelsPerMinute;
                    const overlapping = [];
                    for (let i = index + 1; i < coursesForDay.length; i++) {{
                        if (processed.has(i)) continue;
                        const other = coursesForDay[i];
                        const otherStart = timeToMinutes(other.time.start);
                        const otherEnd = timeToMinutes(other.time.end);
                        if (startMinutes < otherEnd && endMinutes > otherStart) {{
                            overlapping.push({{course: other, index: i}});
                        }}
                    }}
                    const totalOverlapping = overlapping.length + 1;
                    const widthPercent = 100 / totalOverlapping;
                    renderCourseBlock(course, dayColumn, topPosition, height, 0, widthPercent);
                    processed.add(index);
                    overlapping.forEach((item, i) => {{
                        const otherStartMinutes = timeToMinutes(item.course.time.start);
                        const otherEndMinutes = timeToMinutes(item.course.time.end);
                        const otherDuration = otherEndMinutes - otherStartMinutes;
                        const otherTopPosition = (otherStartMinutes - (startHour * 60)) * pixelsPerMinute;
                        const otherHeight = otherDuration * pixelsPerMinute;
                        renderCourseBlock(item.course, dayColumn, otherTopPosition, otherHeight, i + 1, widthPercent);
                        processed.add(item.index);
                    }});
                }});
            }});
        }}

        function renderCourseBlock(course, dayColumn, topPosition, height, column, widthPercent) {{
            const courseBlock = document.createElement('div');
            courseBlock.className = 'course-block';
            courseBlock.style.top = `${{topPosition}}px`;
            courseBlock.style.height = `${{height}}px`;
            courseBlock.style.left = `${{column * widthPercent}}%`;
            courseBlock.style.width = `calc(${{widthPercent}}% - 4px)`;
            courseBlock.innerHTML = `
                <div class="course-number">${{course.course_number}}</div>
                <div class="course-name">${{course.title}}</div>
                <div class="course-time">${{course.time.start}}</div>
            `;
            courseBlock.onclick = () => showModal(course);
            dayColumn.appendChild(courseBlock);
        }}

        function showModal(course) {{
            const statusBadge = document.getElementById('statusBadge');
            const statusClass = course.status === 'OPEN' ? 'status-open' : 'status-closed';
            statusBadge.className = 'status-badge ' + statusClass;
            statusBadge.textContent = course.status;
            document.getElementById('modalCourseNumber').textContent = course.course_number;
            document.getElementById('modalCourseName').textContent = course.title;
            document.getElementById('modalCRN').textContent = course.crn;
            document.getElementById('modalInstructor').textContent = course.instructor;
            document.getElementById('modalTime').textContent = course.time.raw;
            document.getElementById('modalDays').textContent = expandDays(course.days);
            document.getElementById('modalBuilding').textContent = course.building;
            document.getElementById('modalRoom').textContent = course.room;
            document.getElementById('modalCredits').textContent = course.credits;
            document.getElementById('modalDates').textContent = course.dates;
            document.getElementById('modal').style.display = 'block';
        }}

        function closeModal() {{
            document.getElementById('modal').style.display = 'none';
        }}

        function expandDays(days) {{
            const dayNames = {{ 'M': 'Monday', 'T': 'Tuesday', 'W': 'Wednesday', 'R': 'Thursday', 'F': 'Friday' }};
            return days.split('').map(d => dayNames[d]).join(', ');
        }}

        window.onclick = function(event) {{
            if (event.target === document.getElementById('modal')) closeModal();
        }}

        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') closeModal();
        }});

        createTimeSlots();
        renderCourses();
    </script>
</body>
</html>'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"✓ Calendar saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='GWU Course Calendar Scraper',
        epilog='Example: python gwu_scraper.py --url "https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=CSCI"'
    )
    parser.add_argument('--url', type=str, 
                       default="https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=GEOG",
                       help='URL to scrape')
    parser.add_argument('--text-file', type=str, help='Text file to parse instead of URL')
    parser.add_argument('--output', type=str, default='gwu_course_calendar.html',
                       help='Output HTML file')
    parser.add_argument('--json', type=str, default='courses_data.json',
                       help='Output JSON file')
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print(" "*18 + "🎓 GWU COURSE CALENDAR SCRAPER")
    print("="*70 + "\n")
    
    try:
        if args.text_file:
            with open(args.text_file, 'r', encoding='utf-8') as f:
                text_content = f.read()
            scraper = CourseScraper(text_content=text_content)
        else:
            scraper = CourseScraper(url=args.url)
        
        print("Starting scrape...\n")
        courses = scraper.scrape()
        
        if len(courses) == 0:
            print("\n⚠️  WARNING: No courses found!")
            print("   Try saving the webpage and using --text-file")
            return 1
        
        print()
        scraper.save_to_json(args.json)
        generate_html_calendar(courses, args.output)
        
        print("\n" + "="*70)
        print("✅ SUCCESS!")
        print(f"   📊 {len(courses)} courses")
        print(f"   📅 {args.output}")
        print("="*70 + "\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
