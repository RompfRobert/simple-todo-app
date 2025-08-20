import os
import logging
from celery import Celery
from celery.signals import worker_ready, worker_shutdown, task_prerun, task_postrun, task_failure

# Setup logging for Celery worker
from observability import ObservabilityConfig, setup_logging

# Initialize observability config
obs_config = ObservabilityConfig()

# Setup logging for worker
logging.basicConfig(level=getattr(logging, obs_config.log_level))
logger = logging.getLogger(__name__)

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/1')

celery = Celery(
    'todo_app',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)
celery.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression='gzip',
    result_compression='gzip',
)

# Celery signal handlers for observability
@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Log worker startup."""
    logger.info(f"Celery worker {sender.hostname} ready", extra={'worker_id': sender.hostname})

@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Log worker shutdown."""
    logger.info(f"Celery worker {sender.hostname} shutting down", extra={'worker_id': sender.hostname})

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Log task start."""
    logger.info(f"Task {task.name} starting", extra={
        'task_id': task_id,
        'task_name': task.name,
        'task_args': str(args)[:100],  # Truncate for safety
        'task_kwargs': str(kwargs)[:100]
    })

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Log task completion."""
    logger.info(f"Task {task.name} completed", extra={
        'task_id': task_id,
        'task_name': task.name,
        'task_state': state,
        'task_retval': str(retval)[:100] if retval else None
    })

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, einfo=None, **kwds):
    """Log task failure."""
    logger.error(f"Task {sender.name} failed", extra={
        'task_id': task_id,
        'task_name': sender.name,
        'exception': str(exception),
        'traceback': str(einfo)
    }, exc_info=True)

# Ensure Celery discovers tasks defined in the application module
celery.autodiscover_tasks(['app'])

# Also explicitly import the app module so any @celery.task decorated functions
# (like export_todos_task in app.py) are registered when the worker starts.
try:
    import app  # noqa: F401
    logger.info("Successfully imported app module for task discovery")
except Exception as e:
    # If import fails in some environments, worker may still work if tasks are
    # imported elsewhere; we swallow exceptions to avoid startup crashes here.
    logger.warning(f"Failed to import app module: {e}")
    pass
