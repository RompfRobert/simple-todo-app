# Flask + Tailwind To-Do App (v4 — Production Multi-stage Build)

This is **Version 4** of a learning project designed to teach Docker fundamentals by building a simple To-Do list web application.  
It builds on **v3** by implementing a **production-ready multi-stage Docker build** with **Gunicorn** as the WSGI server.

With this version, the app runs behind Gunicorn for better performance and uses a multi-stage build to create smaller, more secure production images.

## Features

- All features from **v1**, **v2**, and **v3**:
  - Add, view, and delete tasks.
  - Tailwind CSS styling (via CDN).
  - Tasks stored in JSON file format.
  - Data persists using Docker named volumes.
- New in **v4**:
  - **Gunicorn WSGI server** instead of Flask development server.
  - **Multi-stage Docker build** for smaller production images.
  - **Pre-built wheels** for faster container startup.
  - **Production-optimized** configuration.

## Why Multi-stage Builds?

**Multi-stage builds** provide several production benefits:

- **Smaller Images**: Final image only contains runtime dependencies, not build tools
- **Layer Optimization**: Build dependencies are cached in separate layers
- **Security**: Fewer packages and tools in production image reduce attack surface
- **Performance**: Pre-built wheels speed up container startup
- **Separation**: Clear separation between build and runtime environments

The builder stage creates optimized wheels, while the production stage uses only what's needed to run the app.

> Why? It’s faster and avoids needing to compile packages again later.
> Think of wheels as ready-to-install versions of your libraries.

## Why Gunicorn?

**Gunicorn** is a production-grade WSGI server that offers:

- **Multi-worker processing** for better concurrency
- **Thread support** for I/O-bound operations
- **Process management** and automatic worker restarts
- **Production stability** and performance optimizations
- **Security features** and proper signal handling

Configuration: `gunicorn -w 2 -k gthread --threads 4 -b 0.0.0.0:5000 app:app`

## Tech Stack

- **Python 3.x** — Latest stable Python version
- **Flask** — Lightweight web framework
- **Gunicorn** — Production WSGI server  
- **Tailwind CSS** — Modern utility-first CSS framework (loaded via CDN)
- **Docker Multi-stage** — Optimized container builds
- **JSON** — Simple file-based storage format
- **Docker Named Volumes** — Persistent storage managed by Docker

## Running Locally (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Run with Flask development server
export TODO_FILE=./data/todos.json
python app.py

# Or run with Gunicorn (production-like)
export TODO_FILE=./data/todos.json
gunicorn -w 2 -k gthread --threads 4 -b 0.0.0.0:5000 app:app
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

## Running in Docker (Production)

1. **Create a named volume:**

   ```bash
   docker volume create todos_data
   ```

2. **Build the production image:**

   ```bash
   docker build -t simple-todo:v4 -f version-4/Dockerfile .
   ```

3. **Run the container with named volume:**

   ```bash
   docker run -p 5000:5000 -v todos_data:/app/data simple-todo:v4
   ```

4. **Access the app:**
   Open [http://localhost:5000](http://localhost:5000) in your browser.

## Verifying Production Setup

### Check that Gunicorn is serving the app

```bash
curl -I http://localhost:5000
```

You should see `Server: gunicorn` in the response headers.

### Check container size comparison

```bash
docker images | grep simple-todo
```

Version 4 should be smaller than previous versions due to multi-stage build optimization.

### Check running processes inside container

```bash
docker exec <container-id> ps aux
```

You should see Gunicorn master and worker processes.

## Volume Management Commands

### List volumes

```bash
docker volume ls
```

### Inspect volume details

```bash
docker volume inspect todos_data
```

### Remove the volume (deletes all data)

```bash
docker volume rm todos_data
```

### Backup volume data

```bash
docker run --rm -v todos_data:/data -v $(pwd):/backup alpine tar czf /backup/todos_backup.tar.gz -C /data .
```

### Restore volume data

```bash
docker run --rm -v todos_data:/data -v $(pwd):/backup alpine tar xzf /backup/todos_backup.tar.gz -C /data
```

## Production Deployment

For production deployment, consider:

```bash
# Run with resource limits
docker run -d \
  --name todo-app \
  --restart unless-stopped \
  -p 5000:5000 \
  -v todos_data:/app/data \
  --memory="256m" \
  --cpus="0.5" \
  simple-todo:v4

# Or with custom Gunicorn settings
docker run -d \
  --name todo-app \
  -p 5000:5000 \
  -v todos_data:/app/data \
  -e GUNICORN_WORKERS=4 \
  -e GUNICORN_THREADS=2 \
  simple-todo:v4
```

## Testing Persistence

To verify that data persists across container lifecycle:

1. **Start the app and add some tasks**
2. **Stop and remove the container:**

   ```bash
   docker stop <container-id>
   docker rm <container-id>
   ```

3. **Run a new container with the same volume:**

   ```bash
   docker run -p 5000:5000 -v todos_data:/app/data simple-todo:v4
   ```

4. **Verify your tasks are still there**

## Learning Objectives

- Learn **multi-stage Docker builds** for production optimization
- Understand the difference between **development** and **production** servers
- Practice using **Gunicorn** as a production WSGI server
- Experience **Docker image size optimization** techniques

## Environment Variables

- `TODO_FILE`: Path to the JSON file (default: `/app/data/todos.json`)
- `GUNICORN_WORKERS`: Number of worker processes (optional)
- `GUNICORN_THREADS`: Number of threads per worker (optional)

Example with custom configuration:

```bash
docker run -p 5000:5000 \
  -v todos_data:/app/data \
  -e TODO_FILE=/app/data/my-todos.json \
  -e GUNICORN_WORKERS=3 \
  simple-todo:v4
```
