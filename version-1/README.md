# Flask + Tailwind To-Do App (v1 — Ephemeral)

This is **Version 1** of a learning project designed to teach Docker fundamentals by building a simple To-Do list web application.  
It uses **Flask** for the backend and **Tailwind CSS** (via CDN) for styling.  

In this first version, tasks are stored **in memory only**.  
When you stop and restart the container, **all tasks are lost** — this is intentional to demonstrate Docker's default ephemeral filesystem behavior.

## Features

- Add tasks via a form.
- View the list of current tasks.
- Delete tasks from the list.
- Styling powered by Tailwind CSS CDN.
- Runs in a single container using Flask’s built-in development server.

## Why this version is ephemeral

In Docker, if you store data inside the container’s writable layer, it disappears when the container is removed.  
This version intentionally keeps all data in a Python list in memory, so stopping or removing the container clears the tasks.

## Tech Stack

- **Python 3.x**
- **Flask** — lightweight web framework.
- **Tailwind CSS** — modern utility-first CSS framework (loaded via CDN).
- **Docker** — containerization platform.

## Running Locally (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
````

Then open [http://localhost:5000](http://localhost:5000) in your browser.

## Running in Docker

1. **Build the image:**

   ```bash
   docker build -t simple-todo:v1 .
   ```

2. **Run the container:**

   ```bash
   docker run -p 5000:5000 simple-todo:v1
   ```

3. **Access the app:**
   Open [http://localhost:5000](http://localhost:5000) in your browser.

## Learning Objectives

- Understand how Docker containers are built and run.
- Learn the difference between ephemeral storage (default) and persistent storage.
- See how application state behaves when stored in memory inside a container.

## Next Steps

In v2, we will add local persistence using a JSON file stored on a bind mount so tasks survive container restarts.

---

The line:

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
```

is commonly used in Python-based Dockerfiles. Here's what each environment variable does and **why it's used in Docker**:

---

### ✅ `PYTHONDONTWRITEBYTECODE=1`

- **What it does:** Prevents Python from writing `.pyc` files (compiled bytecode) to disk.
- **Why it's used:**

  - Keeps the container filesystem cleaner — no `__pycache__` folders or `.pyc` files.
  - Prevents unnecessary file writes, which can slightly reduce disk usage and noise in version control systems if you're mounting source code.
  - In containers, `.pyc` files don't offer much benefit because containers are usually short-lived and rebuilt often.

---

### ✅ `PYTHONUNBUFFERED=1`

- **What it does:** Tells Python to not buffer stdout and stderr.
- **Why it's used:**

  - Ensures logs from `print()` or errors appear **immediately** in the Docker logs.
  - Without this, Python may buffer output, causing delays in seeing logs (especially problematic for debugging).
  - This is crucial in environments like Docker or Kubernetes where logs are your primary way to see what the application is doing.

---

### 🔍 Summary

| Variable                    | Effect                  | Why in Docker?                |
| --------------------------- | ----------------------- | ----------------------------- |
| `PYTHONDONTWRITEBYTECODE=1` | No `.pyc` files         | Cleaner, no unneeded bytecode |
| `PYTHONUNBUFFERED=1`        | Immediate stdout/stderr | Real-time logging             |

These are best practices for making Python apps behave predictably and transparently in containers.
