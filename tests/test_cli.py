#!/usr/bin/env python3
"""Smoke tests for the gwu_scraper.py command line (no network calls).

Run from the repo root:
    python -m unittest discover -s tests
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openpyxl
import gwu_scraper
import registrar_io

PAGE = """
<table class="courseListing"><tr class="crseRow1">
  <td>OPEN</td><td>46234</td>
  <td><span style="font-weight:bold;">GEOG</span><a href="#"><span>1001</span></a></td>
  <td>10</td><td>Intro to Human Geography</td><td>3.00</td><td>Chacko, E</td>
  <td><a href="#">1957 E</a> B12</td><td>TR<br>02:20PM - 03:35PM</td><td>01/12/26 - 04/27/26</td>
</tr></table>
"""


def run_cli(*argv):
    """Run main() with argv; return (exit code, captured stdout)."""
    out = io.StringIO()
    with mock.patch.object(sys, 'argv', ['gwu_scraper.py', *argv]), \
            contextlib.redirect_stdout(out):
        code = gwu_scraper.main()
    return code, out.getvalue()


class TestCli(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name
        self.html = os.path.join(self.dir, 'cal.html')
        self.json = os.path.join(self.dir, 'data.json')

    def tearDown(self):
        self._tmp.cleanup()

    def _path(self, name):
        return os.path.join(self.dir, name)

    def _registrar_file(self):
        path = self._path('in.xlsx')
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(registrar_io.REGISTRAR_COLUMNS)
        ws.append([None, 'GEOG', '1001', '10', 'Intro to Human Geography', None, 'G1',
                   'Chacko', 'Elizabeth', 3, 120, 117, 40, datetime(2027, 1, 11),
                   datetime(2027, 4, 26), 'TR', '1420', '1535', None])
        ws.append([None, 'GEOG', '3998', '10', 'Arranged', None, None, 'Mann', 'M', 3,
                   10, 1, 0, datetime(2027, 1, 11), datetime(2027, 4, 26), None,
                   '####', '####', None])
        wb.save(path)
        return path

    def test_text_file_writes_calendar_and_json(self):
        page = self._path('page.html')
        with open(page, 'w', encoding='utf-8') as f:
            f.write(PAGE)
        code, _ = run_cli('--text-file', page, '--output', self.html, '--json', self.json)
        self.assertEqual(code, 0)
        with open(self.json, encoding='utf-8') as f:
            self.assertEqual(json.load(f)[0]['crn'], '46234')
        with open(self.html, encoding='utf-8') as f:
            self.assertIn('Chacko, E', f.read())

    def test_xlsx_in_keeps_tba_in_json_but_not_calendar(self):
        code, out = run_cli('--xlsx-in', self._registrar_file(),
                            '--output', self.html, '--json', self.json)
        self.assertEqual(code, 0)
        self.assertIn('1 scheduled, 1 arranged/TBA', out)
        with open(self.json, encoding='utf-8') as f:
            self.assertEqual(len(json.load(f)), 2)
        with open(self.html, encoding='utf-8') as f:
            self.assertNotIn('Arranged', f.read())

    def test_xlsx_in_to_xlsx_out_round_trip(self):
        out_xlsx = self._path('out.xlsx')
        code, _ = run_cli('--xlsx-in', self._registrar_file(), '--xlsx-out', out_xlsx,
                          '--output', self.html, '--json', self.json)
        self.assertEqual(code, 0)
        courses = registrar_io.read_registrar_xlsx(out_xlsx)
        self.assertEqual(len(courses), 2)
        self.assertEqual(courses[0]['instructor_first'], 'Elizabeth')

    def test_url_sets_semester_title(self):
        url = 'https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202603&subjId=GEOG'
        with mock.patch.object(gwu_scraper.CourseScraper, 'scrape',
                               return_value=[_scraped()]):
            code, _ = run_cli('--url', url, '--output', self.html, '--json', self.json)
        self.assertEqual(code, 0)
        with open(self.html, encoding='utf-8') as f:
            self.assertIn('GWU Courses - Fall 2026', f.read())

    def test_no_courses_exits_1(self):
        with mock.patch.object(gwu_scraper.CourseScraper, 'scrape', return_value=[]):
            code, out = run_cli('--output', self.html, '--json', self.json)
        self.assertEqual(code, 1)
        self.assertIn('No courses found', out)
        self.assertFalse(os.path.exists(self.html))

    def test_missing_input_file_exits_1(self):
        code, out = run_cli('--xlsx-in', self._path('nope.xlsx'),
                            '--output', self.html, '--json', self.json)
        self.assertEqual(code, 1)
        self.assertIn('ERROR', out)


def _scraped():
    s = gwu_scraper.CourseScraper(text_content=PAGE)
    with contextlib.redirect_stdout(io.StringIO()):
        return s.scrape()[0]


if __name__ == '__main__':
    unittest.main()
