#!/usr/bin/env python3
"""Flask route tests for the web app (no network calls).

Run from the repo root:
    python -m unittest discover -s tests
"""

import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openpyxl
import registrar_io
from app import app


def _registrar_xlsx_bytes():
    """Build a tiny valid registrar .xlsx in memory."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Export'
    ws.append(registrar_io.REGISTRAR_COLUMNS)
    from datetime import datetime
    ws.append([None, 'GEOG', '1001', '10', 'Intro to Human Geography', None,
               'G10715190', 'Chacko', 'Elizabeth', 3, 120, 117, 40,
               datetime(2027, 1, 11), datetime(2027, 4, 26), 'TR', '1420', '1535', None])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_ok(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Scrape a subject', r.data)
        self.assertIn(b'Upload registrar', r.data)

    def test_health(self):
        r = self.client.get('/health')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, b'ok')

    def test_scrape_bad_subject_400(self):
        # Invalid subject -> build_gwu_url raises -> 400, no network hit.
        r = self.client.post('/scrape', data={'year': '2026', 'semester': '01', 'subject': '1'})
        self.assertEqual(r.status_code, 400)

    def test_scrape_bad_year_400(self):
        r = self.client.post('/scrape', data={'year': '26', 'semester': '01', 'subject': 'GEOG'})
        self.assertEqual(r.status_code, 400)

    def test_upload_non_xlsx_400(self):
        r = self.client.post('/upload', data={
            'file': (io.BytesIO(b'not a spreadsheet'), 'notes.txt')},
            content_type='multipart/form-data')
        self.assertEqual(r.status_code, 400)

    def test_upload_valid_renders_calendar(self):
        r = self.client.post('/upload', data={
            'file': (io.BytesIO(_registrar_xlsx_bytes()), 'sched.xlsx')},
            content_type='multipart/form-data')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'text/html', r.content_type.encode())
        # The web-export button should be present in web mode.
        self.assertIn(b'exportToRegistrarServer', r.data)
        self.assertIn(b'Chacko', r.data)

    def test_export_xlsx_ok(self):
        courses = [{
            'subject': 'GEOG', 'course_num': '1001', 'title': 'Intro',
            'instructor': 'Chacko, E', 'credits': '3.00', 'days': 'TR',
            'time': {'start': '02:20PM', 'end': '03:35PM', 'raw': '02:20PM - 03:35PM'},
            'dates': '01/11/27 - 04/26/27', 'course_number': 'GEOG 1001',
        }]
        r = self.client.post('/export/xlsx', json=courses)
        self.assertEqual(r.status_code, 200)
        self.assertIn('spreadsheetml', r.content_type)
        self.assertTrue(r.data[:2] == b'PK')  # .xlsx is a zip

    def test_export_xlsx_bad_payload_400(self):
        self.assertEqual(self.client.post('/export/xlsx', json={'not': 'a list'}).status_code, 400)
        self.assertEqual(self.client.post('/export/xlsx', json=['not a dict']).status_code, 400)

    def test_security_header(self):
        r = self.client.get('/')
        self.assertEqual(r.headers.get('X-Content-Type-Options'), 'nosniff')


class TestAnalytics(unittest.TestCase):
    """The GA4 tag is rendered on every server page and can be disabled via env."""

    def setUp(self):
        self.client = app.test_client()

    def test_default_id_on_index(self):
        app.config['GA_MEASUREMENT_ID'] = 'G-BD4W32R0TM'
        r = self.client.get('/')
        self.assertIn(b'googletagmanager.com/gtag/js?id=G-BD4W32R0TM', r.data)
        self.assertIn(b"gtag('config', 'G-BD4W32R0TM')", r.data)

    def test_tag_on_error_page(self):
        app.config['GA_MEASUREMENT_ID'] = 'G-BD4W32R0TM'
        r = self.client.post('/upload', data={
            'file': (io.BytesIO(b'not a spreadsheet'), 'notes.txt')},
            content_type='multipart/form-data')
        self.assertEqual(r.status_code, 400)
        self.assertIn(b'gtag/js?id=G-BD4W32R0TM', r.data)

    def test_tag_on_calendar_page_but_not_in_offline_export(self):
        app.config['GA_MEASUREMENT_ID'] = 'G-BD4W32R0TM'
        r = self.client.post('/upload', data={
            'file': (io.BytesIO(_registrar_xlsx_bytes()), 'sched.xlsx')},
            content_type='multipart/form-data')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'gtag/js?id=G-BD4W32R0TM', r.data)
        # The embedded offline template (downloaded "Export Schedule") must not
        # carry the tag: decode the base64 blob and check.
        import base64, re
        m = re.search(rb'const EXPORT_TEMPLATE_B64 = "([^"]+)"', r.data)
        self.assertIsNotNone(m)
        offline = base64.b64decode(m.group(1))
        self.assertNotIn(b'googletagmanager', offline)

    def test_empty_id_disables_tag(self):
        app.config['GA_MEASUREMENT_ID'] = ''
        try:
            self.assertNotIn(b'googletagmanager', self.client.get('/').data)
            r = self.client.post('/upload', data={
                'file': (io.BytesIO(_registrar_xlsx_bytes()), 'sched.xlsx')},
                content_type='multipart/form-data')
            self.assertNotIn(b'googletagmanager', r.data)
        finally:
            app.config['GA_MEASUREMENT_ID'] = 'G-BD4W32R0TM'

    def test_env_var_overrides_default(self):
        import importlib, app as app_module
        os.environ['GA_MEASUREMENT_ID'] = 'G-TESTOVERRIDE'
        try:
            importlib.reload(app_module)
            self.assertEqual(app_module.app.config['GA_MEASUREMENT_ID'], 'G-TESTOVERRIDE')
        finally:
            del os.environ['GA_MEASUREMENT_ID']
            importlib.reload(app_module)


if __name__ == '__main__':
    unittest.main()
