#!/usr/bin/env python3
"""Unit tests for the core CourseScraper HTML/time/day parsing logic.

Run from the repo root:
    python -m unittest discover -s tests
"""

import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
import gwu_scraper
from gwu_scraper import CourseScraper, build_gwu_url, build_html_calendar, generate_html_calendar


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


def _row(crn='46234', subject='GEOG', course_num='1001', section='10',
         location='<a href="#">1957 E</a> B12', day_time='TR\n02:20PM - 03:35PM',
         dates='01/12/26 - 04/27/26', extra_cells=True):
    """One GWU course row; pass pieces to exercise parser edge cases."""
    subject_html = f'<span style="font-weight:bold;">{subject}</span>' if subject else ''
    num_html = f'<a href="#"><span>{course_num}</span></a>' if course_num else ''
    cells = ['OPEN', crn, subject_html + num_html, section, 'Intro Course', '3.00',
             'Chacko, E', location, day_time, dates]
    if not extra_cells:
        cells = cells[:6]
    return '<tr class="crseRow1">' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>'


def _page(*rows, pages=1):
    nav = ' '.join(f"goToPage('{n}')" for n in range(1, pages + 1)) if pages > 1 else ''
    return f'<div>{nav}</div><table class="courseListing">{"".join(rows)}</table>'


def _parse(*rows, scraper=None):
    s = scraper or CourseScraper()
    s.parse_page_html(BeautifulSoup(_page(*rows), 'html.parser'))
    return s.courses_by_crn


class TestParseRowEdgeCases(unittest.TestCase):
    def test_short_row_skipped(self):
        self.assertEqual(_parse(_row(extra_cells=False)), {})

    def test_missing_location_is_not_specified(self):
        c = _parse(_row(location=''))['46234']
        self.assertEqual((c['building'], c['room']), ('Not specified', 'Not specified'))

    def test_location_without_link_splits_last_token_as_room(self):
        c = _parse(_row(location='1957 E B12'))['46234']
        self.assertEqual((c['building'], c['room']), ('1957 E', 'B12'))

    def test_single_token_location_is_building_only(self):
        c = _parse(_row(location='ONLINE'))['46234']
        self.assertEqual((c['building'], c['room']), ('ONLINE', 'Not specified'))

    def test_br_separated_day_time(self):
        # Real pages use <br>; get_text(strip=True) joins it without a newline.
        c = _parse(_row(day_time='TR<br>02:20PM - 03:35PM'))['46234']
        self.assertEqual(c['days'], 'TR')
        self.assertEqual(c['time']['start'], '02:20PM')

    def test_arranged_time_row_skipped(self):
        self.assertEqual(_parse(_row(day_time='ARR\nTBA')), {})

    def test_missing_dates_uses_default(self):
        self.assertEqual(_parse(_row(dates=''))['46234']['dates'], '01/12/26 - 04/27/26')

    def test_course_number_falls_back_to_section(self):
        self.assertEqual(_parse(_row(course_num=''))['46234']['course_number'], 'GEOG 10')

    def test_duplicate_crn_prefers_row_with_subject(self):
        c = _parse(_row(subject='', course_num='6306'), _row(course_num='6306'))
        self.assertEqual(c['46234']['subject'], 'GEOG')

    def test_duplicate_crn_keeps_existing_row_with_subject(self):
        c = _parse(_row(section='10'), _row(subject='', section='80'))
        self.assertEqual((c['46234']['subject'], c['46234']['section']), ('GEOG', '10'))

    def test_duplicate_crn_both_with_subject_keeps_first(self):
        c = _parse(_row(section='10'), _row(section='80'))
        self.assertEqual(c['46234']['section'], '10')


class TestBuildGwuUrl(unittest.TestCase):
    def test_builds_expected_url(self):
        self.assertEqual(build_gwu_url('2026', '01', 'GEOG'),
                         'https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=GEOG')

    def test_normalizes_case_and_whitespace(self):
        self.assertTrue(build_gwu_url(' 2026 ', ' 03 ', ' csci ').endswith('termId=202603&subjId=CSCI'))

    def test_accepts_int_year(self):
        self.assertIn('termId=202702', build_gwu_url(2027, '02', 'MATH'))

    def test_rejects_bad_input(self):
        bad = [('26', '01', 'GEOG'), ('1999', '01', 'GEOG'), ('2100', '01', 'GEOG'),
               ('2026', '1', 'GEOG'), ('2026', '04', 'GEOG'), ('2026', '01', 'G'),
               ('2026', '01', 'GEOGRA'), ('2026', '01', 'GE0G'),
               ('2026', '01', 'GEOG&x=1'), ('2026', '01', '')]
        for args in bad:
            with self.subTest(args=args), self.assertRaises(ValueError):
                build_gwu_url(*args)


def _response(text):
    r = mock.Mock(text=text)
    r.raise_for_status = mock.Mock()
    return r


class TestScrape(unittest.TestCase):
    URL = 'https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=GEOG'

    def test_fetches_every_page_and_combines(self):
        pages = [_page(_row(crn='1'), _row(crn='2'), pages=3),
                 _page(_row(crn='3')), _page(_row(crn='4'))]
        with mock.patch.object(gwu_scraper.requests, 'get',
                               side_effect=[_response(p) for p in pages]) as get:
            courses = CourseScraper(url=self.URL).scrape()
        self.assertEqual(sorted(c['crn'] for c in courses), ['1', '2', '3', '4'])
        urls = [call.args[0] for call in get.call_args_list]
        self.assertEqual(urls, [self.URL, self.URL + '&pageNum=2', self.URL + '&pageNum=3'])

    def test_same_crn_across_pages_counted_once(self):
        pages = [_page(_row(crn='1'), pages=2), _page(_row(crn='1'))]
        with mock.patch.object(gwu_scraper.requests, 'get',
                               side_effect=[_response(p) for p in pages]):
            self.assertEqual(len(CourseScraper(url=self.URL).scrape()), 1)

    def test_network_error_returns_empty_list(self):
        with mock.patch.object(gwu_scraper.requests, 'get',
                               side_effect=gwu_scraper.requests.ConnectionError('down')):
            self.assertEqual(CourseScraper(url=self.URL).scrape(), [])

    def test_http_error_returns_empty_list(self):
        r = _response('')
        r.raise_for_status.side_effect = gwu_scraper.requests.HTTPError('403')
        with mock.patch.object(gwu_scraper.requests, 'get', return_value=r):
            self.assertEqual(CourseScraper(url=self.URL).scrape(), [])

    def test_text_content_needs_no_network(self):
        with mock.patch.object(gwu_scraper.requests, 'get') as get:
            courses = CourseScraper(text_content=_page(_row())).scrape()
        get.assert_not_called()
        self.assertEqual(len(courses), 1)

    def test_no_source_raises(self):
        with self.assertRaises(ValueError):
            CourseScraper().scrape()


class TestOfflineCalendar(unittest.TestCase):
    COURSE = {'crn': '1', 'subject': 'GEOG', 'course_num': '1001', 'section': '10',
              'title': 'Intro', 'credits': '3.00', 'instructor': 'Chacko, E', 'days': 'TR',
              'time': {'start': '02:20PM', 'end': '03:35PM', 'raw': '02:20PM - 03:35PM'},
              'dates': '01/12/26 - 04/27/26', 'building': '1957 E', 'room': 'B12',
              'status': 'OPEN', 'course_number': 'GEOG 1001'}

    def test_offline_build_has_no_web_only_parts(self):
        html = build_html_calendar([self.COURSE], year='2026', semester='01')
        for marker in ('<!--WEB_BACK_BUTTON-->', '<!--WEB_EXPORT_BUTTON-->',
                       '//WEB_EXPORT_SCRIPT', 'exportToRegistrarServer', '/export/xlsx'):
            self.assertNotIn(marker, html)
        self.assertIn('<title>GWU Courses - Spring 2026</title>', html)

    def test_web_build_has_web_only_parts(self):
        html = build_html_calendar([self.COURSE], web_export=True)
        self.assertIn('exportToRegistrarServer', html)
        self.assertIn('New calendar', html)

    def test_generate_writes_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'cal.html')
            generate_html_calendar([self.COURSE], path)
            with open(path, encoding='utf-8') as f:
                self.assertIn('Chacko, E', f.read())


if __name__ == '__main__':
    unittest.main()
