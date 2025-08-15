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
celery.autodiscover_tasks(['.'])
