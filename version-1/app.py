from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# In-memory task storage; resets when the process/container restarts
tasks: list[str] = []


@app.get("/")
def index():
    """Show form to add tasks and display the current list."""
    return render_template("index.html", tasks=tasks)


@app.post("/add")
def add_task():
    """Add a new task to the in-memory list and redirect to /."""
    text = (request.form.get("task") or "").strip()
    if text:
        tasks.append(text)
    return redirect(url_for("index"))


@app.post("/delete/<int:task_id>")
def delete_task(task_id: int):
    """Delete a task by its index (if valid) and redirect to /."""
    if 0 <= task_id < len(tasks):
        tasks.pop(task_id)
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Run Flask’s built-in development server
    app.run(debug=True, host="0.0.0.0", port=5000)