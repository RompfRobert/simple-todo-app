# Flask + Tailwind To-Do App (v1 — Ephemeral)

This is **Version 1** of a learning project designed to teach Docker fundamentals by building a simple To-Do list web application.  
It uses **Flask** for the backend and **Tailwind CSS** (via CDN) for styling.  

In this first version, tasks are stored **in memory only**.  
When you stop and restart the container, **all tasks are lost** — this is intentional to demonstrate Docker's default ephemeral filesystem behavior.

---

## Features
- Add tasks via a form.
- View the list of current tasks.
- Delete tasks from the list.
- Styling powered by Tailwind CSS CDN.
- Runs in a single container using Flask’s built-in development server.

---

## Why this version is ephemeral
In Docker, if you store data inside the container’s writable layer, it disappears when the container is removed.  
This version intentionally keeps all data in a Python list in memory, so stopping or removing the container clears the tasks.

---

## Tech Stack
- **Python 3.x**
- **Flask** — lightweight web framework.
- **Tailwind CSS** — modern utility-first CSS framework (loaded via CDN).
- **Docker** — containerization platform.

---

## Running Locally (without Docker)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
````

Then open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Running in Docker

1. **Build the image:**

   ```bash
   docker build -t todo-v1 .
   ```

2. **Run the container:**

   ```bash
   docker run -p 5000:5000 todo-v1
   ```

3. **Access the app:**
   Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Learning Objectives

* Understand how Docker containers are built and run.
* Learn the difference between ephemeral storage (default) and persistent storage.
* See how application state behaves when stored in memory inside a container.

---

## Next Steps

In v2, we will add local persistence using a JSON file stored on a bind mount so tasks survive container restarts.
