# Simple Todo App - Version 9: Supply Chain Security & CI/CD Automation

A production-ready Flask todo application demonstrating modern Docker development practices with **automated CI/CD pipelines, multi-architecture builds, and supply chain security**.

This is **Version 9** of a progressive learning project that builds on **Version 8** by implementing **enterprise-grade CI/CD automation**. This version focuses on teaching modern DevOps practices including automated builds, multi-platform support, Software Bill of Materials (SBOM) generation, and container security scanning.

## 🎯 Learning Objectives: What Version 9 Teaches

### From Manual to Automated (v8 → v9)
- **v8**: Manual `docker build` and `docker push` commands
- **v9**: Fully automated GitHub Actions pipeline that builds and publishes on every commit

### From Single Architecture to Multi-Platform
- **v8**: Images built for your development machine's architecture only
- **v9**: Universal images supporting both `linux/amd64` (Intel/AMD) and `linux/arm64` (Apple Silicon, ARM servers)

### From Basic Images to Secure Supply Chain
- **v8**: Basic Docker images with minimal metadata
- **v9**: Images with comprehensive metadata, SBOM generation, and vulnerability scanning

### Key Learning Topics Covered
1. **GitHub Actions Workflows**: Understanding CI/CD pipeline automation
2. **Multi-Architecture Builds**: Using Docker Buildx for universal container images
3. **Container Registries**: Automated publishing to Docker Hub
4. **Supply Chain Security**: SBOM generation and vulnerability scanning
5. **Build Optimization**: Leveraging caching for faster builds
6. **Secret Management**: Secure handling of registry credentials

## 🚀 Features by Version

### Core Application (All Versions)
- Flask web application with PostgreSQL database
- Celery background tasks with Redis broker
- Caddy reverse proxy with static file serving
- Docker multi-stage builds with security hardening

### Observability Stack (Added in v8)
- **Structured JSON Logging**: All logs output as JSON with correlation IDs
- **Prometheus Metrics**: HTTP request histograms and background job counters
- **Distributed Tracing**: Optional OpenTelemetry tracing with Jaeger backend
- **Request Correlation**: Request IDs and trace IDs propagated through logs

### CI/CD & Supply Chain Security (New in v9)
- **🤖 Automated Builds**: GitHub Actions pipeline triggered on every commit
- **🌍 Multi-Architecture Support**: Universal images for Intel, AMD, and ARM platforms
- **📦 Automated Publishing**: Direct deployment to Docker Hub with `latest` tag
- **🔒 Security Scanning**: Trivy vulnerability scanner with GitHub Security integration
- **📋 SBOM Generation**: Software Bill of Materials for dependency tracking
- **⚡ Build Caching**: GitHub Actions cache for optimized build performance
- **🔄 PR Validation**: Build-only testing on pull requests (no publishing)

## 🚀 Quick Start

### Option 1: Use Pre-built Image (Recommended)
```bash
# Pull the latest multi-arch image from Docker Hub
docker pull rompfrobert/simple-todo-app:latest

# Clone the repository for docker-compose.yml
git clone https://github.com/RompfRobert/simple-todo-app.git
cd simple-todo-app

# Copy environment configuration
cp .env.example .env

# Start with pre-built image
docker compose up -d
```

### Option 2: Build Locally
```bash
# Clone and setup
git clone https://github.com/RompfRobert/simple-todo-app.git
cd simple-todo-app
cp .env.example .env

# Build and start (this will build the image locally)
docker compose up -d --build
```

### Verify the Services
- **Application**: http://localhost
- **Prometheus Metrics**: http://localhost:9090
- **Jaeger Tracing UI**: http://localhost:16686

### Test the Application
```bash
# Add some todos
curl -X POST http://localhost/add -d "task=Learn Docker CI/CD" -H "Content-Type: application/x-www-form-urlencoded"
curl -X POST http://localhost/add -d "task=Build multi-arch images" -H "Content-Type: application/x-www-form-urlencoded"

# Trigger background export task
curl -X POST http://localhost/export -H "Content-Type: application/json" -d '{}'

# Check application health
curl http://localhost/healthz
```

## 📚 Understanding the CI/CD Pipeline (Learning Focus)

### What is CI/CD and Why Do We Need It?

In **Version 8**, we manually built and pushed our Docker images:
```bash
# Manual process (v8)
docker build -t my-app .
docker push my-registry/my-app:latest
```

**Problems with manual deployment:**
- 🚫 Prone to human error ("Did I forget to push?")
- 🚫 Inconsistent builds across team members
- 🚫 Only builds for your local machine's architecture
- 🚫 No testing before deployment
- 🚫 No visibility into what's in your images (security)

**Version 9 Solution - Automated CI/CD:**
- ✅ Every commit automatically builds and tests
- ✅ Consistent builds regardless of developer machine
- ✅ Multi-architecture support (Intel, AMD, ARM)
- ✅ Automated security scanning and SBOM generation
- ✅ Only deploys if all tests pass

### Key Concepts Learned

#### 1. **Multi-Architecture Builds**
```yaml
platforms: linux/amd64,linux/arm64  # Universal images
```
**Why this matters:**
- Your teammates using Apple Silicon (M1/M2) can run the same image
- Production servers running ARM (cost-effective) work seamlessly
- Cloud providers offering ARM instances (AWS Graviton) are supported

#### 2. **GitHub Actions Workflow**
```yaml
on:
  push:
    branches: [master]     # Deploy on main branch
  pull_request:
    branches: [master]     # Test on pull requests
```
**Learning points:**
- Understand event-driven automation
- Different actions for different triggers
- Environment-specific behavior (PR vs production)

#### 3. **Software Bill of Materials (SBOM)**
```yaml
- name: Generate SBOM
  uses: anchore/sbom-action@v0
```
**Why SBOMs are critical:**
- Know exactly what's in your container images
- Track dependencies for security vulnerabilities
- Compliance requirements in enterprise environments
- Supply chain attack prevention

#### 4. **Container Security Scanning**
```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
```
**Security best practices:**
- Automated vulnerability detection
- Integration with GitHub Security tab
- Catch security issues before deployment
- Part of "shift-left" security philosophy

### Hands-On Learning Exercises

#### Exercise 1: Compare Architectures
```bash
# Pull the multi-arch image
docker pull rompfrobert/simple-todo-app:latest

# Check what architecture you got
docker image inspect rompfrobert/simple-todo-app:latest | grep Architecture

# Compare with a single-arch build
docker buildx build --platform linux/amd64 -t local-amd64 .
docker buildx build --platform linux/arm64 -t local-arm64 .
```

#### Exercise 2: Explore the SBOM
1. Go to the GitHub Actions run
2. Download the SBOM artifact
3. Open the JSON file and explore:
   ```bash
   cat sbom.spdx.json | jq '.packages[].name' | head -20
   ```

#### Exercise 3: Security Scanning
1. Check the GitHub Security tab in your repository
2. Review the Trivy scan results
3. Understand the vulnerability reports

## 🔧 CI/CD Pipeline Details

### Workflow Triggers

| Event | Action | Purpose |
|-------|--------|---------|
| Push to `master` | Build + Push + Scan | Deploy to production |
| Pull Request | Build only | Validate changes |
| Manual trigger | Build + Push + Scan | Emergency deployments |

### Pipeline Stages

```mermaid
graph LR
    A[Code Push] --> B[Checkout Code]
    B --> C[Setup Buildx]
    C --> D[Build Multi-Arch]
    D --> E[Push to Registry]
    E --> F[Generate SBOM]
    F --> G[Security Scan]
    G --> H[Upload Artifacts]
```

### Build Process Deep Dive

1. **Checkout**: Fetch source code and git history
2. **QEMU Setup**: Enable emulation for multi-arch builds
3. **Buildx Setup**: Configure Docker's buildx builder
4. **Authentication**: Login to Docker Hub using secrets
5. **Multi-Arch Build**: Build for both amd64 and arm64
6. **Registry Push**: Upload to Docker Hub with metadata
7. **SBOM Generation**: Catalog all dependencies
8. **Security Scanning**: Check for vulnerabilities
9. **Artifact Upload**: Store SBOM and scan results

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

## 🔧 Production CI/CD Pipeline Configuration

### Required GitHub Secrets

Before the pipeline can work, configure these secrets in your repository:

| Secret | Description | How to Get |
|--------|-------------|------------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username | Your Docker Hub account name |
| `DOCKERHUB_TOKEN` | Docker Hub access token | Docker Hub → Account Settings → Security → Access Tokens |

**Setup Steps:**
1. Go to your repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"  
3. Add both secrets with the values above

### Pipeline Behavior

| Trigger | Actions Performed | Result |
|---------|------------------|--------|
| **Push to `master`** | ✅ Build multi-arch<br>✅ Push to Docker Hub<br>✅ Generate SBOM<br>✅ Security scan | Production deployment |
| **Pull Request** | ✅ Build multi-arch<br>❌ No push<br>❌ No SBOM<br>❌ No scan | Validation only |

### Docker Hub Access

Once your pipeline runs successfully:

```bash
# Always get the latest version
docker pull rompfrobert/simple-todo-app:latest

# This works on any architecture (Intel, AMD, ARM)
docker run -p 5000:5000 rompfrobert/simple-todo-app:latest
```

### Pipeline Outputs & Artifacts

1. **Multi-Architecture Image**: `rompfrobert/simple-todo-app:latest`
   - Supports `linux/amd64` and `linux/arm64`
   - Automatically selects correct architecture when pulled

2. **SBOM Artifact**: Download from GitHub Actions
   - Lists all dependencies and versions
   - SPDX JSON format for compliance tools
   - 30-day retention policy

3. **Security Report**: Available in GitHub Security tab
   - Vulnerability scan results from Trivy
   - Integration with GitHub's security features
   - Automated alerts for new vulnerabilities

### Local Multi-Architecture Testing

Want to test multi-arch builds locally? Here's how:

```bash
# Setup buildx (one-time setup)
docker buildx create --name multiarch --use
docker buildx inspect --bootstrap

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag simple-todo-app:multiarch \
  --push \
  .

# Test on your current platform
docker buildx build \
  --platform linux/$(uname -m) \
  --tag simple-todo-app:local \
  --load \
  .
```

## 🚀 What's Next? Future Learning Opportunities

Version 9 establishes a solid foundation for enterprise-grade container deployment. Here are natural next steps to continue learning:

### Advanced CI/CD Concepts
- **Semantic Versioning**: Automated version tagging based on commit messages
- **Blue-Green Deployments**: Zero-downtime deployment strategies  
- **Canary Releases**: Gradual rollout to minimize risk
- **Rollback Strategies**: Automated rollback on deployment failures

### Container Orchestration
- **Kubernetes Deployment**: Moving beyond docker-compose to K8s
- **Helm Charts**: Package management for Kubernetes applications
- **Ingress Controllers**: Advanced routing and load balancing
- **Pod Autoscaling**: Automatic scaling based on metrics

### Advanced Security
- **Image Signing**: Cosign for cryptographic verification
- **Admission Controllers**: Policy enforcement in Kubernetes
- **Runtime Security**: Falco for runtime threat detection
- **Secret Management**: HashiCorp Vault integration

### Monitoring & Observability
- **Infrastructure Monitoring**: Node Exporter, cAdvisor
- **Log Aggregation**: ELK/EFK stack for centralized logging
- **Alert Management**: AlertManager with PagerDuty/Slack
- **Service Mesh**: Istio for advanced observability

### Performance & Reliability
- **Load Testing**: Automated performance testing in CI
- **Chaos Engineering**: Resilience testing with Chaos Monkey
- **Database Migrations**: Zero-downtime schema changes
- **CDN Integration**: Global content delivery optimization

## 📊 Observability Features (Version 8 Foundation)

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

## 📝 Version 9 Summary: Key Takeaways

### What We Built
✅ **Automated CI/CD Pipeline** - No more manual builds and pushes  
✅ **Multi-Architecture Support** - Works on Intel, AMD, and ARM processors  
✅ **Supply Chain Security** - SBOM generation and vulnerability scanning  
✅ **Production-Ready Deployment** - Automated Docker Hub publishing  
✅ **Security Integration** - GitHub Security tab for vulnerability tracking  

### What We Learned
🎓 **Docker Buildx** - Multi-platform container builds  
🎓 **GitHub Actions** - Event-driven automation and workflows  
🎓 **Container Registries** - Automated publishing and distribution  
🎓 **Supply Chain Security** - Understanding what's inside our containers  
🎓 **DevSecOps** - Integrating security into the development pipeline  

### Why This Matters
🌟 **Team Collaboration** - Everyone gets the same image regardless of their machine  
🌟 **Production Reliability** - Consistent, tested builds every time  
🌟 **Security Compliance** - Automated vulnerability detection and SBOM generation  
🌟 **Developer Productivity** - No manual deployment steps, focus on code  
🌟 **Platform Flexibility** - Support for different processor architectures  

This version demonstrates the evolution from manual Docker operations to fully automated, secure, multi-platform container deployment - a critical skill in modern software development.

## License

GPL-3.0 License - see LICENSE file for details.
