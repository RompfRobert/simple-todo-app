# Flask + Tailwind To-Do App (v7 — Background Jobs with Celery & Redis)

This is **Version 7** of a learning project designed to teach Docker fundamentals by building a simple To-Do list web application.  
It builds on **v6** by implementing **background job processing** with **Celery** and **Redis**, enabling **asynchronous task execution** without blocking the web server.

With this version, slow operations like data exports are processed by dedicated worker containers, keeping the web interface responsive while jobs run in the background.

## Features

- All features from **v1** through **v6**:
  - Add, view, and delete tasks
  - Tailwind CSS styling (via CDN)
  - Multi-stage Docker builds
  - Gunicorn WSGI server
  - PostgreSQL backend with health checks
  - Container hardening and graceful shutdown
  - Caddy reverse proxy with network segmentation
  - Database isolation and static file serving
- New in **v7**:
  - **Background Job Processing**: Celery workers handle slow tasks asynchronously
  - **Redis Message Broker**: Redis serves as both message broker and result backend
  - **Task Management API**: Endpoints to enqueue, monitor, and retrieve job results
  - **CSV Export Feature**: Asynchronous todo export to CSV as a demonstration
  - **Worker Scaling**: Dedicated worker containers independent of web processes
  - **Job Status Tracking**: Real-time status updates and progress monitoring
  - **Background Health Checks**: Redis connectivity monitoring for observability

## Why Version 7 Improvements?

### Background Job Processing

- **Responsiveness**: Web server never blocks on slow operations
- **Scalability**: Worker processes can scale independently of web processes
- **Reliability**: Failed jobs can be retried automatically
- **Monitoring**: Real-time visibility into job status and progress

### Asynchronous Architecture

- **Task Queues**: Redis manages job distribution to available workers
- **Result Storage**: Job results and status stored in Redis for retrieval
- **Process Separation**: Web and worker processes have distinct responsibilities
- **Resource Management**: CPU-intensive tasks don't impact web response times

### Enhanced Observability

- **Job Tracking**: Complete audit trail of background task execution
- **Health Monitoring**: Redis connectivity checks for infrastructure health
- **Status APIs**: RESTful endpoints for job management and monitoring
- **Error Handling**: Comprehensive error reporting and recovery mechanisms

## Tech Stack

- **Python** — Latest stable Python version
- **Flask** — Lightweight web framework
- **Celery** — Distributed task queue for background job processing
- **Redis** — In-memory data store serving as message broker and result backend
- **Gunicorn + tini** — Production WSGI server with proper init
- **PostgreSQL 16** — Production-grade database
- **SQLAlchemy** — Python ORM for database interactions
- **Tailwind CSS** — Modern utility-first CSS framework (loaded via CDN)
- **Caddy** — Modern web server with automatic HTTPS and reverse proxy
- **Docker Compose** — Multi-container orchestration
- **Docker Health Checks** — Container health monitoring
- **Gunicorn + tini** — Production WSGI server with proper init
- **PostgreSQL 16** — Production-grade database
- **SQLAlchemy** — Python ORM for database interactions
- **Tailwind CSS** — Modern utility-first CSS framework (loaded via CDN)
- **Docker Compose** — Multi-container orchestration
- **Docker Health Checks** — Container health monitoring

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git (optional, for VCS metadata in builds)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd simple-todo-app

# Copy environment configuration
cp .env.example .env
```

### 2. Build and Run

```bash
# Build and start the complete stack
docker compose up -d

# Check that services are healthy
docker ps
```

### 3. Access the Application

Open [http://localhost](http://localhost) in your browser.

The application is now accessible through the Caddy reverse proxy on port 80.

## Environment Configuration

Edit `.env` file to customize database settings:

```bash
# PostgreSQL Database Configuration
POSTGRES_DB=todos
POSTGRES_USER=todos
POSTGRES_PASSWORD=todos123

# Application Database URL
DATABASE_URL=postgresql+psycopg2://todos:todos123@db:5432/todos
```

## Verification and Testing

### 1. Check Container Health Status

```bash
docker ps
# Look for "healthy" status in the STATUS column
```

### 2. Verify Health Endpoint

```bash
# Test app health through proxy
curl http://localhost/healthz
# Should return: {"status": "healthy", "timestamp": "..."}

# Test proxy health directly
curl http://localhost/proxy-health
# Should return: OK
```

### 3. Verify Network Segmentation

```bash
# Check that database is NOT accessible from host
nslookup db || echo "Database isolated as expected"

# Verify networks
docker network ls | grep simple-todo

# Confirm backend network is internal
docker network inspect simple-todo-backend --format '{{.Internal}}'
# Should return: true

# Confirm frontend network is not internal
docker network inspect simple-todo-frontend --format '{{.Internal}}'
# Should return: false
```

### 4. Test Background Job Processing

```bash
# Test CSV export functionality
curl -X POST http://localhost/export -H "Content-Type: application/json" -d '{"filters": {}}'
# Should return: {"task_id": "abc123..."}

# Check job status
curl http://localhost/tasks/abc123...
# Should return status information

# Download result when ready
curl http://localhost/download/abc123... -o todos_export.csv

# Test background health check
curl http://localhost/healthz/background
# Should return: {"redis": "ok"}
```

### 5. Test Worker and Job Processing

```bash
# Check that all services are running and healthy
docker compose ps
# Should show: app, worker, redis, db, proxy all healthy

# Monitor worker logs
docker compose logs -f worker

# Test job processing under load
for i in {1..5}; do
  curl -X POST http://localhost/export &
done
wait

# Verify web responsiveness during job processing
curl http://localhost/healthz
# Should remain fast and responsive
```

### 4. Check File Ownership in Mounted Volumes

```bash
# Start with bind mount to test file ownership
docker run -d -p 5000:5000 -v $(pwd)/test_data:/app/data simple-todo:v5

# Check ownership of files created by container
ls -la test_data/
# Files should be owned by UID/GID 10001
```

### 5. Test Data Persistence

```bash
# Add some tasks through the web interface at http://localhost:5000

# Stop the entire stack
docker compose down

# Start again
docker compose up -d

# Verify tasks are still there
```

## Background Job API

### Export Todos to CSV

```bash
# Start an export job
curl -X POST http://localhost/export \
  -H "Content-Type: application/json" \
  -d '{"filters": {"done": true}}'

# Response: {"task_id": "550e8400-e29b-41d4-a716-446655440000"}
```

### Check Job Status

```bash
# Get job status and progress
curl http://localhost/tasks/550e8400-e29b-41d4-a716-446655440000

# Response example:
# {
#   "task_id": "550e8400-e29b-41d4-a716-446655440000",
#   "state": "SUCCESS",
#   "info": {"csv_path": "/tmp/todos_export_550e8400.csv", "count": 15},
#   "ready": true,
#   "successful": true
# }
```

### Download Results

```bash
# Download the generated CSV file
curl http://localhost/download/550e8400-e29b-41d4-a716-446655440000 \
  -o my_todos_export.csv
```

## Database Operations

### Access PostgreSQL directly

```bash
# Connect to database container (since it's not exposed to host)
docker compose exec db psql -U todos -d todos

# List tables
\dt

# Query todos
SELECT * FROM todos;

# Exit
\q

# Note: Database is only accessible from app container due to network segmentation
```

### Access Redis directly

```bash
# Connect to Redis container
docker compose exec redis redis-cli

# Check queue status
KEYS celery*

# Monitor job activity
MONITOR

# Exit
exit
```

### Database Schema

```sql
CREATE TABLE todos (
    id SERIAL PRIMARY KEY,
    text VARCHAR(500) NOT NULL,
    done BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## Production Deployment

### Build with Metadata

```bash
export BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
export VCS_REF=$(git rev-parse --short HEAD)

docker compose build
```

### Resource Limits

```yaml
# Add to docker-compose.override.yml
version: '3.8'
services:
  web:
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'
        reservations:
          memory: 128M
  db:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
```

### Monitoring

```bash
# Check container logs
docker compose logs -f web
docker compose logs -f db

# Monitor resource usage
docker stats simple-todo-web simple-todo-db
```

## Troubleshooting

### Service Won't Start

```bash
# Check service logs
docker compose logs web
docker compose logs db

# Check health status
docker inspect simple-todo-web | grep Health -A 10
```

### Database Connection Issues

```bash
# Test database connectivity
docker exec simple-todo-web python -c "
import os
from sqlalchemy import create_engine, text
engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection successful:', result.fetchone())
"
```

### Background Job Troubleshooting

```bash
# Check worker status
docker compose logs worker

# Monitor Redis connectivity
docker exec simple-todo-redis redis-cli ping

# Check Celery job queues
docker exec simple-todo-worker celery -A celery_app.celery inspect active

# Test Redis connection from app
docker exec simple-todo-app python -c "
import redis
import os
r = redis.Redis.from_url(os.environ['CELERY_BROKER_URL'])
print('Redis ping:', r.ping())
"
```

## Architecture Overview

```text
                    Internet
                        │
                        ▼
            ┌─────────────────────┐
            │   Caddy Proxy       │
            │   Port: 80/443      │
            │   Static Serving    │
            │   Health Checks     │
            └──────────┬──────────┘
                       │ front-net
                       ▼
            ┌─────────────────────┐
            │   Flask App         │
            │   Port: 5000        │
            │   User: 10001       │
            │   Health: /healthz  │
            │   API: /export      │
            └──────────┬──────────┘
                       │ back-net (internal)
                       ▼
     ┌─────────────────────┐    ┌─────────────────────┐
     │   Celery Worker     │    │   Redis Broker      │
     │   Background Jobs   │◄──►│   Message Queue     │
     │   CSV Export        │    │   Result Backend    │
     │   User: 10001       │    │   Port: 6379        │
     └─────────────────────┘    └─────────────────────┘
                       │                    │
                       │ back-net (internal)│
                       ▼                    │
            ┌─────────────────────────┐     │
            │   PostgreSQL            │     │
            │   Port: 5432            │     │
            │   Volume: postgres_data │◄────┘
            │   NO HOST ACCESS        │
            └─────────────────────────┘
```

### Service Communication

- **Web → Worker**: Jobs enqueued via Redis message broker
- **Worker → Database**: Direct SQL access for data processing
- **Web → Redis**: Job status checks and result retrieval  
- **Client → Web**: RESTful API for job management
- **All Services**: Isolated on back-net except proxy communication

## Security Features

- **Network Segmentation**: Database and Redis isolated from external access
- **Reverse Proxy**: All traffic filtered through Caddy
- **Non-root Execution**: All processes run as UID/GID 10001
- **Minimal Base Image**: python:slim reduces attack surface
- **Proper Init**: tini handles zombie processes and signals correctly
- **Internal Networks**: back-net not exposed to host
- **Environment Separation**: Secrets managed via environment variables
- **Health Monitoring**: Unhealthy containers are automatically restarted
- **Job Isolation**: Background tasks run in separate containers
- **Message Security**: Redis communication isolated to internal network

## Learning Objectives

- Understand **asynchronous task processing** with Celery and Redis
- Learn **message broker patterns** for distributed systems
- Practice **worker process scaling** and job queue management
- Implement **background job APIs** with status tracking and file downloads
- Experience **multi-service orchestration** with interdependent containers
- Apply **observability patterns** for distributed job processing
- Understand **resource isolation** between web and worker processes
- Learn **Redis operations** for caching and message queuing
- Practice **container health monitoring** across multiple service types

## File Structure

```text
version-7/
├── Dockerfile          # Multi-stage hardened build with Celery
├── app.py             # Flask app with background job APIs
├── celery_app.py      # Celery configuration and initialization
├── requirements.txt   # Python dependencies including Celery/Redis
├── templates/
│   └── index.html     # Tailwind CSS interface
└── README.md          # This file

Root Directory:
├── docker-compose.yml # Complete stack with worker and Redis services
├── .env               # Environment configuration
├── .env.example       # Configuration template
└── .dockerignore      # Build context exclusions
```

## Success Criteria ✅

- ✅ **Background Job Processing**: CSV exports run asynchronously without blocking web requests
- ✅ **Worker Health**: Celery workers start successfully and process jobs
- ✅ **Redis Connectivity**: Message broker and result backend operational
- ✅ **API Responsiveness**: Web endpoints for job management respond quickly
- ✅ **Job Status Tracking**: Real-time status updates and progress monitoring
- ✅ **File Downloads**: Generated CSV files downloadable via task ID
- ✅ **Service Isolation**: Web processes remain responsive during heavy job processing
- ✅ **Container Health**: All services (app, worker, redis, db, proxy) report healthy
- ✅ **Graceful Scaling**: Workers can be scaled independently of web processes
- ✅ **Error Handling**: Failed jobs reported with meaningful error messages

## Next Steps

Consider these enhancements for production:

- **Job Persistence**: Implement job result persistence beyond Redis TTL
- **Worker Autoscaling**: Dynamic worker scaling based on queue depth
- **Job Prioritization**: Multiple queues with different priority levels
- **Result Streaming**: WebSocket or Server-Sent Events for real-time updates
- **Job Scheduling**: Periodic tasks with Celery Beat
- **Monitoring Integration**: Flower or custom dashboards for job monitoring
- **Error Notifications**: Alert systems for failed job processing
- **Load Testing**: Validate performance under concurrent job processing
- **Backup Strategies**: Redis persistence and backup procedures
