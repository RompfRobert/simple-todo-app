import os
import signal
import sys
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from sqlalchemy import create_engine, text, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from celery_app import celery
import tempfile
import csv
import redis

app = Flask(__name__)

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://todos:todos123@localhost:5432/todos")

# SQLAlchemy setup
Base = declarative_base()

class Todo(Base):
    __tablename__ = 'todos'
    
    id = Column(Integer, primary_key=True)
    text = Column(String(500), nullable=False)
    done = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# Database connection
engine = None
SessionLocal = None

def init_database():
    """Initialize database connection and create tables if needed."""
    global engine, SessionLocal
    
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        print("Database connection established and tables created/verified.")
        return True
        
    except Exception as e:
        print(f"Database initialization failed: {e}")
        return False

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise

@app.route("/healthz")
def health_check():
    """Health check endpoint that returns 200 without touching database."""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200

@app.get("/")
def index():
    """Show form to add tasks and display the current list."""
    try:
        db = get_db()
        todos = db.query(Todo).order_by(Todo.created_at.desc()).all()
        db.close()
        
        # Convert to simple list format for template compatibility
        tasks = [todo.text for todo in todos]
        return render_template("index.html", tasks=tasks)
        
    except Exception as e:
        print(f"Error fetching todos: {e}")
        return render_template("index.html", tasks=[])

@app.post("/add")
def add_task():
    """Add a new task to the database."""
    text = (request.form.get("task") or "").strip()
    if text:
        try:
            db = get_db()
            new_todo = Todo(text=text)
            db.add(new_todo)
            db.commit()
            db.close()
        except Exception as e:
            print(f"Error adding task: {e}")
            
    return redirect(url_for("index"))

@app.post("/delete/<int:task_id>")
def delete_task(task_id: int):
    """Delete a task by its position in the list (for template compatibility)."""
    try:
        db = get_db()
        todos = db.query(Todo).order_by(Todo.created_at.desc()).all()
        
        if 0 <= task_id < len(todos):
            todo_to_delete = todos[task_id]
            db.delete(todo_to_delete)
            db.commit()
            
        db.close()
        
    except Exception as e:
        print(f"Error deleting task: {e}")
        
    return redirect(url_for("index"))

@celery.task(bind=True)
def export_todos_task(self, filters=None):
    # Simulate slow work
    import time
    time.sleep(5)
    # Query todos from DB (pseudo-code, replace with real query)
    todos = []  # TODO: fetch from DB, apply filters
    # For demonstration, create dummy data
    todos = [
        {'id': 1, 'title': 'Task 1', 'done': False},
        {'id': 2, 'title': 'Task 2', 'done': True},
    ]
    # Write CSV into a shared exports directory so the web app can serve it
    export_dir = os.environ.get('EXPORT_DIR', '/app/data/exports')
    os.makedirs(export_dir, exist_ok=True)
    csv_path = os.path.join(export_dir, f'todos_export_{self.request.id}.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['id', 'title', 'done'])
        writer.writeheader()
        for todo in todos:
            writer.writerow(todo)
    return {'csv_path': csv_path, 'count': len(todos)}

@app.route('/export', methods=['POST'])
def export_todos():
    filters = request.json.get('filters') if request.is_json else None
    task = export_todos_task.apply_async(kwargs={'filters': filters})
    return jsonify({'task_id': task.id}), 202

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task = export_todos_task.AsyncResult(task_id)
    response = {
        'task_id': task_id,
        'state': task.state,
        'info': task.info if task.info else {},
        'ready': task.ready(),
        'successful': task.successful(),
    }
    return jsonify(response)

@app.route('/download/<task_id>', methods=['GET'])
def download_csv(task_id):
    task = export_todos_task.AsyncResult(task_id)
    if not task.successful():
        return jsonify({'error': 'Task not completed'}), 404
    csv_path = task.info.get('csv_path')
    if not csv_path or not os.path.exists(csv_path):
        return jsonify({'error': 'CSV not found'}), 404
    return send_file(csv_path, mimetype='text/csv', as_attachment=True, download_name=f'todos_{task_id}.csv')

@app.route('/healthz/background', methods=['GET'])
def healthz_background():
    try:
        r = redis.Redis.from_url(os.environ['CELERY_BROKER_URL'])
        r.ping()
        return jsonify({'redis': 'ok'}), 200
    except Exception as e:
        return jsonify({'redis': 'unreachable', 'error': str(e)}), 503

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

# Initialize database on startup
if not init_database():
    print("Failed to initialize database. Exiting.")
    sys.exit(1)

# Set up signal handlers for graceful shutdown
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Only run the development server when called directly
if __name__ == "__main__":
    # Run Flask's built-in development server (only for local development)
    app.run(debug=True, host="0.0.0.0", port=5000)
