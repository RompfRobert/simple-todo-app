# Flask + Tailwind To-Do App (v6 — Network Segmentation with Reverse Proxy)

This is **Version 6** of a learning project designed to teach Docker fundamentals by building a simple To-Do list web application.  
It builds on **v5** by implementing **network segmentation**, **reverse proxy architecture**, and **enhanced security isolation**.

With this version, the database is isolated from the host network, the app is only accessible through a Caddy reverse proxy, and two separate networks provide clear traffic separation.

## Features

- All features from **v1** through **v5**:
  - Add, view, and delete tasks
  - Tailwind CSS styling (via CDN)
  - Multi-stage Docker builds
  - Gunicorn WSGI server
  - PostgreSQL backend with health checks
  - Container hardening and graceful shutdown
- New in **v6**:
  - **Caddy Reverse Proxy**: All traffic flows through Caddy on port 80
  - **Network Segmentation**: Two isolated networks (front-net and back-net)
  - **Database Isolation**: PostgreSQL only accessible from the app via back-net
  - **Static File Serving**: Caddy serves static assets directly without hitting Flask
  - **Enhanced Security**: Database not exposed to host network
  - **TLS Ready**: Caddy configuration ready for HTTPS/TLS certificates

## Why Version 6 Improvements?

### Network Segmentation

- **Security**: Database isolated from external access
- **Performance**: Static files served directly by Caddy
- **Scalability**: Clean separation of concerns
- **Monitoring**: Centralized proxy with logging and health checks

### Container Hardening

- **Security**: Non-root execution reduces attack surface
- **Signal Handling**: Proper tini init for clean shutdowns
- **File Ownership**: Mounted volumes get correct UID/GID (10001)
- **Resource Management**: Graceful handling of resource limits

### Health Monitoring

- **Observability**: Built-in health checks for monitoring systems
- **Reliability**: Container orchestrators can detect and restart unhealthy instances
- **Dependencies**: Services can wait for healthy dependencies before starting

## Tech Stack

- **Python** — Latest stable Python version
- **Flask** — Lightweight web framework
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

### 4. Test Static File Serving

```bash
# Test static file serving through Caddy
curl http://localhost/static/style.css
# Should return the CSS content
```

### 5. Test Graceful Shutdown (No Exit Code 137)

```bash
# Start the stack
docker compose up -d

# Stop with timeout to test graceful shutdown
docker stop --time=20 simple-todo-web
echo "Exit code: $?"
# Should be 0, not 137
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

### Permission Issues

```bash
# Check if running as correct user
docker exec simple-todo-web id
# Should show: uid=10001(appuser) gid=10001(appuser)

# Check file ownership
docker exec simple-todo-web ls -la /app/
```

## Architecture Overview

```
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
            └──────────┬──────────┘
                       │ back-net (internal)
                       ▼
            ┌─────────────────────────┐
            │   PostgreSQL            │
            │   Port: 5432            │
            │   Volume: postgres_data │
            │   NO HOST ACCESS        │
            └─────────────────────────┘
```

### Network Topology

- **front-net**: Public-facing network (proxy ↔ app)
- **back-net**: Internal network (app ↔ database) with `internal: true`
- **Database Isolation**: PostgreSQL only accessible from app container
- **Static Assets**: Caddy serves files directly from mounted volume

## Security Features

- **Network Segmentation**: Database isolated from external access
- **Reverse Proxy**: All traffic filtered through Caddy
- **Non-root Execution**: All processes run as UID/GID 10001
- **Minimal Base Image**: python:slim reduces attack surface
- **Proper Init**: tini handles zombie processes and signals correctly
- **Internal Networks**: back-net not exposed to host
- **Environment Separation**: Secrets managed via environment variables
- **Health Monitoring**: Unhealthy containers are automatically restarted

## Learning Objectives

- Understand **container hardening** with non-root users and proper init systems
- Learn **multi-service orchestration** with Docker Compose
- Practice **database integration** with PostgreSQL and SQLAlchemy
- Implement **health checks** and observability patterns
- Experience **graceful shutdown** and signal handling in containers
- Apply **security best practices** for production deployments

## File Structure

```text
version-6/
├── Dockerfile          # Multi-stage hardened build
├── app.py             # Flask app with PostgreSQL and health checks
├── templates/
│   └── index.html     # Tailwind CSS interface
└── README.md          # This file

Root Directory:
├── docker-compose.yml # Complete stack definition
├── .env               # Environment configuration
├── .env.example       # Configuration template
├── .dockerignore      # Build context exclusions
└── requirements.txt   # Python dependencies
```

## Success Criteria ✅

- ✅ **Graceful SIGTERM handling**: No exit code 137 on shutdown
- ✅ **Non-root file ownership**: UID/GID 10001 for mounted volumes
- ✅ **Health status**: Docker reports container as "healthy"
- ✅ **Compose stack**: Web service waits for healthy database
- ✅ **PostgreSQL persistence**: Data survives complete stack restarts
- ✅ **Container hardening**: tini init, dedicated user, proper signals
- ✅ **OCI compliance**: Standard metadata labels for traceability

## Next Steps

Consider these enhancements for production:

- **Load Balancing**: Add nginx or haproxy for multiple web instances
- **SSL/TLS**: Terminate HTTPS at load balancer or reverse proxy
- **Monitoring**: Integrate with Prometheus, Grafana, or similar
- **Logging**: Centralized log aggregation with ELK stack or similar
- **Backup**: Automated PostgreSQL backup and restore procedures
- **CI/CD**: Automated testing and deployment pipelines
