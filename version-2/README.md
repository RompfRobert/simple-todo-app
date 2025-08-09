# Flask + Tailwind To-Do App (v2 — Local Persistence via Bind Mount)

This is **Version 2** of a learning project designed to teach Docker fundamentals by building a simple To-Do list web application.  
It builds on **v1** by adding **local data persistence** using a JSON file and Docker bind mounts.  

With this version, tasks are saved to a file on the host machine so they **survive container restarts** (as long as you use the same bind mount).

---

## Features
- All features from **v1**:
  - Add, view, and delete tasks.
  - Tailwind CSS styling (via CDN).
  - Runs in a single Flask container.
- New in **v2**:
  - Tasks are stored in a JSON file instead of memory.
  - Data persists between container restarts if a bind mount is used.
  - Configurable file path via `TODO_FILE` environment variable (default: `/app/data/todos.json`).

---

## Why this version persists data
By default, Docker stores container data inside its writable layer, which is **destroyed when the container is removed**.  
In this version, we **mount a host directory into the container** so that the application writes to a file on the host.  
This allows the data to outlive the container lifecycle.

---

## Tech Stack
- **Python 3.x**
- **Flask** — lightweight web framework.
- **Tailwind CSS** — modern utility-first CSS framework (loaded via CDN).
- **Docker** — containerization platform.
- **JSON** — simple file-based storage format.

---

## Running Locally (without Docker)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
export TODO_FILE=./data/todos.json
python app.py
````

Then open [http://localhost:5000](http://localhost:5000) in your browser.
Data will be stored in `./data/todos.json`.

---

## Running in Docker with Persistence

1. **Create a directory for data:**

   ```bash
   mkdir data
   ```

2. **Build the image:**

   ```bash
   docker build -t todo-v2 .
   ```

3. **Run the container with a bind mount:**

   ```bash
   docker run -p 5000:5000 \
     -v $(pwd)/data:/app/data \
     todo-v2
   ```

4. **Access the app:**
   Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Learning Objectives

* Learn how to use **bind mounts** in Docker to persist data between container restarts.
* Understand how a container can interact with files on the host system.
* Practice configuring applications with **environment variables** for flexible file paths.

---

## Next Steps

In **v3**, we will replace the bind mount with a **named volume** to decouple the app’s persistent data from the host filesystem while still keeping it persistent between container runs.
