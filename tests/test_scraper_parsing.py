#!/usr/bin/env python3
"""Unit tests for the core CourseScraper HTML/time/day parsing logic.

Run from the repo root:
    python -m unittest discover -s tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from gwu_scraper import CourseScraper


class TestParseTime(unittest.TestCase):
    def setUp(self):
        self.s = CourseScraper()

    def test_basic(self):
        t = self.s.parse_time('02:20PM - 03:35PM')
        self.assertEqual(t, {'start': '02:20PM', 'end': '03:35PM',
                             'raw': '02:20PM - 03:35PM'})

    def test_with_surrounding_text(self):
        t = self.s.parse_time('TR 02:20PM - 03:35PM')
        self.assertIsNotNone(t)
        self.assertEqual(t['start'], '02:20PM')

    def test_arranged_returns_none(self):
        self.assertIsNone(self.s.parse_time('ARR'))
        self.assertIsNone(self.s.parse_time(''))
        self.assertIsNone(self.s.parse_time(None))

    def test_unparseable_returns_none(self):
        self.assertIsNone(self.s.parse_time('TBA'))


class TestParseDays(unittest.TestCase):
    def setUp(self):
        self.s = CourseScraper()

    def test_valid_patterns(self):
        self.assertEqual(self.s.parse_days('MW'), 'MW')
        self.assertEqual(self.s.parse_days('TR'), 'TR')
        self.assertEqual(self.s.parse_days('MWF'), 'MWF')

    def test_strips_non_day_chars(self):
        self.assertEqual(self.s.parse_days(' M W '), 'MW')
        self.assertEqual(self.s.parse_days('T/R'), 'TR')

    def test_empty_returns_none(self):
        self.assertIsNone(self.s.parse_days(''))
        self.assertIsNone(self.s.parse_days(None))
        self.assertIsNone(self.s.parse_days('XYZ'))  # no valid day letters


class TestDetectTotalPages(unittest.TestCase):
    def setUp(self):
        self.s = CourseScraper()

    def test_single_page(self):
        self.assertEqual(self.s.detect_total_pages('<html>no pagination</html>'), 1)

    def test_multiple_pages(self):
        html = "goToPage('1') goToPage('2') goToPage('3')"
        self.assertEqual(self.s.detect_total_pages(html), 3)


class TestSubjectFallbackFromUrl(unittest.TestCase):
    def test_subject_extracted(self):
        s = CourseScraper(url='https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=CSCI')
        self.assertEqual(s.subject_code, 'CSCI')

    def test_no_url_no_subject(self):
        self.assertIsNone(CourseScraper().subject_code)


# A minimal page mirroring GWU's table structure (see CLAUDE.md cell layout).
_PAGE_HTML = """
<table class="courseListing">
  <tr class="crseRow1">
    <td>OPEN</td>
    <td>46234</td>
    <td><span style="font-weight:bold;">GEOG</span><a href="#"><span>1001</span></a></td>
    <td>10</td>
    <td>Introduction to Human Geography</td>
    <td>3.00</td>
    <td>Chacko, E</td>
    <td><a href="#">1957 E</a> B12</td>
    <td>TR\n02:20PM - 03:35PM</td>
    <td>01/12/26 - 04/27/26</td>
  </tr>
  <tr class="crseRow1" style="display:none">
    <td>OPEN</td><td>99999</td>
    <td><span style="font-weight:bold;">GEOG</span><a href="#"><span>9999</span></a></td>
    <td>99</td><td>Hidden Row</td><td>3.00</td><td>Nobody, X</td>
    <td><a href="#">X</a> Y</td><td>MW\n09:00AM - 10:00AM</td><td>01/12/26 - 04/27/26</td>
  </tr>
</table>
"""


class TestParsePageHtml(unittest.TestCase):
    def setUp(self):
        self.s = CourseScraper()

    def test_parses_expected_fields(self):
        soup = BeautifulSoup(_PAGE_HTML, 'html.parser')
        found = self.s.parse_page_html(soup)
        self.assertEqual(found, 1)  # hidden row skipped
        # parse_page_html stores parsed rows in courses_by_crn (deduped by CRN).
        self.assertIn('46234', self.s.courses_by_crn)
        c = self.s.courses_by_crn['46234']
        self.assertEqual(c['status'], 'OPEN')
        self.assertEqual(c['crn'], '46234')
        self.assertEqual(c['subject'], 'GEOG')
        self.assertEqual(c['course_num'], '1001')
        self.assertEqual(c['section'], '10')
        self.assertEqual(c['title'], 'Introduction to Human Geography')
        self.assertEqual(c['credits'], '3.00')
        self.assertEqual(c['instructor'], 'Chacko, E')
        self.assertEqual(c['days'], 'TR')
        self.assertEqual(c['time']['raw'], '02:20PM - 03:35PM')
        self.assertEqual(c['building'], '1957 E')
        self.assertEqual(c['room'], 'B12')
        self.assertEqual(c['course_number'], 'GEOG 1001')

    def test_hidden_rows_skipped(self):
        soup = BeautifulSoup(_PAGE_HTML, 'html.parser')
        self.s.parse_page_html(soup)
        self.assertNotIn('99999', self.s.courses_by_crn)


if __name__ == '__main__':
    unittest.main()
