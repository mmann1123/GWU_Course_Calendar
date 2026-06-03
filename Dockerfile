# GWU Course Calendar web app — container for Google Cloud Run.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only what the web app needs (the desktop GUI, tests, and media are excluded
# via .dockerignore).
COPY gwu_scraper.py registrar_io.py app.py ./
COPY templates/ ./templates/

# Run as a non-root user.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8080

# gthread workers suit the blocking multi-page scrape; honor Cloud Run's $PORT.
# Keep gunicorn --timeout below the Cloud Run request timeout.
CMD exec gunicorn --bind :$PORT --workers 2 --threads 8 --timeout 120 \
    --worker-class gthread app:app
