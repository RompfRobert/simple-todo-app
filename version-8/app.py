import os
import signal
import sys
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, g
from sqlalchemy import create_engine, text, Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from celery_app import celery
import tempfile
import csv
import redis

# Import observability
from observability import init_observability

app = Flask(__name__)

# Initialize observability first
obs_config, metrics = init_observability(app)

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://todos:todos123@localhost:5432/todos")

# SQLAlchemy setup
Base = declarative_base()

class Todo(Base):
    __tablename__ = 'todos'
    
    id = Column(Integer, primary_key=True)
    text = Column(String(500), nullable=False)
    done = Column(Boolean, default=False, nullable=False)
    # Lower values come first when ordering
    order = Column(Integer, default=0, nullable=False)
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
        
        app.logger.info("Database connection established and tables created/verified", 
                       extra={'database_url': DATABASE_URL.replace(DATABASE_URL.split('@')[0].split('//')[-1], '***')})
        return True
        
    except Exception as e:
        app.logger.error(f"Database initialization failed: {e}", exc_info=True)
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
        # Order by the explicit order column (ascending). New items get the highest order.
        todos = db.query(Todo).order_by(Todo.order.asc(), Todo.created_at.desc()).all()
        db.close()

        # Convert to structured list for template
        tasks = [{'id': t.id, 'text': t.text, 'done': t.done} for t in todos]
        app.logger.info(f"Retrieved {len(tasks)} todos for display")
        return render_template("index.html", tasks=tasks)
    except Exception as e:
        app.logger.error(f"Error fetching todos: {e}", exc_info=True)
        return render_template("index.html", tasks=[])

@app.post("/add")
def add_task():
    """Add a new task to the database."""
    text = (request.form.get("task") or "").strip()
    if text:
        try:
            db = get_db()
            # determine next order (append to end)
            max_order = db.query(func.max(Todo.order)).scalar() or 0
            next_order = (max_order or 0) + 1
            new_todo = Todo(text=text, order=next_order)
            db.add(new_todo)
            db.commit()
            db.close()
            app.logger.info(f"Added new task: {text[:50]}...")
        except Exception as e:
            app.logger.error(f"Error adding task: {e}", exc_info=True)
    else:
        app.logger.warning("Attempted to add empty task")
            
    return redirect(url_for("index"))

@app.post("/delete/<int:todo_id>")
def delete_task(todo_id: int):
    """Delete a task by its database id."""
    try:
        db = get_db()
        todo = db.query(Todo).filter(Todo.id == todo_id).one_or_none()
        if todo:
            app.logger.info(f"Deleting task id={todo_id}: {todo.text[:50]}...")
            db.delete(todo)
            db.commit()
        else:
            app.logger.warning(f"Attempted to delete missing todo id={todo_id}")
        db.close()
    except Exception as e:
        app.logger.error(f"Error deleting task: {e}", exc_info=True)
    return redirect(url_for("index"))


@app.post('/toggle/<int:todo_id>')
def toggle_task(todo_id: int):
    """Toggle the completed state for a todo. Returns JSON."""
    try:
        db = get_db()
        todo = db.query(Todo).filter(Todo.id == todo_id).one_or_none()
        if not todo:
            db.close()
            return jsonify({'error': 'not found'}), 404
        todo.done = not bool(todo.done)
        db.add(todo)
        db.commit()
        db.close()
        return jsonify({'id': todo_id, 'done': todo.done}), 200
    except Exception as e:
        app.logger.error(f"Error toggling task: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.post('/edit/<int:todo_id>')
def edit_task(todo_id: int):
    """Edit a todo's text. Expects JSON {'text': '...'}"""
    try:
        payload = request.get_json(force=True)
        new_text = (payload.get('text') or '').strip()
        if not new_text:
            return jsonify({'error': 'empty text'}), 400
        db = get_db()
        todo = db.query(Todo).filter(Todo.id == todo_id).one_or_none()
        if not todo:
            db.close()
            return jsonify({'error': 'not found'}), 404
        todo.text = new_text
        db.add(todo)
        db.commit()
        db.close()
        return jsonify({'id': todo_id, 'text': todo.text}), 200
    except Exception as e:
        app.logger.error(f"Error editing task: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.post('/reorder')
def reorder_tasks():
    """Accepts JSON {'order': [id1,id2,...]} and updates the Todo.order field to persist ordering."""
    try:
        payload = request.get_json(force=True)
        order_list = payload.get('order') or []
        if not isinstance(order_list, list):
            return jsonify({'error': 'order must be list of ids'}), 400
        db = get_db()
        for idx, tid in enumerate(order_list, start=1):
            todo = db.query(Todo).filter(Todo.id == int(tid)).one_or_none()
            if todo:
                todo.order = idx
                db.add(todo)
        db.commit()
        db.close()
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        app.logger.error(f"Error reordering tasks: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@celery.task(bind=True)
def export_todos_task(self, filters=None):
    """Export todos to CSV - background task with metrics."""
    import time
    start_time = time.time()
    
    try:
        # Update job metrics (simplified to avoid complex metrics API)
        app.logger.info(f"Starting export task {self.request.id}", extra={'task_id': self.request.id})
        
        # Simulate slow work
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
        
        duration = time.time() - start_time
        app.logger.info(f"Export task {self.request.id} completed", 
                       extra={'task_id': self.request.id, 'duration_s': round(duration, 2), 'count': len(todos)})
        
        return {'csv_path': csv_path, 'count': len(todos)}
        
    except Exception as e:
        app.logger.error(f"Export task {self.request.id} failed: {e}", 
                        extra={'task_id': self.request.id}, exc_info=True)
        raise

@app.route('/export', methods=['POST'])
def export_todos():
    """Start background export task."""
    filters = request.json.get('filters') if request.is_json else None
    task = export_todos_task.apply_async(kwargs={'filters': filters})
    
    # Update enqueued metrics
    try:
        job_counter = metrics.counter(
            'background_jobs_total',
            'Total background jobs processed',
            labels={
                'status': lambda: 'enqueued',
                'job_type': lambda: 'export'
            }
        )
        job_counter.inc()
    except Exception as e:
        app.logger.warning(f"Failed to update export metrics: {e}")
    
    app.logger.info(f"Export task enqueued: {task.id}")
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
    """Background services health check."""
    try:
        r = redis.Redis.from_url(os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'))
        r.ping()
        app.logger.debug("Background health check passed")
        return jsonify({'redis': 'ok'}), 200
    except Exception as e:
        app.logger.error(f"Background health check failed: {e}")
        return jsonify({'redis': 'unreachable', 'error': str(e)}), 503

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    app.logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

# Initialize database on startup
if not init_database():
    app.logger.critical("Failed to initialize database. Exiting.")
    sys.exit(1)

# Set up signal handlers for graceful shutdown
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

app.logger.info("Application startup completed")

# Only run the development server when called directly
if __name__ == "__main__":
    # Run Flask's built-in development server (only for local development)
    app.logger.info("Starting development server")
    app.run(debug=True, host="0.0.0.0", port=5000)
