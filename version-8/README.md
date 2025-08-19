# Simple Todo App - Version 8

A production-ready Flask todo application with comprehensive observability: structured JSON logging, Prometheus metrics, and OpenTelemetry distributed tracing.

This is **Version 8** of a learning project that builds on **v7** by implementing **enterprise-grade observability** with structured logging, metrics collection, and distributed tracing.

## Features

### Core Application

- Flask web application with PostgreSQL database
- Celery background tasks with Redis broker
- Caddy reverse proxy with static file serving
- Docker multi-stage builds with security hardening

### Observability (New in v8)

- **Structured JSON Logging**: All logs output as JSON to stdout/stderr with correlation IDs
- **Prometheus Metrics**: HTTP request histograms, background job counters, and application metrics
- **Distributed Tracing**: Optional OpenTelemetry tracing with Jaeger backend
- **Request Correlation**: Request IDs and trace IDs propagated through logs and responses

## Quick Start

1. **Clone and setup**:

   ```bash
   cd version-8
   cp .env.example .env
   ```

2. **Start the application**:

   ```bash
   docker compose up -d
   ```

3. **Verify the services**:
   - Application: <http://localhost>
   - Prometheus: <http://localhost:9090>
   - Jaeger UI: <http://localhost:16686>

4. **Generate some traffic**:

   ```bash
   # Add some todos
   curl -X POST http://localhost/add -d "task=Test task 1" -H "Content-Type: application/x-www-form-urlencoded"
   curl -X POST http://localhost/add -d "task=Test task 2" -H "Content-Type: application/x-www-form-urlencoded"
   
   # Trigger background export
   curl -X POST http://localhost/export -H "Content-Type: application/json" -d '{}'
   ```

## Observability Features

### Metrics

Access metrics at <http://localhost:9090> (Prometheus) or <http://localhost/metrics> (direct).

**Available Metrics**:

- `http_request_duration_seconds` - HTTP request latency histogram with buckets optimized for web traffic
- `background_jobs_total` - Counter for background jobs by status (enqueued, started, succeeded, failed)
- Standard process metrics (CPU, memory, file descriptors)

**Metric Labels**:

- `method` - HTTP method (GET, POST, etc.)
- `endpoint` - Flask endpoint name
- `status` - HTTP status code
- `environment` - Application environment (from APP_ENV)
- `job_type` - Background job type (export, etc.)

### Logging

All logs are output as structured JSON with the following fields:

- `timestamp` - ISO-8601 formatted timestamp
- `level` - Log level (INFO, ERROR, etc.)
- `logger` - Logger name
- `message` - Log message
- `request_id` - Unique request identifier
- `http.method` - HTTP method (in request context)
- `http.path` - HTTP path (in request context)
- `status_code` - HTTP response status
- `duration_ms` - Request duration in milliseconds
- `client_ip` - Client IP address
- `user_agent` - User agent string
- `trace_id` - Distributed trace ID (when tracing enabled)
- `span_id` - Current span ID (when tracing enabled)

**View logs**:

```bash
# Web application logs
docker compose logs web

# Worker logs  
docker compose logs worker

# All logs with JSON formatting
docker compose logs --follow
```

### Distributed Tracing

Enable tracing by setting `TRACING_ENABLED=true` in your `.env` file:

```bash
# Enable tracing
echo "TRACING_ENABLED=true" >> .env

# Restart services
docker compose up -d

# Generate traced requests
curl http://localhost/
curl -X POST http://localhost/export -H "Content-Type: application/json" -d '{}'

# View traces at http://localhost:16686
```

**Trace Features**:

- Automatic instrumentation for Flask, requests, PostgreSQL, Redis, and Celery
- W3C trace context propagation via `traceparent` response headers
- Trace/span IDs included in logs for correlation
- OTLP export to Jaeger
- Graceful degradation when Jaeger is unavailable

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Browser   │───▶│    Caddy     │───▶│  Flask App  │
└─────────────┘    │  (Proxy)     │    │   (Web)     │
                   │   Port 80    │    └─────────────┘
                   └──────────────┘           │
                                             │
                   ┌──────────────┐    ┌─────────────┐
                   │  Prometheus  │    │  PostgreSQL │
                   │   Port 9090  │    │     (DB)    │
                   └──────────────┘    └─────────────┘
                           │                   │
                   ┌──────────────┐    ┌─────────────┐
                   │    Jaeger    │    │    Redis    │
                   │  Port 16686  │    │  (Broker)   │
                   └──────────────┘    └─────────────┘
                                             │
                                    ┌─────────────┐
                                    │   Celery    │
                                    │  (Worker)   │
                                    └─────────────┘
```

### Network Topology

- **front-net**: Caddy ↔ Web (external access via proxy only)
- **back-net**: Web ↔ DB/Redis/Worker + Prometheus/Jaeger (internal only)
- Published ports: 80 (Caddy), 9090 (Prometheus), 16686 (Jaeger)

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `production` | Application environment |
| `LOG_LEVEL` | `INFO` | Logging level |
| `TRACING_ENABLED` | `false` | Enable OpenTelemetry tracing |
| `OTEL_SERVICE_NAME` | `todo-web` | Service name for tracing |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://jaeger:4318` | OTLP exporter endpoint |
| `DATABASE_URL` | See .env.example | PostgreSQL connection string |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Redis broker URL |
| `GUNICORN_WORKERS` | `2` | Number of Gunicorn workers |
| `GUNICORN_THREADS` | `4` | Threads per worker |

### Request Correlation

Every request gets a unique `request_id` that appears in:

- Response header: `X-Request-ID`
- All log entries for that request
- Error responses

When tracing is enabled:

- Response header: `traceparent` (W3C format)
- Log entries include `trace_id` and `span_id`

## Monitoring Queries

### Prometheus Queries

**Request Rate**:

```promql
rate(http_request_duration_seconds_count[5m])
```

**95th Percentile Latency**:

```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Error Rate**:

```promql
rate(http_request_duration_seconds_count{status=~"5.."}[5m])
```

**Background Job Success Rate**:

```promql
rate(background_jobs_total{status="succeeded"}[5m]) / rate(background_jobs_total{status=~"succeeded|failed"}[5m])
```

### Log Analysis

**Find all requests by trace ID**:

```bash
docker compose logs web | jq 'select(.trace_id == "YOUR_TRACE_ID")'
```

**Error analysis**:

```bash
docker compose logs web | jq 'select(.level == "ERROR")'
```

**Slow requests** (>1 second):

```bash
docker compose logs web | jq 'select(.duration_ms > 1000)'
```

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+psycopg2://todos:todos123@localhost:5432/todos"
export TRACING_ENABLED=false

# Run with development server
python app.py
```

### Testing Observability

1. **Metrics Test**:

   ```bash
   # Check metrics endpoint
   curl http://localhost/metrics
   
   # Should see Prometheus format metrics including:
   # - http_request_duration_seconds_bucket
   # - background_jobs_total
   ```

2. **Logging Test**:

   ```bash
   # Make a request and check logs
   curl http://localhost/
   docker compose logs web --tail 10
   
   # Should see JSON logs with request_id, duration_ms, etc.
   ```

3. **Tracing Test**:

   ```bash
   # Enable tracing
   echo "TRACING_ENABLED=true" >> .env
   docker compose up -d
   
   # Make requests
   curl -v http://localhost/
   
   # Check for traceparent header in response
   # View traces in Jaeger UI at http://localhost:16686
   ```

## Troubleshooting

### Common Issues

1. **Metrics not appearing in Prometheus**:
   - Check that web service is accessible: `docker compose exec prometheus wget -qO- http://web:5000/metrics`
   - Verify Prometheus config: `docker compose exec prometheus cat /etc/prometheus/prometheus.yml`

2. **Tracing not working**:
   - Verify `TRACING_ENABLED=true` in environment
   - Check Jaeger connectivity: `docker compose logs jaeger`
   - Look for OpenTelemetry errors in web logs

3. **JSON logs not formatted correctly**:
   - Verify `LOG_LEVEL` is set correctly
   - Check for any custom logging configuration conflicts

4. **High memory usage**:
   - Reduce `GUNICORN_WORKERS` and `GUNICORN_THREADS`
   - Adjust trace sampling rates if using tracing heavily

### Health Checks

```bash
# Application health
curl http://localhost/healthz

# Background services health  
curl http://localhost/healthz/background

# Prometheus targets
curl http://localhost:9090/api/v1/targets

# Jaeger health
curl http://localhost:16686/
```

## Security Notes

- All services run as non-root users
- Database and Redis are not exposed to host network
- Static files are served efficiently by Caddy
- Request IDs are UUIDs (not sequential numbers)
- No sensitive data logged (passwords masked in connection strings)

## Performance

- Gunicorn with threading for concurrent request handling
- Connection pooling for database access
- Efficient metrics collection with minimal overhead
- Optional tracing to avoid performance impact when disabled
- Prometheus metrics use appropriate histogram buckets for web latency

## License

GPL-3.0 License - see LICENSE file for details.
