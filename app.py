#!/usr/bin/env python3
"""
GWU Course Calendar — Flask web app (for Google Cloud Run).

A thin, STATELESS wrapper around the existing scraper / calendar / registrar-xlsx
logic. Nothing per-user is written to disk: the calendar HTML is built in memory
and returned, and the registrar .xlsx export is built in a BytesIO and streamed
back. This makes it safe for many concurrent users with nothing to clean up.

Routes:
    GET  /              landing page (scrape form + upload form)
    POST /scrape        scrape a subject -> interactive calendar HTML
    POST /upload        upload a registrar .xlsx -> interactive calendar HTML
    POST /export/xlsx   POST edited courses (JSON) -> registrar .xlsx download
    GET  /healthz       health check for Cloud Run
"""

from io import BytesIO

from flask import (Flask, Response, render_template, request, send_file,
                   jsonify)

from gwu_scraper import CourseScraper, build_html_calendar, build_gwu_url
import registrar_io

app = Flask(__name__)
# Cap request bodies (covers both .xlsx uploads and the export JSON payload).
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB
MAX_EXPORT_COURSES = 5000

SEMESTER_LABELS = {'01': 'Spring', '02': 'Summer', '03': 'Fall'}


@app.after_request
def _security_headers(resp):
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp


def _calendar_response(courses, year=None, semester=None):
    """Build the interactive calendar HTML (web mode) and return it as a response."""
    timed = [c for c in courses if c.get('time')]
    html = build_html_calendar(timed, year=year, semester=semester, web_export=True)
    return Response(html, mimetype='text/html')


def _error(message, status=400):
    """Render a simple, friendly error page."""
    body = render_template('error.html', message=message)
    return Response(body, status=status, mimetype='text/html')


@app.get('/')
def index():
    return render_template('index.html', semesters=SEMESTER_LABELS)


@app.post('/scrape')
def scrape():
    try:
        url = build_gwu_url(request.form.get('year', ''),
                            request.form.get('semester', ''),
                            request.form.get('subject', ''))
    except ValueError as e:
        return _error(str(e), 400)

    try:
        courses = CourseScraper(url=url).scrape()
    except Exception:
        return _error("Couldn't reach the GWU schedule site. Please try again "
                      "in a moment, or upload a registrar .xlsx instead.", 502)

    if not courses:
        return _error("No courses found for that subject/term. Double-check the "
                      "subject code and semester, or upload a registrar .xlsx.", 404)

    year = request.form.get('year') or None
    semester = request.form.get('semester') or None
    return _calendar_response(courses, year=year, semester=semester)


@app.post('/upload')
def upload():
    file = request.files.get('file')
    if file is None or not file.filename:
        return _error("No file was uploaded.", 400)
    if not file.filename.lower().endswith('.xlsx'):
        return _error("Please upload a registrar .xlsx file.", 400)

    try:
        courses, warnings = registrar_io.read_registrar_xlsx(
            BytesIO(file.read()), return_warnings=True)
    except Exception as e:
        return _error(f"Couldn't read that file as a registrar .xlsx: {e}", 400)

    if not courses:
        return _error("No course rows were found in that file.", 400)

    # Note: warnings (e.g. missing instructor column) are non-fatal; the calendar
    # still renders. They are surfaced in the CLI/GUI; for the web UI we proceed.
    return _calendar_response(courses)


@app.post('/export/xlsx')
def export_xlsx():
    data = request.get_json(silent=True)
    if not isinstance(data, list):
        return jsonify(error="Expected a JSON array of courses."), 400
    if len(data) > MAX_EXPORT_COURSES:
        return jsonify(error="Too many courses to export."), 400
    if not all(isinstance(c, dict) for c in data):
        return jsonify(error="Each course must be an object."), 400

    buf = BytesIO()
    registrar_io.write_registrar_xlsx(data, buf)
    buf.seek(0)
    return send_file(
        buf, as_attachment=True, download_name='registrar_export.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.get('/health')
def health():
    # Note: '/healthz' is intercepted by Google Frontend on Cloud Run, so use '/health'.
    return 'ok', 200


if __name__ == '__main__':
    # Local dev only; production uses gunicorn (see Dockerfile).
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
