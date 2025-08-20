"""
Gunicorn configuration for production deployment with JSON logging.
"""
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = int(os.environ.get('GUNICORN_WORKERS', 2))
worker_class = 'gthread'
threads = int(os.environ.get('GUNICORN_THREADS', 4))
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 30
keepalive = 2
graceful_timeout = 30

# Logging
errorlog = '-'
accesslog = '-'  # Enable access log to stdout  
loglevel = os.environ.get('LOG_LEVEL', 'info').lower()

# Use a simple access log format that will be processed by our JSON formatter
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Custom access log format processor
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Gunicorn server with observability features")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Gunicorn workers")

def worker_int(worker):
    """Called just after a worker has been killed."""
    worker.log.info(f"Worker {worker.pid} killed")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker {worker.pid} spawned")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Gunicorn server ready")

def worker_abort(worker):
    """Called when a worker process is aborted."""
    worker.log.warning(f"Worker {worker.pid} aborted")

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL (disabled for this version)
# keyfile = None
# certfile = None

# Process naming
proc_name = 'simple-todo-web'

# Temp directory
tmp_upload_dir = None

# Debugging
spew = False

# Environment variables for the application
raw_env = [
    f"GUNICORN_WORKERS={workers}",
    f"GUNICORN_THREADS={threads}",
    f"WORKER_PID={{os.getpid()}}",
]
