#!/usr/bin/env python3
"""
Registrar .xlsx import/export for the GWU Course Calendar.

The GWU registrar's office distributes/collects schedules as an .xlsx file with a
specific column layout (the "Export" sheet). This module converts between that
layout and the dashboard's internal course dictionaries so departments can:

    registrar .xlsx  --read-->  dashboard calendar  --write-->  registrar .xlsx

The conversion is designed to be lossless on round-trip: registrar-only columns
(GWID, enrollment counts, comment, section title, full first name) are carried
through as pass-through fields on each course dict, and the start/end dates are
preserved as ISO strings so they can be written back exactly.

Registrar column layout (header row, 18 columns):
    Changes | Subject Code | Course Number | Course | Section Title |
    Instructor GWID | Instructor Last Name | Instructor First Name | Credits |
    Max Enrollment | Prior Enrollment | Wait Capacity |
    Course Start Date | Course End Date | Weekly Meeting Pattern |
    Begin Time HHMM | End Time HHMM | Comment
"""

import re
from datetime import datetime
from typing import Dict, List, Optional

try:
    import openpyxl
    from openpyxl.styles import Font
except ImportError:  # pragma: no cover - surfaced to the caller with guidance
    openpyxl = None


# Exact registrar header order. The reader matches columns by name (so it is
# robust to reordering), but the writer emits them in this order.
REGISTRAR_COLUMNS = [
    'Changes',
    'Subject Code',
    'Course Number',
    'Course',
    'Section Title',
    'Instructor GWID',
    'Instructor Last Name',
    'Instructor First Name',
    'Credits',
    'Max Enrollment',
    'Prior Enrollment',
    'Wait Capacity',
    'Course Start Date',
    'Course End Date',
    'Weekly Meeting Pattern',
    'Begin Time HHMM',
    'End Time HHMM',
    'Comment',
]


def _require_openpyxl():
    if openpyxl is None:
        raise ImportError(
            "openpyxl is required for .xlsx import/export.\n"
            "Install it with:  pip install openpyxl\n"
            "(or:  pip install -r requirements.txt)"
        )


# ---------------------------------------------------------------------------
# Value converters
# ---------------------------------------------------------------------------

def hhmm_to_12h(value) -> Optional[str]:
    """Convert registrar 'HHMM' 24-hour time to dashboard '02:20PM' format.

    Returns None for arranged / TBA courses (blank, None, or '####' markers).
    Examples: '1420' -> '02:20PM', '0900' -> '09:00AM', '####' -> None
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s or '#' in s or not s.isdigit():
        return None
    s = s.zfill(4)
    hour = int(s[:2])
    minute = int(s[2:])
    if hour > 23 or minute > 59:
        return None
    period = 'AM' if hour < 12 else 'PM'
    hour12 = hour % 12
    if hour12 == 0:
        hour12 = 12
    return f"{hour12:02d}:{minute:02d}{period}"


def time12h_to_hhmm(value: Optional[str]) -> Optional[str]:
    """Convert dashboard '02:20PM' to registrar 'HHMM'. Returns None if unparseable."""
    if not value:
        return None
    m = re.match(r'\s*(\d{1,2}):(\d{2})\s*([AP]M)\s*$', str(value), re.IGNORECASE)
    if not m:
        return None
    hour = int(m.group(1)) % 12
    minute = int(m.group(2))
    if m.group(3).upper() == 'PM':
        hour += 12
    return f"{hour:02d}{minute:02d}"


def credits_to_display(value) -> str:
    """Registrar credits (3, 0, 1) -> dashboard '3.00' style string."""
    if value is None or str(value).strip() == '':
        return ''
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value).strip()


def credits_to_number(value):
    """Dashboard '3.00' -> registrar number (int when whole, else float)."""
    if value is None or str(value).strip() == '':
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value).strip()
    return int(num) if num.is_integer() else num


def fmt_date(value) -> str:
    """A datetime (or 'MM/DD/YY' string) -> 'MM/DD/YY' display string."""
    if value is None:
        return ''
    if isinstance(value, datetime):
        return value.strftime('%m/%d/%y')
    return str(value).strip()


def _to_datetime(value) -> Optional[datetime]:
    """Coerce a cell value or ISO/US date string into a datetime."""
    if value is None or str(value).strip() == '':
        return None
    if isinstance(value, datetime):
        return value
    s = str(value).strip()
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def build_instructor_display(last: Optional[str], first: Optional[str]) -> str:
    """('Chacko', 'Elizabeth') -> 'Chacko, E'. Blank last name -> ''."""
    last = (last or '').strip()
    first = (first or '').strip()
    if not last:
        return ''
    if first:
        return f"{last}, {first[0]}"
    return last


def split_instructor_display(instructor: Optional[str]):
    """'Chacko, E' -> ('Chacko', 'E'). Only the first initial is recoverable."""
    if not instructor or not instructor.strip():
        return '', ''
    parts = instructor.split(',', 1)
    last = parts[0].strip()
    first = parts[1].strip() if len(parts) > 1 else ''
    return last, first


def derive_status(max_enrollment, prior_enrollment) -> str:
    """OPEN unless prior enrollment has met or exceeded the cap -> CLOSED."""
    try:
        max_e = int(max_enrollment)
        prior_e = int(prior_enrollment)
    except (TypeError, ValueError):
        return 'OPEN'
    if max_e > 0 and prior_e >= max_e:
        return 'CLOSED'
    return 'OPEN'


# ---------------------------------------------------------------------------
# Reader: registrar .xlsx -> course dictionaries
# ---------------------------------------------------------------------------

def read_registrar_xlsx(path: str) -> List[Dict]:
    """Read a registrar .xlsx file and return a list of course dictionaries.

    Every data row is returned, including arranged / TBA courses (which have
    ``time`` set to None and empty ``days``). Use ``[c for c in courses if
    c.get('time')]`` to get only the rows that can be placed on the calendar.

    Registrar-only fields are preserved on each dict for lossless write-back:
    ``gwid``, ``instructor_last``, ``instructor_first``, ``section_title``,
    ``max_enrollment``, ``prior_enrollment``, ``wait_capacity``, ``comment``,
    ``course_start_date``/``course_end_date`` (ISO), and ``source='registrar'``.
    """
    _require_openpyxl()
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active  # registrar files use a single 'Export' sheet

    # Locate the header row (the one containing 'Subject Code') and map names.
    header_row = None
    col_index = {}
    for r in range(1, min(ws.max_row, 10) + 1):
        values = [ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)]
        names = [str(v).strip() if v is not None else '' for v in values]
        if 'Subject Code' in names:
            header_row = r
            col_index = {name: i + 1 for i, name in enumerate(names) if name}
            break

    if header_row is None:
        raise ValueError(
            "Could not find a registrar header row (expected a 'Subject Code' "
            "column). Is this the registrar's Export .xlsx layout?"
        )

    def cell(r, name):
        c = col_index.get(name)
        return ws.cell(row=r, column=c).value if c else None

    courses: List[Dict] = []
    seq = 0
    for r in range(header_row + 1, ws.max_row + 1):
        subject = cell(r, 'Subject Code')
        course_num = cell(r, 'Course Number')
        # Skip fully blank rows.
        if (subject is None or str(subject).strip() == '') and \
           (course_num is None or str(course_num).strip() == ''):
            continue

        seq += 1
        subject = str(subject).strip() if subject is not None else ''
        course_num = str(course_num).strip() if course_num is not None else ''
        course_title = (str(cell(r, 'Course')).strip()
                        if cell(r, 'Course') is not None else '')
        section_title = (str(cell(r, 'Section Title')).strip()
                         if cell(r, 'Section Title') is not None else '')

        last = cell(r, 'Instructor Last Name')
        first = cell(r, 'Instructor First Name')
        gwid = cell(r, 'Instructor GWID')

        max_e = cell(r, 'Max Enrollment')
        prior_e = cell(r, 'Prior Enrollment')
        wait_c = cell(r, 'Wait Capacity')

        start_dt = _to_datetime(cell(r, 'Course Start Date'))
        end_dt = _to_datetime(cell(r, 'Course End Date'))

        days = cell(r, 'Weekly Meeting Pattern')
        days = ''.join(ch for ch in str(days).strip() if ch in 'MTWRF') if days else ''

        start12 = hhmm_to_12h(cell(r, 'Begin Time HHMM'))
        end12 = hhmm_to_12h(cell(r, 'End Time HHMM'))
        comment = cell(r, 'Comment')

        # Display title folds in the special-topics section title when present.
        display_title = course_title
        if section_title:
            display_title = f"{course_title} - {section_title}" if course_title else section_title

        if start12 and end12 and days:
            time_info = {'start': start12, 'end': end12, 'raw': f"{start12} - {end12}"}
        else:
            time_info = None  # arranged / TBA course

        dates_str = ''
        if start_dt and end_dt:
            dates_str = f"{fmt_date(start_dt)} - {fmt_date(end_dt)}"

        course = {
            # ---- dashboard fields ----
            'status': derive_status(max_e, prior_e),
            'crn': f"R{seq:04d}",          # synthetic; registrar has no CRN column
            'subject': subject,
            'course_num': course_num,
            'section': '',                 # registrar sheet has no section number
            'title': display_title,
            'credits': credits_to_display(cell(r, 'Credits')),
            'instructor': build_instructor_display(last, first),
            'days': days,
            'time': time_info,
            'dates': dates_str,
            'building': 'Not specified',   # room assignment happens after Round I
            'room': 'Not specified',
            'course_number': f"{subject} {course_num}".strip(),
            # ---- registrar pass-through (for lossless write-back) ----
            'source': 'registrar',
            'synthetic_crn': True,
            'gwid': str(gwid).strip() if gwid is not None else '',
            'instructor_last': str(last).strip() if last is not None else '',
            'instructor_first': str(first).strip() if first is not None else '',
            'section_title': section_title,
            'max_enrollment': max_e,
            'prior_enrollment': prior_e,
            'wait_capacity': wait_c,
            'comment': str(comment).strip() if comment is not None else '',
            'course_start_date': start_dt.isoformat() if start_dt else '',
            'course_end_date': end_dt.isoformat() if end_dt else '',
        }
        courses.append(course)

    return courses


# ---------------------------------------------------------------------------
# Writer: course dictionaries -> registrar .xlsx
# ---------------------------------------------------------------------------

def _registrar_row(course: Dict) -> List:
    """Build one registrar row (list aligned to REGISTRAR_COLUMNS) from a course."""
    subject = course.get('subject', '') or ''
    course_num = course.get('course_num', '') or ''

    # Prefer preserved registrar fields; fall back to deriving from dashboard data.
    section_title = course.get('section_title', '')
    if not section_title:
        # If the title was folded as "Course - Section Title", we leave the
        # whole thing in Course and Section Title blank; nothing to recover.
        pass

    last = course.get('instructor_last', '')
    first = course.get('instructor_first', '')
    if not last and not first:
        last, first = split_instructor_display(course.get('instructor', ''))

    # Course title: drop any "- Section Title" suffix when we have it separately.
    title = course.get('title', '') or ''
    if section_title and title.endswith(f" - {section_title}"):
        title = title[: -len(f" - {section_title}")]

    # Dates: prefer preserved ISO dates, else parse the display range.
    start_dt = _to_datetime(course.get('course_start_date'))
    end_dt = _to_datetime(course.get('course_end_date'))
    if (start_dt is None or end_dt is None) and course.get('dates'):
        m = re.match(r'\s*([\d/]+)\s*-\s*([\d/]+)\s*$', course['dates'])
        if m:
            start_dt = start_dt or _to_datetime(m.group(1))
            end_dt = end_dt or _to_datetime(m.group(2))

    time_info = course.get('time') or {}
    begin_hhmm = time12h_to_hhmm(time_info.get('start')) if time_info else None
    end_hhmm = time12h_to_hhmm(time_info.get('end')) if time_info else None

    return [
        None,                                       # Changes
        subject,                                    # Subject Code
        course_num,                                 # Course Number
        title,                                      # Course
        section_title or None,                      # Section Title
        course.get('gwid') or None,                 # Instructor GWID
        last or None,                               # Instructor Last Name
        first or None,                              # Instructor First Name
        credits_to_number(course.get('credits')),   # Credits
        course.get('max_enrollment'),               # Max Enrollment
        course.get('prior_enrollment'),             # Prior Enrollment
        course.get('wait_capacity'),                # Wait Capacity
        start_dt,                                    # Course Start Date
        end_dt,                                      # Course End Date
        course.get('days') or None,                 # Weekly Meeting Pattern
        begin_hhmm,                                 # Begin Time HHMM
        end_hhmm,                                   # End Time HHMM
        course.get('comment') or None,              # Comment
    ]


def write_registrar_xlsx(courses: List[Dict], path: str, sheet_name: str = 'Export'):
    """Write a list of course dictionaries to a registrar-format .xlsx file."""
    _require_openpyxl()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name

    ws.append(REGISTRAR_COLUMNS)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    date_style = 'mm/dd/yyyy'
    for course in courses:
        row = _registrar_row(course)
        ws.append(row)
        # Format the two date cells (columns 13 and 14).
        r = ws.max_row
        for col in (13, 14):
            c = ws.cell(row=r, column=col)
            if isinstance(c.value, datetime):
                c.number_format = date_style

    # Reasonable column widths for readability.
    widths = [9, 12, 13, 30, 22, 14, 18, 18, 8, 8, 8, 8, 16, 16, 10, 10, 10, 40]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    wb.save(path)
    return path
