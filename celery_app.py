import os
from celery import Celery

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
)
# Ensure Celery discovers tasks defined in the application module
celery.autodiscover_tasks(['app'])

# Also explicitly import the app module so any @celery.task decorated functions
# (like export_todos_task in app.py) are registered when the worker starts.
try:
    import app  # noqa: F401
except Exception:
    # If import fails in some environments, worker may still work if tasks are
    # imported elsewhere; we swallow exceptions to avoid startup crashes here.
    pass
