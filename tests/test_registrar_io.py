#!/usr/bin/env python3
"""Unit tests for registrar_io: .xlsx <-> course-dict conversion.

Run from the repo root:
    python -m unittest discover -s tests
or:
    python -m pytest tests/
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime

# Make the repo root importable when run directly or via discovery.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import registrar_io as rio


class TestTimeConverters(unittest.TestCase):
    def test_hhmm_to_12h_basic(self):
        self.assertEqual(rio.hhmm_to_12h('1420'), '02:20PM')
        self.assertEqual(rio.hhmm_to_12h('0900'), '09:00AM')
        self.assertEqual(rio.hhmm_to_12h('1110'), '11:10AM')
        self.assertEqual(rio.hhmm_to_12h('1635'), '04:35PM')

    def test_hhmm_to_12h_noon_and_midnight(self):
        self.assertEqual(rio.hhmm_to_12h('1200'), '12:00PM')  # noon
        self.assertEqual(rio.hhmm_to_12h('0000'), '12:00AM')  # midnight
        self.assertEqual(rio.hhmm_to_12h('2359'), '11:59PM')

    def test_hhmm_to_12h_accepts_int_and_short(self):
        self.assertEqual(rio.hhmm_to_12h(900), '09:00AM')   # int, 3-digit
        self.assertEqual(rio.hhmm_to_12h(1420), '02:20PM')

    def test_hhmm_to_12h_tba_returns_none(self):
        for bad in ('####', '', None, '  ', 'ARR'):
            self.assertIsNone(rio.hhmm_to_12h(bad), f"expected None for {bad!r}")

    def test_hhmm_to_12h_out_of_range_returns_none(self):
        self.assertIsNone(rio.hhmm_to_12h('2500'))
        self.assertIsNone(rio.hhmm_to_12h('1290'))

    def test_time12h_to_hhmm_basic(self):
        self.assertEqual(rio.time12h_to_hhmm('02:20PM'), '1420')
        self.assertEqual(rio.time12h_to_hhmm('09:00AM'), '0900')
        self.assertEqual(rio.time12h_to_hhmm('12:00PM'), '1200')
        self.assertEqual(rio.time12h_to_hhmm('12:00AM'), '0000')

    def test_time12h_to_hhmm_unparseable(self):
        self.assertIsNone(rio.time12h_to_hhmm(''))
        self.assertIsNone(rio.time12h_to_hhmm(None))
        self.assertIsNone(rio.time12h_to_hhmm('TBA'))

    def test_time_round_trip(self):
        for hhmm in ('0900', '1110', '1420', '1635', '1200', '0000'):
            self.assertEqual(rio.time12h_to_hhmm(rio.hhmm_to_12h(hhmm)), hhmm)


class TestCreditsConverters(unittest.TestCase):
    def test_to_display(self):
        self.assertEqual(rio.credits_to_display(3), '3.00')
        self.assertEqual(rio.credits_to_display(0), '0.00')
        self.assertEqual(rio.credits_to_display(1), '1.00')
        self.assertEqual(rio.credits_to_display(1.5), '1.50')

    def test_to_display_blank(self):
        self.assertEqual(rio.credits_to_display(None), '')
        self.assertEqual(rio.credits_to_display(''), '')

    def test_to_number_whole_is_int(self):
        self.assertEqual(rio.credits_to_number('3.00'), 3)
        self.assertIsInstance(rio.credits_to_number('3.00'), int)

    def test_to_number_fractional_is_float(self):
        self.assertEqual(rio.credits_to_number('1.50'), 1.5)

    def test_to_number_blank(self):
        self.assertIsNone(rio.credits_to_number(None))
        self.assertIsNone(rio.credits_to_number(''))


class TestInstructorConverters(unittest.TestCase):
    def test_build_display(self):
        self.assertEqual(rio.build_instructor_display('Chacko', 'Elizabeth'), 'Chacko, E')
        self.assertEqual(rio.build_instructor_display("O'Brien", 'Maya'), "O'Brien, M")

    def test_build_display_no_first(self):
        self.assertEqual(rio.build_instructor_display('Staff', ''), 'Staff')
        self.assertEqual(rio.build_instructor_display('Staff', None), 'Staff')

    def test_build_display_blank_last(self):
        self.assertEqual(rio.build_instructor_display('', 'Elizabeth'), '')
        self.assertEqual(rio.build_instructor_display(None, None), '')

    def test_split_display(self):
        self.assertEqual(rio.split_instructor_display('Chacko, E'), ('Chacko', 'E'))
        self.assertEqual(rio.split_instructor_display("O'Brien, M"), ("O'Brien", 'M'))

    def test_split_display_single_name(self):
        self.assertEqual(rio.split_instructor_display('Staff'), ('Staff', ''))

    def test_split_display_empty(self):
        self.assertEqual(rio.split_instructor_display(''), ('', ''))
        self.assertEqual(rio.split_instructor_display(None), ('', ''))


class TestStatusAndDates(unittest.TestCase):
    def test_derive_status_open(self):
        self.assertEqual(rio.derive_status(120, 117), 'OPEN')
        self.assertEqual(rio.derive_status(35, 0), 'OPEN')

    def test_derive_status_closed_when_full(self):
        self.assertEqual(rio.derive_status(25, 26), 'CLOSED')  # over capacity
        self.assertEqual(rio.derive_status(20, 20), 'CLOSED')  # exactly full

    def test_derive_status_defaults_open_on_bad_data(self):
        self.assertEqual(rio.derive_status(None, None), 'OPEN')
        self.assertEqual(rio.derive_status('', ''), 'OPEN')
        self.assertEqual(rio.derive_status(0, 0), 'OPEN')  # max 0 -> not "closed"

    def test_fmt_date(self):
        self.assertEqual(rio.fmt_date(datetime(2027, 1, 11)), '01/11/27')
        self.assertEqual(rio.fmt_date(None), '')
        self.assertEqual(rio.fmt_date('01/11/27'), '01/11/27')

    def test_to_datetime_parses_formats(self):
        self.assertEqual(rio._to_datetime('2027-01-11'), datetime(2027, 1, 11))
        self.assertEqual(rio._to_datetime('01/11/2027'), datetime(2027, 1, 11))
        self.assertEqual(rio._to_datetime('01/11/27'), datetime(2027, 1, 11))

    def test_to_datetime_passthrough_and_none(self):
        dt = datetime(2027, 4, 26)
        self.assertEqual(rio._to_datetime(dt), dt)
        self.assertIsNone(rio._to_datetime(''))
        self.assertIsNone(rio._to_datetime(None))


def _make_registrar_workbook(path, rows):
    """Write a minimal registrar-format workbook for read tests."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Export'
    ws.append(rio.REGISTRAR_COLUMNS)
    for row in rows:
        ws.append(row)
    wb.save(path)


# Column order matches rio.REGISTRAR_COLUMNS:
# Changes, Subject Code, Course Number, Course, Section Title, GWID,
# Section, Course, Section Title, GWID, Last, First, Credits, Max, Prior, Wait,
# Start, End, Pattern, Begin, End, Comment
_SCHEDULED = [None, 'GEOG', '1001', '10', 'Intro to Human Geography', None,
              'G10715190', 'Chacko', 'Elizabeth', 3, 120, 117, 40,
              datetime(2027, 1, 11), datetime(2027, 4, 26), 'TR', '1420', '1535', None]
_SPECIAL_TOPIC = [None, 'GEOG', '3195', '80', 'Special Topics in Human Geog',
                  'Global Environmental Justice', 'G22598702', 'Odell', 'Scott',
                  3, 20, 16, 40, datetime(2027, 1, 11), datetime(2027, 4, 26),
                  'R', '1710', '1900', 'Some comment.']
_TBA = [None, 'GEOG', '6999', '10', 'Thesis Research', None, 'G17436241', 'Rain', 'David',
        6, 10, 6, 0, datetime(2027, 1, 11), datetime(2027, 4, 26), None,
        '####', '####', 'Instructor Approval Required to Register.']
_FULL = [None, 'GEOG', '2127', '10', 'Population Geography', None, 'G24949761', 'Gardner',
         'Todd', 3, 24, 26, 40, datetime(2027, 1, 11), datetime(2027, 4, 26),
         'R', '1710', '1900', None]  # prior(26) > max(24) -> CLOSED


class TestReadRegistrar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, 'sched.xlsx')

    def test_read_scheduled_course(self):
        _make_registrar_workbook(self.path, [_SCHEDULED])
        courses = rio.read_registrar_xlsx(self.path)
        self.assertEqual(len(courses), 1)
        c = courses[0]
        self.assertEqual(c['subject'], 'GEOG')
        self.assertEqual(c['course_num'], '1001')
        self.assertEqual(c['course_number'], 'GEOG 1001')
        self.assertEqual(c['instructor'], 'Chacko, E')
        self.assertEqual(c['days'], 'TR')
        self.assertEqual(c['time']['raw'], '02:20PM - 03:35PM')
        self.assertEqual(c['credits'], '3.00')
        self.assertEqual(c['dates'], '01/11/27 - 04/26/27')
        self.assertEqual(c['status'], 'OPEN')
        # registrar-only pass-through preserved
        self.assertEqual(c['gwid'], 'G10715190')
        self.assertEqual(c['max_enrollment'], 120)
        self.assertEqual(c['section'], '10')
        self.assertEqual(c['source'], 'registrar')

    def test_special_topic_subtitle_folded(self):
        _make_registrar_workbook(self.path, [_SPECIAL_TOPIC])
        c = rio.read_registrar_xlsx(self.path)[0]
        self.assertEqual(c['title'], 'Special Topics in Human Geog - Global Environmental Justice')
        self.assertEqual(c['section_title'], 'Global Environmental Justice')

    def test_tba_course_has_no_time(self):
        _make_registrar_workbook(self.path, [_TBA])
        c = rio.read_registrar_xlsx(self.path)[0]
        self.assertIsNone(c['time'])
        self.assertEqual(c['days'], '')
        self.assertEqual(c['comment'], 'Instructor Approval Required to Register.')

    def test_status_derived_closed_when_full(self):
        _make_registrar_workbook(self.path, [_FULL])
        c = rio.read_registrar_xlsx(self.path)[0]
        self.assertEqual(c['status'], 'CLOSED')

    def test_synthetic_crns_are_unique(self):
        _make_registrar_workbook(self.path, [_SCHEDULED, _SPECIAL_TOPIC, _TBA])
        courses = rio.read_registrar_xlsx(self.path)
        crns = [c['crn'] for c in courses]
        self.assertEqual(len(crns), len(set(crns)), "CRNs must be unique")

    def test_blank_rows_skipped(self):
        blank = [None] * len(rio.REGISTRAR_COLUMNS)
        _make_registrar_workbook(self.path, [_SCHEDULED, blank, _TBA])
        self.assertEqual(len(rio.read_registrar_xlsx(self.path)), 2)

    def test_missing_header_raises(self):
        import openpyxl
        wb = openpyxl.Workbook()
        wb.active.append(['Not', 'A', 'Registrar', 'File'])
        wb.save(self.path)
        with self.assertRaises(ValueError):
            rio.read_registrar_xlsx(self.path)


class TestRoundTrip(unittest.TestCase):
    """Read -> write -> read must preserve all dashboard + pass-through fields."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.src = os.path.join(self.tmp, 'src.xlsx')
        self.dst = os.path.join(self.tmp, 'dst.xlsx')

    def test_round_trip_fidelity(self):
        _make_registrar_workbook(self.src, [_SCHEDULED, _SPECIAL_TOPIC, _TBA, _FULL])
        original = rio.read_registrar_xlsx(self.src)
        rio.write_registrar_xlsx(original, self.dst)
        reread = rio.read_registrar_xlsx(self.dst)

        self.assertEqual(len(original), len(reread))
        fields = ('subject', 'course_num', 'section', 'title', 'instructor', 'days', 'time',
                  'credits', 'dates', 'status', 'gwid', 'comment', 'section_title',
                  'max_enrollment', 'prior_enrollment', 'wait_capacity')
        for a, b in zip(original, reread):
            for f in fields:
                self.assertEqual(a.get(f), b.get(f),
                                 f"field {f} changed on round-trip for {a['course_number']}")

    def test_write_from_scraped_shape(self):
        """Website-scraped courses (no registrar fields) still export cleanly."""
        scraped = [{
            'status': 'OPEN', 'crn': '55305', 'subject': 'GEOG', 'course_num': '1000',
            'section': '10', 'title': 'Migrants in the City', 'credits': '3.00',
            'instructor': 'Chacko, E', 'days': 'MW',
            'time': {'start': '11:10AM', 'end': '12:25PM', 'raw': '11:10AM - 12:25PM'},
            'dates': '08/24/26 - 12/08/26', 'building': '1776 G', 'room': 'C-117',
            'course_number': 'GEOG 1000',
        }]
        rio.write_registrar_xlsx(scraped, self.dst)
        c = rio.read_registrar_xlsx(self.dst)[0]
        self.assertEqual(c['subject'], 'GEOG')
        self.assertEqual(c['instructor'], 'Chacko, E')  # last + initial recovered
        self.assertEqual(c['days'], 'MW')
        self.assertEqual(c['time']['raw'], '11:10AM - 12:25PM')
        self.assertEqual(c['credits'], '3.00')


def _make_workbook_with_headers(path, headers, rows):
    """Write a workbook with arbitrary header names (for variant-matching tests)."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Export'
    ws.append(headers)
    for row in rows:
        ws.append(row)
    wb.save(path)


class TestHeaderVariants(unittest.TestCase):
    """The reader must tolerate spelling/spacing/casing and combined columns."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, 'variant.xlsx')

    def test_messy_spacing_and_casing(self):
        # Extra spaces, lowercase, trailing space — all should still match.
        headers = ['Changes', 'subject  code', 'Course  Number', 'SECTION', 'Course', 'Section Title',
                   'Instructor GWID', 'instructor last name ', 'Instructor First name',
                   'Credits', 'Max Enrollment', 'Prior Enrollment', 'Wait Capacity',
                   'Course Start Date', 'Course End Date', 'Weekly Meeting Pattern',
                   'Begin Time HHMM', 'End Time HHMM', 'Comment']
        _make_workbook_with_headers(self.path, headers, [_SCHEDULED])
        courses, warnings = rio.read_registrar_xlsx(self.path, return_warnings=True)
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0]['instructor'], 'Chacko, E')
        self.assertEqual(courses[0]['subject'], 'GEOG')
        self.assertEqual(courses[0]['section'], '10')
        self.assertEqual(warnings, [])

    def test_combined_instructor_column(self):
        # A single "Instructor" column holding "Last, First".
        headers = ['Subject Code', 'Course Number', 'Course', 'Instructor',
                   'Credits', 'Weekly Meeting Pattern', 'Begin Time HHMM', 'End Time HHMM']
        row = ['GEOG', '1001', 'Intro to Human Geography', 'Chacko, Elizabeth',
               3, 'TR', '1420', '1535']
        _make_workbook_with_headers(self.path, headers, [row])
        c = rio.read_registrar_xlsx(self.path)[0]
        self.assertEqual(c['instructor'], 'Chacko, E')
        self.assertEqual(c['instructor_last'], 'Chacko')
        self.assertEqual(c['instructor_first'], 'Elizabeth')

    def test_missing_instructor_columns_warns_and_staff(self):
        headers = ['Subject Code', 'Course Number', 'Course',
                   'Credits', 'Weekly Meeting Pattern', 'Begin Time HHMM', 'End Time HHMM']
        row = ['GEOG', '1001', 'Intro to Human Geography', 3, 'TR', '1420', '1535']
        _make_workbook_with_headers(self.path, headers, [row])
        courses, warnings = rio.read_registrar_xlsx(self.path, return_warnings=True)
        self.assertEqual(courses[0]['instructor'], 'Staff')
        self.assertTrue(any('instructor' in w.lower() for w in warnings))

    def test_staff_row_exports_blank_not_staff(self):
        # An unassigned row reads as 'Staff' but must round-trip to blank, not 'Staff'.
        _make_registrar_workbook(self.path, [_SCHEDULED, _STAFF_ROW])
        courses = rio.read_registrar_xlsx(self.path)
        staff = courses[1]
        self.assertEqual(staff['instructor'], 'Staff')
        self.assertEqual(staff['instructor_last'], '')
        dst = os.path.join(self.tmp, 'out.xlsx')
        rio.write_registrar_xlsx(courses, dst)
        reread = rio.read_registrar_xlsx(dst)
        self.assertEqual(reread[1]['instructor'], 'Staff')   # still Staff on re-read
        # And the written Last Name cell is empty (not the literal 'Staff').
        import openpyxl
        ws = openpyxl.load_workbook(dst).active
        last_name_col = rio.REGISTRAR_COLUMNS.index('Instructor Last Name') + 1
        self.assertIn(ws.cell(row=3, column=last_name_col).value, (None, ''))


class TestBytesIO(unittest.TestCase):
    """Reading/writing via in-memory BytesIO (for the stateless web server)."""

    def test_write_then_read_bytesio(self):
        from io import BytesIO
        # Build a source workbook in memory.
        src = BytesIO()
        _make_registrar_workbook(src, [_SCHEDULED, _SPECIAL_TOPIC, _TBA])
        src.seek(0)
        courses = rio.read_registrar_xlsx(src)
        self.assertEqual(len(courses), 3)
        # Write to a BytesIO and read it back — no disk involved.
        out = BytesIO()
        rio.write_registrar_xlsx(courses, out)
        out.seek(0)
        reread = rio.read_registrar_xlsx(out)
        self.assertEqual([c['instructor'] for c in reread],
                         [c['instructor'] for c in courses])


# A genuinely unassigned ("Staff") row: empty GWID/last/first.
_STAFF_ROW = [None, 'GEOG', '1002', '10', 'Intro-Physical Geography', None,
              None, None, None, 4, 100, 99, 0,
              datetime(2027, 1, 11), datetime(2027, 4, 26), 'MW', '1110', '1225', None]


if __name__ == '__main__':
    unittest.main()
