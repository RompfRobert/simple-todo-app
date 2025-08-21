# Multi-stage build for production Flask app with Gunicorn, hardening, and health checks

# Builder stage - Build wheels for dependencies
FROM python:slim AS builder

WORKDIR /build

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Build wheels for all dependencies
RUN pip wheel -r requirements.txt -w /wheels

# Final production stage
FROM python:slim AS production

# Build arguments for OCI labels
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=9.0.0

# OCI Image Labels for metadata
LABEL org.opencontainers.image.title="Simple Todo App" \
      org.opencontainers.image.description="Production-ready Flask Todo application with PostgreSQL backend" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.url="https://github.com/RompfRobert/simple-todo-app" \
      org.opencontainers.image.source="https://github.com/RompfRobert/simple-todo-app" \
      org.opencontainers.image.licenses="GPL-3.0" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.authors="Robert Rompf <robert@rompf.dev>" \
      org.opencontainers.image.documentation="https://github.com/RompfRobert/simple-todo-app/blob/main/README.md"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install tini for proper signal handling
RUN apt-get update && \
    apt-get install -y --no-install-recommends tini && \
    rm -rf /var/lib/apt/lists/*

# Create dedicated user and group with stable IDs
RUN groupadd -r -g 10001 appuser && \
    useradd -r -u 10001 -g appuser -d /app -s /bin/bash appuser

WORKDIR /app

# Copy wheels from builder stage
COPY --from=builder /wheels /wheels
COPY requirements.txt .

# Install dependencies from pre-built wheels and remove temporary files
RUN pip install --no-cache-dir --no-compile -r requirements.txt \
    --no-index --find-links /wheels && \
    rm -rf /wheels requirements.txt

# Copy application code with proper ownership
COPY --chown=10001:10001 . /app/

# Create data directory with proper ownership
RUN mkdir -p /app/data && \
    chown -R 10001:10001 /app

# Switch to non-root user
USER 10001:10001

# Health check using Python's urllib
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/healthz').status==200 else 1)"

# Configure signal handling
STOPSIGNAL SIGTERM

EXPOSE 5000

# Use tini as init process for proper signal handling
ENTRYPOINT ["tini", "--"]

# Use Gunicorn with production settings and observability
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
