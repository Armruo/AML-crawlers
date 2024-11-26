import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aml_crawlers.settings')

app = Celery('aml_crawlers')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
