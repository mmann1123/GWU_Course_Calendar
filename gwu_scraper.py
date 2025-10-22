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
        self.courses_by_crn = {}  # Track by CRN for deduplication

    def detect_total_pages(self, html_content: str) -> int:
        """Detect total number of pages from pagination links"""
        page_nums = re.findall(r"goToPage\('(\d+)'\)", html_content)
        if page_nums:
            return max(map(int, page_nums))
        return 1
        
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
    
    def parse_page_html(self, soup: BeautifulSoup, page_num: int = 1) -> int:
        """Parse a single page of HTML and add courses to self.courses. Returns number of courses found."""
        courses_found = 0

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

                    # Parse building/room using HTML structure
                    # Building is in a link (<a> tag), room is plain text
                    building = 'Not specified'
                    room = 'Not specified'
                    building_room_cell = cells[7]

                    # Try to find building link
                    building_link = building_room_cell.find('a')
                    if building_link:
                        building = building_link.get_text(strip=True)
                        # Get all text from cell, then remove the building part to get room
                        full_text = building_room_cell.get_text(strip=True)
                        # Remove building from full text to get room
                        room_text = full_text.replace(building, '').strip()
                        if room_text:
                            room = room_text
                    else:
                        # No link found, fallback to old parsing method
                        building_room = building_room_cell.get_text(strip=True)
                        if building_room and building_room != 'Not specified':
                            parts = building_room.strip().split()
                            if len(parts) >= 2:
                                building = ' '.join(parts[:-1])
                                room = parts[-1]
                            else:
                                building = building_room

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

                    # Deduplication: prefer courses with subject code over those without
                    if crn in self.courses_by_crn:
                        existing = self.courses_by_crn[crn]
                        # Always prefer the version with a subject code (GEOG 6306 > 6306)
                        has_subject_new = bool(subject and subject.strip())
                        has_subject_existing = bool(existing['subject'] and existing['subject'].strip())

                        if has_subject_new and not has_subject_existing:
                            # New has subject, existing doesn't - replace
                            self.courses_by_crn[crn] = course
                            print(f"✓ {course['course_number']}: {course['title'][:45]}... ({course['days']} {course['time']['raw']}) [CRN: {crn}] (replaced duplicate)")
                        elif has_subject_existing and not has_subject_new:
                            # Existing has subject, new doesn't - keep existing
                            print(f"  ↳ Skipped duplicate CRN {crn}: {course['course_number']} (keeping {existing['course_number']})")
                        else:
                            # Both have subject or both don't - keep first one
                            print(f"  ↳ Skipped duplicate CRN {crn}: {course['course_number']}")
                    else:
                        # New CRN, add it
                        self.courses_by_crn[crn] = course
                        courses_found += 1
                        print(f"✓ {course['course_number']}: {course['title'][:45]}... ({course['days']} {course['time']['raw']}) [CRN: {crn}]")

                except Exception as e:
                    # Skip rows that don't match expected format
                    continue

        return courses_found

    def scrape(self) -> List[Dict]:
        """Scrape course data from URL or text content"""

        if self.text_content:
            print("Using provided text content")
            soup = BeautifulSoup(self.text_content, 'html.parser')
            self.parse_page_html(soup)
            # Convert deduplicated courses to list
            self.courses = list(self.courses_by_crn.values())
            print(f"\n{'='*70}")
            print(f"✅ Total courses scraped: {len(self.courses)} (after deduplication)")
            print(f"{'='*70}")
            return self.courses

        elif self.url:
            print(f"Fetching data from: {self.url}")
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }

                # Fetch first page
                response = requests.get(self.url, timeout=30, headers=headers)
                response.raise_for_status()

                # Detect total pages
                total_pages = self.detect_total_pages(response.text)
                if total_pages > 1:
                    print(f"📄 Found {total_pages} pages of results")

                # Parse first page
                soup = BeautifulSoup(response.text, 'html.parser')
                count = self.parse_page_html(soup, page_num=1)
                if total_pages > 1:
                    print(f"   → Page 1: {count} courses")

                # Fetch remaining pages
                for page_num in range(2, total_pages + 1):
                    page_url = f"{self.url}&pageNum={page_num}"
                    print(f"\nFetching page {page_num}...")
                    response = requests.get(page_url, timeout=30, headers=headers)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    count = self.parse_page_html(soup, page_num=page_num)
                    print(f"   → Page {page_num}: {count} courses")

                # Convert deduplicated courses to list
                self.courses = list(self.courses_by_crn.values())
                print(f"\n{'='*70}")
                print(f"✅ Total courses scraped: {len(self.courses)} (after deduplication)")
                print(f"{'='*70}")
                return self.courses

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
    
    def save_to_json(self, filename: str):
        """Save scraped courses to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.courses, f, indent=2)
        print(f"✓ Saved raw data to: {filename}")


def generate_html_calendar(courses: List[Dict], output_file: str, year: str = None, semester: str = None):
    """Generate interactive HTML calendar"""

    courses_json = json.dumps(courses, ensure_ascii=False)

    # Generate dynamic title
    semester_map = {
        '01': 'Spring',
        '02': 'Summer',
        '03': 'Fall'
    }

    if year and semester:
        semester_name = semester_map.get(semester, 'Unknown')
        title = f"GWU Courses - {semester_name} {year}"
    else:
        title = "GWU Courses"

    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; padding: 0; }}
        .main-content {{ padding: 20px; }}

        /* Read the Docs style navigation */
        .rtd-navbar {{ background-color: #2980b9; color: white; padding: 0 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); position: sticky; top: 0; z-index: 1000; }}
        .rtd-navbar-content {{ display: flex; justify-content: space-between; align-items: center; max-width: 1400px; margin: 0 auto; height: 50px; }}
        .rtd-navbar-left {{ display: flex; align-items: center; gap: 20px; }}
        .rtd-navbar-title {{ font-size: 18px; font-weight: 600; color: white; text-decoration: none; display: flex; align-items: center; gap: 8px; }}
        .rtd-navbar-right {{ display: flex; align-items: center; gap: 15px; }}
        .rtd-nav-link {{ color: rgba(255,255,255,0.9); text-decoration: none; font-size: 14px; font-weight: 500; padding: 8px 14px; border-radius: 5px; transition: all 0.2s; display: flex; align-items: center; gap: 6px; }}
        .rtd-nav-link:hover {{ background-color: rgba(255,255,255,0.15); color: white; }}
        .github-icon {{ width: 20px; height: 20px; fill: currentColor; }}

        /* Footer */
        .rtd-footer {{ background-color: #343131; color: #d9d9d9; padding: 30px 20px; margin-top: 40px; border-top: 4px solid #2980b9; }}
        .rtd-footer-content {{ max-width: 1400px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px; }}
        .rtd-footer-left {{ font-size: 13px; }}
        .rtd-footer-links {{ display: flex; gap: 20px; }}
        .rtd-footer-link {{ color: #2980b9; text-decoration: none; font-size: 14px; font-weight: 500; display: flex; align-items: center; gap: 6px; transition: all 0.2s; }}
        .rtd-footer-link:hover {{ color: #5dade2; }}
        .rtd-footer-attribution {{ margin-top: 15px; padding-top: 15px; border-top: 1px solid #4a4a4a; text-align: center; font-size: 12px; color: #999; }}
        .header {{ background: linear-gradient(135deg, #1a73e8 0%, #4285f4 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(26,115,232,0.3); }}
        .header h1 {{ font-size: 30px; margin-bottom: 10px; font-weight: 700; letter-spacing: -0.5px; }}
        .header p {{ font-size: 14px; opacity: 0.92; font-weight: 400; }}
        .stats {{ background-color: white; padding: 24px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); display: flex; gap: 50px; }}
        .stats-item {{ color: #5f6368; font-size: 14px; font-weight: 500; }}
        .stats-number {{ font-size: 36px; font-weight: 700; background: linear-gradient(135deg, #1a73e8 0%, #4285f4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: block; margin-bottom: 5px; }}
        .calendar-container {{ background-color: white; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); overflow-x: auto; }}
        .calendar-header {{ display: grid; grid-template-columns: 80px repeat(5, minmax(180px, 1fr)); border-bottom: 2px solid #e0e0e0; background-color: #f8f9fa; position: sticky; top: 0; z-index: 10; }}
        .day-header {{ padding: 15px 10px; text-align: center; font-weight: 600; font-size: 14px; color: #3c4043; border-right: 1px solid #e0e0e0; cursor: pointer; transition: all 0.2s ease; }}
        .day-header:hover {{ background-color: #e3f2fd; color: #1a73e8; }}
        .day-header.active {{ background-color: #1a73e8; color: white; }}
        .day-header:last-child {{ border-right: none; }}
        .filter-controls {{ background-color: white; padding: 18px 24px; margin-bottom: 10px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }}
        .filter-btn {{ padding: 9px 18px; border: 1px solid #1a73e8; background-color: white; color: #1a73e8; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 600; transition: all 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
        .filter-btn:hover {{ background-color: #1a73e8; color: white; transform: translateY(-1px); box-shadow: 0 3px 8px rgba(26,115,232,0.25); }}
        .filter-btn:active {{ transform: translateY(0); }}
        .filter-text {{ color: #5f6368; font-size: 14px; font-weight: 500; }}
        .calendar-body {{ display: grid; grid-template-columns: 80px repeat(5, minmax(180px, 1fr)); position: relative; }}
        .time-column {{ border-right: 2px solid #e0e0e0; background-color: #fafafa; }}
        .time-slot {{ height: 60px; padding: 8px; font-size: 12px; font-weight: 500; color: #70757a; text-align: right; border-bottom: 1px solid #f0f0f0; }}
        .day-column {{ border-right: 1px solid #e0e0e0; position: relative; min-height: 100%; }}
        .day-column:last-child {{ border-right: none; }}
        .hour-line {{ position: absolute; width: 100%; height: 1px; background-color: #f0f0f0; left: 0; }}
        .course-block {{ position: absolute; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 5px; padding: 8px; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.15); overflow: visible; z-index: 1; border: 1px solid rgba(255,255,255,0.3); }}
        .course-block:hover {{ transform: translateY(-2px) scale(1.02); box-shadow: 0 6px 16px rgba(0,0,0,0.25); z-index: 100; }}
        .course-block:hover .tooltip {{ visibility: visible; opacity: 1; }}
        .tooltip {{ visibility: hidden; opacity: 0; position: absolute; left: 105%; top: 0; background-color: #2d2d2d; color: white; padding: 12px 15px; border-radius: 8px; font-size: 12px; white-space: nowrap; z-index: 1000; box-shadow: 0 4px 12px rgba(0,0,0,0.3); transition: opacity 0.3s, visibility 0.3s; pointer-events: none; }}
        .tooltip::before {{ content: ''; position: absolute; right: 100%; top: 15px; border: 6px solid transparent; border-right-color: #2d2d2d; }}
        .tooltip-row {{ margin-bottom: 6px; }}
        .tooltip-row:last-child {{ margin-bottom: 0; }}
        .tooltip-label {{ font-weight: 600; color: #a0a0a0; display: inline-block; min-width: 80px; }}
        .tooltip-value {{ color: white; }}
        .course-number {{ font-weight: 700; color: white; font-size: 11px; margin-bottom: 3px; text-shadow: 0 1px 2px rgba(0,0,0,0.2); }}
        .course-name {{ color: rgba(255,255,255,0.95); font-size: 10px; line-height: 1.3; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; }}
        .course-time {{ color: rgba(255,255,255,0.85); font-size: 9px; margin-top: 4px; font-weight: 600; }}
        .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.6); z-index: 1000; animation: fadeIn 0.2s; backdrop-filter: blur(2px); }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        .modal-content {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background-color: white; border-radius: 16px; padding: 32px; max-width: 580px; width: 90%; max-height: 85vh; overflow-y: auto; box-shadow: 0 12px 48px rgba(0,0,0,0.25), 0 4px 16px rgba(0,0,0,0.12); animation: slideIn 0.3s; }}
        @keyframes slideIn {{ from {{ transform: translate(-50%, -55%); opacity: 0; }} to {{ transform: translate(-50%, -50%); opacity: 1; }} }}
        .modal-content::-webkit-scrollbar {{ width: 8px; }}
        .modal-content::-webkit-scrollbar-track {{ background: #f1f3f4; border-radius: 4px; }}
        .modal-content::-webkit-scrollbar-thumb {{ background: #dadce0; border-radius: 4px; }}
        .modal-content::-webkit-scrollbar-thumb:hover {{ background: #bdc1c6; }}
        .modal-header {{ margin-bottom: 28px; padding-bottom: 24px; border-bottom: 2px solid #e8eaed; }}
        .status-badge {{ display: inline-block; padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 700; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .status-open {{ background: linear-gradient(135deg, #34a853 0%, #0f9d58 100%); color: white; box-shadow: 0 2px 6px rgba(52,168,83,0.3); }}
        .status-closed, .status-waitlist {{ background: linear-gradient(135deg, #ea4335 0%, #d33b2c 100%); color: white; box-shadow: 0 2px 6px rgba(234,67,53,0.3); }}
        .modal-course-number {{ font-size: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700; margin-bottom: 10px; letter-spacing: 0.3px; }}
        .modal-course-name {{ font-size: 24px; font-weight: 700; color: #202124; line-height: 1.3; margin-bottom: 4px; }}
        .modal-body {{ margin-bottom: 20px; }}
        .detail-row {{ display: flex; margin-bottom: 18px; align-items: flex-start; padding: 10px 0; border-bottom: 1px solid #f1f3f4; }}
        .detail-row:last-child {{ border-bottom: none; }}
        .detail-label {{ font-weight: 600; color: #5f6368; min-width: 130px; font-size: 14px; }}
        .detail-value {{ color: #202124; font-size: 14px; flex: 1; line-height: 1.5; font-weight: 500; }}
        .close-btn {{ position: absolute; top: 24px; right: 24px; font-size: 28px; color: #5f6368; cursor: pointer; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 50%; transition: all 0.2s; }}
        .close-btn:hover {{ background-color: #f1f3f4; transform: scale(1.1); color: #202124; }}
        .legend {{ margin-top: 20px; padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .legend-title {{ font-weight: 700; margin-bottom: 12px; color: #202124; font-size: 16px; }}
        .legend-item {{ display: block; margin-bottom: 8px; font-size: 13px; color: #5f6368; line-height: 1.6; }}
        .legend-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px 20px; margin-top: 15px; }}
        .legend-grid-item {{ display: flex; align-items: center; font-size: 13px; color: #202124; }}
        .color-box {{ display: inline-block; width: 18px; height: 18px; border-radius: 4px; margin-right: 8px; vertical-align: middle; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); flex-shrink: 0; }}

        /* Tabs */
        .tabs-container {{ background-color: white; padding: 12px 24px; margin-bottom: 10px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); display: flex; gap: 12px; }}
        .tab-btn {{ padding: 12px 24px; border: none; background-color: #f1f3f4; color: #5f6368; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; transition: all 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        .tab-btn:hover {{ background-color: #e8f0fe; color: #1a73e8; transform: translateY(-1px); box-shadow: 0 2px 6px rgba(0,0,0,0.1); }}
        .tab-btn:active {{ transform: translateY(0); }}
        .tab-btn.active {{ background: linear-gradient(135deg, #1a73e8 0%, #4285f4 100%); color: white; box-shadow: 0 3px 8px rgba(26,115,232,0.3); }}
        .tab-content {{ display: block; }}

        /* Instructor Selector */
        .instructor-selector-wrapper {{ position: relative; }}
        .instructor-dropdown {{ display: none; position: absolute; top: 100%; left: 0; background-color: white; border: 1px solid #dadce0; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.12), 0 2px 6px rgba(0,0,0,0.08); min-width: 320px; max-width: 420px; z-index: 100; margin-top: 8px; overflow: hidden; }}
        .instructor-dropdown.show {{ display: block; animation: dropdownSlide 0.2s ease-out; }}
        @keyframes dropdownSlide {{ from {{ opacity: 0; transform: translateY(-8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .instructor-dropdown-header {{ display: flex; justify-content: space-between; padding: 12px 16px; background: linear-gradient(135deg, #f8f9fa 0%, #e8eaed 100%); border-bottom: 1px solid #dadce0; gap: 10px; }}
        .dropdown-action-btn {{ padding: 8px 16px; border: 1px solid #1a73e8; background-color: white; color: #1a73e8; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.2s; flex: 1; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
        .dropdown-action-btn:hover {{ background-color: #1a73e8; color: white; transform: translateY(-1px); box-shadow: 0 2px 6px rgba(26,115,232,0.3); }}
        .dropdown-action-btn:active {{ transform: translateY(0); }}
        .instructor-list {{ max-height: 340px; overflow-y: auto; padding: 8px; background-color: #fafafa; }}
        .instructor-list::-webkit-scrollbar {{ width: 8px; }}
        .instructor-list::-webkit-scrollbar-track {{ background: #f1f3f4; border-radius: 4px; }}
        .instructor-list::-webkit-scrollbar-thumb {{ background: #dadce0; border-radius: 4px; }}
        .instructor-list::-webkit-scrollbar-thumb:hover {{ background: #bdc1c6; }}
        .instructor-checkbox-item {{ display: flex; align-items: center; padding: 10px 12px; margin-bottom: 4px; border-radius: 8px; cursor: pointer; transition: all 0.2s; background-color: white; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
        .instructor-checkbox-item:hover {{ background-color: #e8f0fe; transform: translateX(4px); box-shadow: 0 2px 6px rgba(26,115,232,0.15); }}
        .instructor-checkbox-item input[type="checkbox"] {{ margin-right: 12px; cursor: pointer; width: 18px; height: 18px; accent-color: #1a73e8; }}
        .instructor-checkbox-item label {{ cursor: pointer; font-size: 13px; color: #202124; flex: 1; display: flex; align-items: center; gap: 10px; font-weight: 500; }}
        .instructor-color-indicator {{ display: inline-block; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }}

        /* Planning Mode */
        .planning-container, .conflicts-container {{ background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .planning-container h2, .conflicts-container h2 {{ color: #202124; margin-bottom: 10px; font-size: 24px; }}
        .tab-description {{ color: #5f6368; margin-bottom: 25px; font-size: 14px; }}
        .instructor-schedule {{ margin-bottom: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid #1a73e8; }}
        .instructor-schedule-header {{ font-size: 18px; font-weight: 700; color: #202124; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }}
        .instructor-schedule-courses {{ display: grid; gap: 10px; }}
        .schedule-course-item {{ padding: 12px 15px; background-color: white; border-radius: 6px; border-left: 3px solid #667eea; }}
        .schedule-course-title {{ font-weight: 600; color: #202124; margin-bottom: 5px; }}
        .schedule-course-details {{ font-size: 13px; color: #5f6368; }}

        /* Room Conflicts */
        .conflict-group {{ margin-bottom: 25px; padding: 20px; background-color: #fff3cd; border-radius: 8px; border-left: 4px solid #ff6b6b; position: relative; }}
        .conflict-header {{ font-size: 16px; font-weight: 700; color: #721c24; margin-bottom: 10px; display: flex; align-items: center; gap: 10px; }}
        .conflict-severity {{ display: inline-block; padding: 3px 10px; background-color: #ff6b6b; color: white; border-radius: 12px; font-size: 11px; font-weight: 700; }}
        .conflict-ignore-btn {{ position: absolute; top: 15px; right: 15px; padding: 6px 12px; background-color: #5f6368; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.2s; }}
        .conflict-ignore-btn:hover {{ background-color: #3c4043; transform: scale(1.05); }}
        .conflict-courses {{ display: grid; gap: 12px; margin-top: 15px; }}
        .conflict-course-item {{ padding: 12px 15px; background-color: white; border-radius: 6px; border-left: 3px solid #ff6b6b; }}
        .conflict-course-header {{ font-weight: 600; color: #202124; margin-bottom: 5px; }}
        .conflict-course-details {{ font-size: 13px; color: #5f6368; }}
        .no-conflicts {{ padding: 30px; text-align: center; color: #5f6368; font-size: 16px; }}
        .conflict-indicator {{ border: 3px solid #ff6b6b !important; box-shadow: 0 0 0 3px rgba(255,107,107,0.2) !important; }}
        .conflict-hidden {{ display: none; }}
    </style>
</head>
<body>
    <!-- Read the Docs style navigation -->
    <nav class="rtd-navbar">
        <div class="rtd-navbar-content">
            <div class="rtd-navbar-left">
                <span class="rtd-navbar-title">🎓 GWU Course Calendar</span>
            </div>
            <div class="rtd-navbar-right">
                <a href="https://github.com/mmann1123/GWU_Course_Calendar" target="_blank" class="rtd-nav-link">
                    <svg class="github-icon" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
                        <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                    </svg>
                    GitHub
                </a>
                <a href="https://github.com/mmann1123/GWU_Course_Calendar/issues" target="_blank" class="rtd-nav-link">
                    Report Issue
                </a>
            </div>
        </div>
    </nav>

    <div class="main-content">
        <div class="header">
            <h1>🗓️ {title}</h1>
            <p>Interactive Course Schedule | Scraped from GWU website on {datetime.now().strftime("%B %d, %Y")}</p>
        </div>

    <div class="stats">
        <div class="stats-item"><span class="stats-number" id="totalCourses">0</span><span>Total Courses</span></div>
        <div class="stats-item"><span class="stats-number" id="totalInstructors">0</span><span>Instructors</span></div>
    </div>

    <div class="tabs-container">
        <button class="tab-btn active" data-tab="all-courses" onclick="switchTab('all-courses')">📅 All Courses</button>
        <button class="tab-btn" data-tab="planning-mode" onclick="switchTab('planning-mode')">👥 Planning Mode</button>
        <button class="tab-btn" data-tab="room-conflicts" onclick="switchTab('room-conflicts')">⚠️ Room Conflicts</button>
    </div>

    <div class="filter-controls">
        <span class="filter-text">View:</span>
        <button class="filter-btn" onclick="showAllDays()">Show All Days</button>
        <span class="filter-text">|</span>
        <span class="filter-text">Instructors:</span>
        <div class="instructor-selector-wrapper">
            <button class="filter-btn" id="instructorDropdownBtn" onclick="toggleInstructorDropdown()">
                <span id="instructorBtnText">All Instructors</span> ▼
            </button>
            <div class="instructor-dropdown" id="instructorDropdown">
                <div class="instructor-dropdown-header">
                    <button class="dropdown-action-btn" onclick="selectAllInstructors()">Select All</button>
                    <button class="dropdown-action-btn" onclick="clearAllInstructors()">Clear All</button>
                </div>
                <div class="instructor-list" id="instructorList"></div>
            </div>
        </div>
        <span class="filter-text" id="filterStatus">Showing all days, all instructors</span>
    </div>

    <div class="tab-content" id="all-courses-tab">
        <div class="calendar-container">
            <div class="calendar-header">
                <div class="day-header" style="background-color: white; cursor: default;"></div>
                <div class="day-header" data-day="monday" onclick="filterDay('monday')">Monday</div>
                <div class="day-header" data-day="tuesday" onclick="filterDay('tuesday')">Tuesday</div>
                <div class="day-header" data-day="wednesday" onclick="filterDay('wednesday')">Wednesday</div>
                <div class="day-header" data-day="thursday" onclick="filterDay('thursday')">Thursday</div>
                <div class="day-header" data-day="friday" onclick="filterDay('friday')">Friday</div>
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

        <div class="legend" id="instructorLegend"></div>
    </div>

    <div class="tab-content" id="planning-mode-tab" style="display: none;">
        <div class="planning-container">
            <h2>Planning Mode - Instructor Schedules</h2>
            <p class="tab-description">View individual instructor schedules and identify potential conflicts</p>
            <div id="planningModeContent"></div>
        </div>
    </div>

    <div class="tab-content" id="room-conflicts-tab" style="display: none;">
        <div class="conflicts-container">
            <h2>Room Conflicts Detection</h2>
            <p class="tab-description">Courses scheduled in the same room at overlapping times</p>
            <div id="conflictsContent"></div>
        </div>
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
        let instructorColors = {{}};
        let selectedInstructors = new Set();
        let activeTab = 'all-courses';
        let selectedDay = null;
        let roomConflicts = [];

        // Generate unique color for each instructor using HSL
        function generateInstructorColors() {{
            const instructors = [...new Set(courses.map(c => c.instructor))].sort();
            const hueStep = 360 / instructors.length;
            instructors.forEach((instructor, index) => {{
                const hue = Math.floor(index * hueStep);
                const saturation = 65 + (index % 3) * 10; // 65%, 75%, or 85%
                const lightness = 50 + (index % 2) * 10;  // 50% or 60%
                instructorColors[instructor] = `hsl(${{hue}}, ${{saturation}}%, ${{lightness}}%)`;
            }});
        }}

        function getInstructorColor(instructor) {{
            return instructorColors[instructor] || '#667eea';
        }}

        // Tab switching
        function switchTab(tabName) {{
            activeTab = tabName;

            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                if (btn.getAttribute('data-tab') === tabName) {{
                    btn.classList.add('active');
                }} else {{
                    btn.classList.remove('active');
                }}
            }});

            // Update tab content visibility
            document.querySelectorAll('.tab-content').forEach(content => {{
                content.style.display = 'none';
            }});
            document.getElementById(tabName + '-tab').style.display = 'block';

            // Load tab-specific content
            if (tabName === 'planning-mode') {{
                generatePlanningMode();
            }} else if (tabName === 'room-conflicts') {{
                detectAndDisplayRoomConflicts();
            }}
        }}

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

            // Use instructor-specific color
            const instructorColor = getInstructorColor(course.instructor);
            courseBlock.style.background = instructorColor;

            // Check if this course has a room conflict
            const hasConflict = roomConflicts.some(conflict =>
                conflict.courses.some(c => c.crn === course.crn)
            );
            if (hasConflict) {{
                courseBlock.classList.add('conflict-indicator');
            }}

            courseBlock.innerHTML = `
                <div class="course-number">${{course.course_number}}</div>
                <div class="course-name">${{course.title}}</div>
                <div class="course-time">${{course.time.start}}</div>
                <div class="tooltip">
                    <div class="tooltip-row"><span class="tooltip-label">Course:</span><span class="tooltip-value">${{course.course_number}}</span></div>
                    <div class="tooltip-row"><span class="tooltip-label">Instructor:</span><span class="tooltip-value">${{course.instructor}}</span></div>
                    <div class="tooltip-row"><span class="tooltip-label">Time:</span><span class="tooltip-value">${{course.time.raw}}</span></div>
                    <div class="tooltip-row"><span class="tooltip-label">Location:</span><span class="tooltip-value">${{course.building}} ${{course.room}}</span></div>
                    <div class="tooltip-row"><span class="tooltip-label">CRN:</span><span class="tooltip-value">${{course.crn}}</span></div>
                </div>
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

        // Instructor dropdown functions
        function populateInstructorList() {{
            const instructors = [...new Set(courses.map(c => c.instructor))].sort();
            const instructorList = document.getElementById('instructorList');
            instructorList.innerHTML = '';

            instructors.forEach(instructor => {{
                const item = document.createElement('div');
                item.className = 'instructor-checkbox-item';
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `instructor-${{instructor.replace(/\\s+/g, '-')}}`;
                checkbox.value = instructor;
                checkbox.checked = selectedInstructors.size === 0 || selectedInstructors.has(instructor);
                checkbox.onchange = () => toggleInstructorSelection(instructor);

                const label = document.createElement('label');
                label.setAttribute('for', checkbox.id);
                const colorIndicator = document.createElement('span');
                colorIndicator.className = 'instructor-color-indicator';
                colorIndicator.style.backgroundColor = getInstructorColor(instructor);
                label.appendChild(colorIndicator);
                label.appendChild(document.createTextNode(instructor));

                item.appendChild(checkbox);
                item.appendChild(label);
                instructorList.appendChild(item);
            }});
        }}

        function toggleInstructorDropdown() {{
            const dropdown = document.getElementById('instructorDropdown');
            dropdown.classList.toggle('show');
        }}

        function toggleInstructorSelection(instructor) {{
            if (selectedInstructors.has(instructor)) {{
                selectedInstructors.delete(instructor);
            }} else {{
                selectedInstructors.add(instructor);
            }}
            updateInstructorButtonText();
            applyFilters();
        }}

        function selectAllInstructors() {{
            selectedInstructors.clear();
            document.querySelectorAll('#instructorList input[type="checkbox"]').forEach(cb => {{
                cb.checked = true;
            }});
            updateInstructorButtonText();
            applyFilters();
        }}

        function clearAllInstructors() {{
            selectedInstructors.clear();
            document.querySelectorAll('#instructorList input[type="checkbox"]').forEach(cb => {{
                cb.checked = false;
                selectedInstructors.add(cb.value);
            }});
            // Start with one instructor selected
            const firstCheckbox = document.querySelector('#instructorList input[type="checkbox"]');
            if (firstCheckbox) {{
                firstCheckbox.checked = true;
                selectedInstructors.clear();
                selectedInstructors.add(firstCheckbox.value);
            }}
            updateInstructorButtonText();
            applyFilters();
        }}

        function updateInstructorButtonText() {{
            const btnText = document.getElementById('instructorBtnText');
            if (selectedInstructors.size === 0) {{
                btnText.textContent = 'All Instructors';
            }} else if (selectedInstructors.size === 1) {{
                btnText.textContent = Array.from(selectedInstructors)[0];
            }} else {{
                btnText.textContent = `${{selectedInstructors.size}} Instructors`;
            }}
        }}

        function applyFilters() {{
            clearCalendar();
            const filteredCourses = courses.filter(course => {{
                const instructorMatch = selectedInstructors.size === 0 || selectedInstructors.has(course.instructor);
                return instructorMatch;
            }});
            renderCoursesFiltered(filteredCourses);
            updateFilterStatus();
            updateInstructorLegend();

            // If planning mode is active, regenerate it with the filtered instructors
            if (activeTab === 'planning-mode') {{
                generatePlanningMode();
            }}
        }}

        function clearCalendar() {{
            ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'].forEach(day => {{
                const dayColumn = document.getElementById(day);
                // Remove only course blocks, keep hour lines
                dayColumn.querySelectorAll('.course-block').forEach(block => block.remove());
            }});
        }}

        function renderCoursesFiltered(coursesToRender) {{
            const startHour = 9;
            const pixelsPerMinute = 1;
            const coursesByDay = {{ monday: [], tuesday: [], wednesday: [], thursday: [], friday: [] }};

            coursesToRender.forEach(course => {{
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

        function updateFilterStatus() {{
            const filterStatus = document.getElementById('filterStatus');
            let statusParts = [];

            if (selectedDay) {{
                const dayNames = {{
                    'monday': 'Monday',
                    'tuesday': 'Tuesday',
                    'wednesday': 'Wednesday',
                    'thursday': 'Thursday',
                    'friday': 'Friday'
                }};
                statusParts.push(`${{dayNames[selectedDay]}} only`);
            }} else {{
                statusParts.push('all days');
            }}

            if (selectedInstructors.size === 0) {{
                statusParts.push('all instructors');
            }} else if (selectedInstructors.size === 1) {{
                statusParts.push(Array.from(selectedInstructors)[0]);
            }} else {{
                statusParts.push(`${{selectedInstructors.size}} instructors`);
            }}

            filterStatus.textContent = `Showing: ${{statusParts.join(' | ')}}`;
        }}

        function updateInstructorLegend() {{
            const legend = document.getElementById('instructorLegend');
            if (!legend) return;

            const instructorsToShow = selectedInstructors.size === 0
                ? [...new Set(courses.map(c => c.instructor))].sort()
                : Array.from(selectedInstructors).sort();

            let html = '<div class="legend-title">👥 Instructor Color Key</div><div class="legend-grid">';
            instructorsToShow.forEach(instructor => {{
                const color = getInstructorColor(instructor);
                html += `<div class="legend-grid-item"><span class="color-box" style="background: ${{color}}"></span><span>${{instructor}}</span></div>`;
            }});
            html += '</div>';
            legend.innerHTML = html;
        }}

        // Close dropdown when clicking outside
        document.addEventListener('click', function(event) {{
            const dropdown = document.getElementById('instructorDropdown');
            const btn = document.getElementById('instructorDropdownBtn');
            if (dropdown && btn && !dropdown.contains(event.target) && !btn.contains(event.target)) {{
                dropdown.classList.remove('show');
            }}
        }});

        function filterDay(day) {{
            selectedDay = day;

            // Hide all day columns
            ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'].forEach(d => {{
                const col = document.getElementById(d);
                if (d === day) {{
                    col.style.display = 'block';
                }} else {{
                    col.style.display = 'none';
                }}
            }});

            // Update active state on headers
            document.querySelectorAll('.day-header[data-day]').forEach(header => {{
                if (header.getAttribute('data-day') === day) {{
                    header.classList.add('active');
                }} else {{
                    header.classList.remove('active');
                }}
            }});

            // Adjust calendar layout for single day view
            const calendarBody = document.querySelector('.calendar-body');
            const calendarHeader = document.querySelector('.calendar-header');
            calendarBody.style.gridTemplateColumns = '80px 1fr';
            calendarHeader.style.gridTemplateColumns = '80px 1fr';

            updateFilterStatus();
        }}

        function showAllDays() {{
            selectedDay = null;

            // Show all day columns
            ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'].forEach(d => {{
                document.getElementById(d).style.display = 'block';
            }});

            // Remove active state from all headers
            document.querySelectorAll('.day-header[data-day]').forEach(header => {{
                header.classList.remove('active');
            }});

            // Restore calendar layout
            const calendarBody = document.querySelector('.calendar-body');
            const calendarHeader = document.querySelector('.calendar-header');
            calendarBody.style.gridTemplateColumns = '80px repeat(5, minmax(180px, 1fr))';
            calendarHeader.style.gridTemplateColumns = '80px repeat(5, minmax(180px, 1fr))';

            updateFilterStatus();
        }}

        // Room conflict detection
        function detectRoomConflicts() {{
            roomConflicts = [];
            const roomGroups = {{}};

            // Normalize room key for consistent matching
            function normalizeRoomKey(building, room) {{
                // Remove extra spaces, convert to uppercase for consistency
                const normBuilding = building.replace(/\\s+/g, ' ').trim().toUpperCase();
                const normRoom = room.replace(/\\s+/g, ' ').trim().toUpperCase();
                return `${{normBuilding}}|${{normRoom}}`;
            }}

            // Group courses by room
            courses.forEach(course => {{
                if (course.building === 'Not specified' || course.room === 'Not specified') return;
                const roomKey = normalizeRoomKey(course.building, course.room);
                if (!roomGroups[roomKey]) {{
                    roomGroups[roomKey] = {{
                        displayName: `${{course.building}} ${{course.room}}`,
                        courses: []
                    }};
                }}
                roomGroups[roomKey].courses.push(course);
            }});

            // Check for overlaps within each room
            console.log(`📋 Checking ${{Object.keys(roomGroups).length}} rooms for conflicts...`);
            Object.keys(roomGroups).forEach(roomKey => {{
                const roomData = roomGroups[roomKey];
                const roomCourses = roomData.courses;

                // Log rooms with multiple courses
                if (roomCourses.length >= 2) {{
                    console.log(`  Room: ${{roomData.displayName}} has ${{roomCourses.length}} courses`);
                    roomCourses.forEach(c => {{
                        console.log(`    - ${{c.course_number}} (${{c.instructor}}) ${{c.days}} ${{c.time.raw}}`);
                    }});
                }}

                if (roomCourses.length < 2) return;

                const conflicts = [];
                for (let i = 0; i < roomCourses.length; i++) {{
                    for (let j = i + 1; j < roomCourses.length; j++) {{
                        const course1 = roomCourses[i];
                        const course2 = roomCourses[j];

                        // Check if they share any days
                        const days1 = course1.days.split('');
                        const days2 = course2.days.split('');
                        const sharedDays = days1.filter(d => days2.includes(d));

                        if (sharedDays.length === 0) continue;

                        // Check if times overlap
                        const start1 = timeToMinutes(course1.time.start);
                        const end1 = timeToMinutes(course1.time.end);
                        const start2 = timeToMinutes(course2.time.start);
                        const end2 = timeToMinutes(course2.time.end);

                        if (start1 < end2 && end1 > start2) {{
                            // We have a conflict
                            const existingConflict = conflicts.find(c =>
                                c.courses.some(co => co.crn === course1.crn || co.crn === course2.crn)
                            );

                            if (existingConflict) {{
                                if (!existingConflict.courses.some(c => c.crn === course1.crn)) {{
                                    existingConflict.courses.push(course1);
                                }}
                                if (!existingConflict.courses.some(c => c.crn === course2.crn)) {{
                                    existingConflict.courses.push(course2);
                                }}
                            }} else {{
                                conflicts.push({{
                                    room: roomData.displayName,
                                    courses: [course1, course2],
                                    sharedDays: sharedDays
                                }});
                            }}
                        }}
                    }}
                }}

                roomConflicts.push(...conflicts);
            }});

            // Log detected conflicts for debugging
            console.log(`🔍 Room Conflict Detection: Found ${{roomConflicts.length}} conflict group(s)`);
            roomConflicts.forEach((conflict, index) => {{
                console.log(`  Conflict ${{index + 1}}: ${{conflict.room}} - ${{conflict.courses.length}} courses`);
                conflict.courses.forEach(c => {{
                    console.log(`    - ${{c.course_number}} (${{c.instructor}}) ${{c.days}} ${{c.time.raw}}`);
                }});
            }});

            return roomConflicts;
        }}

        function detectAndDisplayRoomConflicts() {{
            const conflicts = detectRoomConflicts();
            const container = document.getElementById('conflictsContent');

            // Find courses with unspecified rooms
            const unspecifiedRooms = courses.filter(c =>
                c.room.toLowerCase().includes('not specified') ||
                c.room.toLowerCase().includes('tbd') ||
                c.room.toLowerCase().includes('tba') ||
                c.room.trim() === ''
            );

            let html = '';

            // Display unspecified rooms section
            if (unspecifiedRooms.length > 0) {{
                html += `<div style="margin-bottom: 25px; padding: 18px; background-color: #e3f2fd; border-left: 4px solid #2980b9; border-radius: 8px;">
                    <strong>📋 Found ${{unspecifiedRooms.length}} course${{unspecifiedRooms.length > 1 ? 's' : ''}} with unspecified rooms</strong>
                    <p style="margin-top: 8px; color: #5f6368; font-size: 14px;">The following courses do not have room assignments:</p>
                </div>`;

                html += `<div style="margin-bottom: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid #2980b9;">
                    <div style="font-size: 16px; font-weight: 700; color: #202124; margin-bottom: 15px; display: flex; align-items: center; gap: 10px;">
                        <span>📍 Unspecified Rooms</span>
                        <span style="display: inline-block; padding: 3px 10px; background-color: #2980b9; color: white; border-radius: 12px; font-size: 11px; font-weight: 700;">${{unspecifiedRooms.length}} COURSES</span>
                    </div>
                    <div style="display: grid; gap: 12px;">`;

                unspecifiedRooms.forEach(course => {{
                    const daysExpanded = expandDays(course.days);
                    html += `<div style="padding: 12px 15px; background-color: white; border-radius: 6px; border-left: 3px solid #2980b9;">
                        <div style="font-weight: 600; color: #202124; margin-bottom: 5px;">${{course.course_number}} - ${{course.title}}</div>
                        <div style="font-size: 13px; color: #5f6368;">
                            <strong>CRN:</strong> ${{course.crn}} |
                            <strong>Instructor:</strong> ${{course.instructor}}<br>
                            <strong>Time:</strong> ${{course.time.raw}} |
                            <strong>Days:</strong> ${{daysExpanded}} |
                            <strong>Room:</strong> ${{course.room}}
                        </div>
                    </div>`;
                }});

                html += `</div></div>`;
            }}

            // Display room conflicts
            if (conflicts.length === 0) {{
                if (unspecifiedRooms.length === 0) {{
                    html = '<div class="no-conflicts">✅ No room conflicts detected! All courses are scheduled without overlap.</div>';
                }} else {{
                    html += '<div class="no-conflicts">✅ No room conflicts detected for assigned rooms.</div>';
                }}
                container.innerHTML = html;
                return;
            }}

            html += `<div style="margin-bottom: 20px; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ff6b6b; border-radius: 6px;">
                <strong>⚠️ Found ${{conflicts.length}} room conflict${{conflicts.length > 1 ? 's' : ''}}</strong>
                <p style="margin-top: 8px; color: #5f6368; font-size: 14px;">The following rooms have multiple courses scheduled at overlapping times:</p>
            </div>`;

            conflicts.forEach((conflict, index) => {{
                html += `<div class="conflict-group" id="conflict-${{index}}">
                    <button class="conflict-ignore-btn" onclick="ignoreConflict(${{index}})">✕ Ignore</button>
                    <div class="conflict-header">
                        <span>📍 ${{conflict.room}}</span>
                        <span class="conflict-severity">${{conflict.courses.length}} COURSES</span>
                    </div>
                    <p style="color: #721c24; font-size: 13px; margin: 10px 0;">These courses are scheduled in the same room at overlapping times:</p>
                    <div class="conflict-courses">`;

                conflict.courses.forEach(course => {{
                    const daysExpanded = expandDays(course.days);
                    html += `<div class="conflict-course-item">
                        <div class="conflict-course-header">${{course.course_number}} - ${{course.title}}</div>
                        <div class="conflict-course-details">
                            <strong>CRN:</strong> ${{course.crn}} |
                            <strong>Instructor:</strong> ${{course.instructor}}<br>
                            <strong>Time:</strong> ${{course.time.raw}} |
                            <strong>Days:</strong> ${{daysExpanded}}
                        </div>
                    </div>`;
                }});

                html += `</div></div>`;
            }});

            container.innerHTML = html;
        }}

        function ignoreConflict(conflictIndex) {{
            const conflictElement = document.getElementById(`conflict-${{conflictIndex}}`);
            if (conflictElement) {{
                conflictElement.classList.add('conflict-hidden');
            }}
        }}

        // Planning mode - show instructor schedules
        function generatePlanningMode() {{
            const container = document.getElementById('planningModeContent');

            // Respect instructor filtering
            const allInstructors = [...new Set(courses.map(c => c.instructor))].sort();
            const instructors = selectedInstructors.size === 0
                ? allInstructors
                : allInstructors.filter(inst => selectedInstructors.has(inst));

            let html = '';

            if (instructors.length === 0) {{
                html = '<div class="no-conflicts">📋 No instructors selected. Use the instructor filter above to select instructors to view their schedules.</div>';
                container.innerHTML = html;
                return;
            }}

            instructors.forEach(instructor => {{
                const instructorCourses = courses.filter(c => c.instructor === instructor);
                const instructorColor = getInstructorColor(instructor);

                html += `<div class="instructor-schedule">
                    <div class="instructor-schedule-header">
                        <span class="instructor-color-indicator" style="background-color: ${{instructorColor}}; width: 20px; height: 20px;"></span>
                        <span>${{instructor}} (${{instructorCourses.length}} course${{instructorCourses.length > 1 ? 's' : ''}})</span>
                    </div>
                    <div class="instructor-schedule-courses">`;

                instructorCourses.forEach(course => {{
                    const daysExpanded = expandDays(course.days);
                    html += `<div class="schedule-course-item" style="border-left-color: ${{instructorColor}};">
                        <div class="schedule-course-title">${{course.course_number}} - ${{course.title}}</div>
                        <div class="schedule-course-details">
                            <strong>CRN:</strong> ${{course.crn}} |
                            <strong>Time:</strong> ${{course.time.raw}} |
                            <strong>Days:</strong> ${{daysExpanded}}<br>
                            <strong>Location:</strong> ${{course.building}} ${{course.room}} |
                            <strong>Credits:</strong> ${{course.credits}}
                        </div>
                    </div>`;
                }});

                html += `</div></div>`;
            }});

            container.innerHTML = html;
        }}

        window.onclick = function(event) {{
            if (event.target === document.getElementById('modal')) closeModal();
        }}

        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') closeModal();
        }});

        // Initialize
        generateInstructorColors();
        detectRoomConflicts();
        createTimeSlots();
        renderCourses();
        populateInstructorList();
        updateInstructorLegend();
    </script>
    </div> <!-- end main-content -->

    <!-- Read the Docs style footer -->
    <footer class="rtd-footer">
        <div class="rtd-footer-content">
            <div class="rtd-footer-left">
                <strong>GWU Course Calendar Scraper</strong><br>
                Interactive course schedule viewer for George Washington University
            </div>
            <div class="rtd-footer-links">
                <a href="https://github.com/mmann1123/GWU_Course_Calendar" target="_blank" class="rtd-footer-link">
                    <svg class="github-icon" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
                        <path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                    </svg>
                    View on GitHub
                </a>
                <a href="https://github.com/mmann1123/GWU_Course_Calendar/issues" target="_blank" class="rtd-footer-link">
                    <svg class="github-icon" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
                        <path fill="currentColor" d="M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 1116 0A8 8 0 010 8zm9 3a1 1 0 11-2 0 1 1 0 012 0zM6.92 6.085c.081-.16.19-.299.34-.398.145-.097.371-.187.74-.187.28 0 .553.087.738.225A.613.613 0 019 6.25c0 .177-.04.264-.077.318a.956.956 0 01-.277.245c-.076.051-.158.1-.258.161l-.007.004a7.728 7.728 0 00-.313.195 2.416 2.416 0 00-.692.661.75.75 0 001.248.832.956.956 0 01.276-.245 6.3 6.3 0 01.26-.16l.006-.004c.093-.057.204-.123.313-.195.222-.149.487-.355.692-.662.214-.32.329-.702.329-1.15 0-.76-.36-1.348-.863-1.725A2.76 2.76 0 008 4c-.631 0-1.155.16-1.572.438-.413.276-.68.638-.849.977a.75.75 0 001.342.67z"/>
                    </svg>
                    Report Issue
                </a>
            </div>
        </div>
        <div class="rtd-footer-attribution">
            Credit: Michael Mann, Dept of Geography & Environment<br>
            Scraped on {datetime.now().strftime("%B %d, %Y at %I:%M %p")} | Built with Python & BeautifulSoup
        </div>
    </footer>
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

        # Extract year and semester from URL if available
        year = None
        semester = None
        if args.url and 'termId=' in args.url:
            import re
            term_match = re.search(r'termId=(\d{4})(\d{2})', args.url)
            if term_match:
                year = term_match.group(1)
                semester = term_match.group(2)

        generate_html_calendar(courses, args.output, year=year, semester=semester)

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
