# Flask + Tailwind To-Do App (v5 — Production Hardened with PostgreSQL)

This is **Version 5** of a learning project designed to teach Docker fundamentals by building a simple To-Do list web application.  
It builds on **v4** by implementing **production hardening**, **PostgreSQL backend**, **health checks**, and **Docker Compose orchestration**.

With this version, the app runs as a non-root user with proper signal handling, includes health monitoring, uses PostgreSQL for persistence, and deploys as a complete stack using Docker Compose.

## Features

- All features from **v1** through **v4**:
  - Add, view, and delete tasks
  - Tailwind CSS styling (via CDN)
  - Multi-stage Docker builds
  - Gunicorn WSGI server
- New in **v5**:
  - **Docker Compose**: Complete stack orchestration with dependencies
  - **PostgreSQL Backend**: Replaces JSON file storage with proper database
  - **Container Hardening**: Non-root user (UID/GID 10001), proper signal handling with tini
  - **Health Checks**: Built-in `/healthz` endpoint with Docker health monitoring
  - **OCI Metadata**: Standard image labels for traceability
  - **Graceful Shutdown**: SIGTERM handling without exit code 137
  - **Security**: Runs as dedicated user with minimal privileges

## Why Version 5 Improvements?

### PostgreSQL Backend

- **Reliability**: ACID transactions and data integrity
- **Scalability**: Better performance under load
- **Concurrency**: Multiple users can safely interact simultaneously
- **Features**: Rich querying, indexing, and relationship capabilities

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

- **Python 3.13.6** — Latest stable Python version
- **Flask** — Lightweight web framework
- **Gunicorn + tini** — Production WSGI server with proper init
- **PostgreSQL 16** — Production-grade database
- **SQLAlchemy** — Python ORM for database interactions
- **Tailwind CSS** — Modern utility-first CSS framework (loaded via CDN)
- **Docker Compose** — Multi-container orchestration
- **Docker Health Checks** — Container health monitoring

## Quick Start

```bash
cd simple-todo-app/version-5

# Copy environment configuration
cp ../.env.example .env
```

### 2. Build and Run

```bash
# Build and start the complete stack
docker compose up -d

# Check that services are healthy
docker ps
```

### 3. Access the Application

Open [http://localhost:5000](http://localhost:5000) in your browser.

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
curl http://localhost:5000/healthz
# Should return: {"status": "healthy", "timestamp": "..."}
```

### 3. Test Graceful Shutdown (No Exit Code 137)

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

Add some tasks through the web interface at http://localhost:5000

```bash
# Stop the entire stack
docker compose down

# Start again
docker compose up -d
```

Verify tasks are still there

## Database Operations

### Access PostgreSQL directly

```bash
# Connect to database container
docker exec -it simple-todo-db psql -U todos -d todos

# List tables
\dt

# Query todos
SELECT * FROM todos;

# Exit
\q
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

```text
┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Monitoring    │
│   (Optional)    │    │   (Optional)    │
└─────────┬───────┘    └─────────────────┘
          │
          ▼
┌─────────────────┐
│  simple-todo-web│
│  Flask + Gunicorn │
│  Port: 5000     │
│  User: 10001    │
│  Health: /healthz│
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ simple-todo-db  │
│ PostgreSQL 16   │
│ Port: 5432      │
│ Volume: postgres_data │
└─────────────────┘
```

## Security Features

- **Non-root Execution**: All processes run as UID/GID 10001
- **Proper Init**: tini handles zombie processes and signals correctly
- **Network Isolation**: Services communicate via dedicated Docker network
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
version-5/
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

In v6, we will add Caddy as a reverse proxy on port 80, segment the network for better isolation, and restrict PostgreSQL access to only the app. Static files will be served directly by Caddy, the database will be kept off the host network, and the stack will be prepared for TLS/HTTPS with a ready-to-use Caddy configuration.
