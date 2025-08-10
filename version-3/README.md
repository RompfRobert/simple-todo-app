# Flask + Tailwind To-Do App (v3 — Named Volume Persistence)

This is **Version 3** of a learning project designed to teach Docker fundamentals by building a simple To-Do list web application.  
It builds on **v2** by using **Docker named volumes** instead of bind mounts for data persistence.

With this version, tasks are saved to a Docker named volume, providing **decoupled persistent storage** that survives container restarts and removal without being tied to the host filesystem structure.

---

## Features
- All features from **v1** and **v2**:
  - Add, view, and delete tasks.
  - Tailwind CSS styling (via CDN).
  - Runs in a single Flask container.
  - Tasks stored in JSON file format.
  - Data persists between container restarts.
- New in **v3**:
  - Uses Docker named volumes instead of bind mounts.
  - Storage is decoupled from host working directory.
  - Easier volume management with Docker commands.
  - Robust directory creation on application startup.

---

## Why Named Volumes?

**Named volumes** offer several advantages over bind mounts:

- **Location Independence**: No dependency on `$(pwd)` or specific host paths
- **Portability**: Works consistently across different environments and machines
- **Docker Management**: Volumes are managed by Docker with built-in commands
- **Performance**: Better performance on non-Linux Docker hosts (Windows/macOS)
- **Isolation**: Volume data is isolated from host filesystem changes
- **Backup**: Easier to backup/restore using Docker volume commands

Named volumes decouple your application's persistent data from the current working directory, making deployment more flexible and robust.

---

## Tech Stack
- **Python 3.x**
- **Flask** — lightweight web framework.
- **Tailwind CSS** — modern utility-first CSS framework (loaded via CDN).
- **Docker** — containerization platform.
- **JSON** — simple file-based storage format.
- **Docker Named Volumes** — persistent storage managed by Docker.

---

## Running Locally (without Docker)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
export TODO_FILE=./data/todos.json
python app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.
Data will be stored in `./data/todos.json`.

---

## Running in Docker with Named Volume

1. **Create a named volume:**
   ```bash
   docker volume create todos_data
   ```

2. **Build the image:**
   ```bash
   docker build -t simple-todo:v3 -f version-3/Dockerfile .
   ```

3. **Run the container with the named volume:**
   ```bash
   docker run -p 5000:5000 -v todos_data:/app/data simple-todo:v3
   ```

4. **Access the app:**
   Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Volume Management Commands

### List volumes:
```bash
docker volume ls
```

### Inspect volume details:
```bash
docker volume inspect todos_data
```

### Remove the volume (deletes all data):
```bash
docker volume rm todos_data
```

### Backup volume data:
```bash
docker run --rm -v todos_data:/data -v $(pwd):/backup alpine tar czf /backup/todos_backup.tar.gz -C /data .
```

### Restore volume data:
```bash
docker run --rm -v todos_data:/data -v $(pwd):/backup alpine tar xzf /backup/todos_backup.tar.gz -C /data
```

---

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
   docker run -p 5000:5000 -v todos_data:/app/data simple-todo:v3
   ```
4. **Verify your tasks are still there**

The data persists because it's stored in the named volume, not in the container's filesystem.

---

## Learning Objectives

* Learn the difference between **bind mounts** and **named volumes**
* Understand how **named volumes** provide location-independent persistence
* Practice Docker volume management commands
* Experience how persistent data survives complete container removal and recreation

---

## Environment Variables

- `TODO_FILE`: Path to the JSON file (default: `/app/data/todos.json`)

Example with custom path:
```bash
docker run -p 5000:5000 -v todos_data:/app/storage -e TODO_FILE=/app/storage/my-todos.json simple-todo:v3
```
