FROM python:3.12-slim

# Install system dependencies required by pdfplumber and data processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser pages/ ./pages/
COPY --chown=appuser:appuser data/processed/ ./data/processed/

# Switch to non-root user
USER appuser

# Expose port for Fly.io
EXPOSE 8080

# Run application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "60", "app.app:server"]
