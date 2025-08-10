import json
import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Configuration for the JSON file path
TODO_FILE = os.environ.get("TODO_FILE", "/app/data/todos.json")

# Ensure the parent directory exists on startup
os.makedirs(os.path.dirname(TODO_FILE), exist_ok=True)

def load_tasks():
    """Load tasks from the JSON file, returning empty list if file doesn't exist."""
    try:
        with open(TODO_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_tasks(tasks):
    """Save tasks to the JSON file, creating directories if needed."""
    # Ensure the directory exists (redundant safety check)
    os.makedirs(os.path.dirname(TODO_FILE), exist_ok=True)
    
    with open(TODO_FILE, 'w') as f:
        json.dump(tasks, f, indent=2)

# Load tasks from JSON file on startup
tasks: list[str] = load_tasks()


@app.get("/")
def index():
    """Show form to add tasks and display the current list."""
    return render_template("index.html", tasks=tasks)


@app.post("/add")
def add_task():
    """Add a new task to the list and save to JSON file."""
    text = (request.form.get("task") or "").strip()
    if text:
        tasks.append(text)
        save_tasks(tasks)
    return redirect(url_for("index"))


@app.post("/delete/<int:task_id>")
def delete_task(task_id: int):
    """Delete a task by its index (if valid) and save to JSON file."""
    if 0 <= task_id < len(tasks):
        tasks.pop(task_id)
        save_tasks(tasks)
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Run Flask's built-in development server
    app.run(debug=True, host="0.0.0.0", port=5000)
