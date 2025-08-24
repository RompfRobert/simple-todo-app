# Simple Todo App - Version 8

A production-ready Flask todo application with comprehensive observability: structured JSON logging, Prometheus metrics, and OpenTelemetry distributed tracing.

This is **Version 8** of a learning project that builds on **v7** by implementing **enterprise-grade observability** with structured logging, metrics collection, and distributed tracing.  

Beyond new functionality, this version also illustrates **how production Docker containers are expected to behave**: logs go to stdout/stderr, metrics are scraped externally, and traces let you follow requests across containers.

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

## Why Observability Matters in Docker

This version isn’t just about learning Flask or Prometheus — it’s about running containers the *production-ready* way.

1. **Structured logs to stdout/stderr**  
   - Containers shouldn’t write to internal log files. They emit logs to stdout/stderr, which Docker and Kubernetes automatically collect and enrich with metadata (container ID, pod name, timestamps).  
   - *What you learn:* `docker logs` shows clean JSON, which can be parsed by log systems instead of free-text output.

2. **Prometheus metrics endpoint**  
   - Containers are black boxes unless they expose their health externally. `/metrics` is the canonical interface.  
   - *What you learn:* How to export metrics inside a container and scrape them from another container (Prometheus), demonstrating **inter-container communication** and **port exposure**.

3. **Latency histograms**  
   - With Docker’s CPU/memory isolation, resource constraints directly affect latency. Histograms let you visualize the impact.  
   - *What you learn:* Apply `--cpus` and `--memory` limits, generate load, and see performance degradation in Prometheus.

4. **Optional Jaeger tracing**  
   - Logs alone can’t explain where a request slowed down in a multi-service chain (web → worker → DB). Tracing connects the dots.  
   - *What you learn:* Wire together multiple services (web, worker, Redis, Postgres, Jaeger) into one observable unit using Compose networks, the same way it’s done in Kubernetes.

✅ **The Docker takeaway:**  

- Containers should **log to stdout**, not to files.  
- Containers should **expose metrics endpoints** instead of relying on `docker exec`.  
- Observability infra often runs as **sidecar/companion containers**.  
- You’re no longer just running “an app in Docker” — you’re running an **observable service**, production-style.

## Quick Start

1. **Clone and setup**:

   ```bash
   cp .env.example .env
   ```

2. **Start the application**:

   ```bash
   docker compose up -d
   ```

3. **Verify the services**:

   - Application: [http://localhost](http://localhost)
   - Prometheus: [http://localhost:9090](http://localhost:9090)
   - Jaeger UI: [http://localhost:16686](http://localhost:16686)

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

Access metrics at [http://localhost:9090](http://localhost:9090) (Prometheus) or [http://localhost/metrics](http://localhost/metrics) (direct).

**Available Metrics**:

- `http_request_duration_seconds` - HTTP request latency histogram with buckets optimized for web traffic
- `background_jobs_total` - Counter for background jobs by status (enqueued, started, succeeded, failed)
- Standard process metrics (CPU, memory, file descriptors)

**Metric Labels**:

- `method` - HTTP method (GET, POST, etc.)
- `endpoint` - Flask endpoint name
- `status` - HTTP status code
- `environment` - Application environment (from APP\_ENV)
- `job_type` - Background job type (export, etc.)

### Logging

All logs are output as structured JSON with the following fields:

- `timestamp`, `level`, `logger`, `message`
- `request_id`, `http.method`, `http.path`, `status_code`, `duration_ms`
- `client_ip`, `user_agent`
- `trace_id`, `span_id` (when tracing enabled)

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
echo "TRACING_ENABLED=true" >> .env
docker compose up -d
```

Generate traced requests:

```bash
curl http://localhost/
curl -X POST http://localhost/export -H "Content-Type: application/json" -d '{}'
```

View traces at [http://localhost:16686](http://localhost:16686).

**Trace Features**:

- Auto-instrumentation for Flask, requests, PostgreSQL, Redis, and Celery
- W3C trace context propagation (`traceparent` headers)
- Trace/span IDs included in logs
- OTLP export to Jaeger
- Graceful fallback when Jaeger is unavailable

## Architecture

```text
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

**Network Topology**:

- **front-net**: Caddy ↔ Web (external access via proxy only)
- **back-net**: Web ↔ DB/Redis/Worker + Prometheus/Jaeger (internal only)
- Published ports: 80 (Caddy), 9090 (Prometheus), 16686 (Jaeger)

## Configuration

(… keep your environment variable table, monitoring queries, dev instructions, troubleshooting, security, performance, license as you had …)
