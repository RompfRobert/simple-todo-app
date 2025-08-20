# Multi-stage build for production Flask app with Gunicorn

# Builder stage - Build wheels for dependencies
FROM python:slim AS builder

WORKDIR /build

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Build wheels for all dependencies
RUN pip wheel -r requirements.txt -w /wheels

# Final production stage
FROM python:slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Copy wheels from builder stage
COPY --from=builder /wheels /wheels
COPY requirements.txt .

# Install dependencies from pre-built wheels
RUN pip install --no-cache-dir --no-compile -r requirements.txt \
    --no-index --find-links /wheels && \
    rm -rf /wheels requirements.txt

# Copy application code
COPY . /app/

# Create data directory
RUN mkdir -p /app/data

EXPOSE 5000

# Use Gunicorn with production settings
CMD ["gunicorn", "-w", "2", "-k", "gthread", "--threads", "4", "-b", "0.0.0.0:5000", "app:app"]
