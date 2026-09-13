import os
from celery import Celery

# Set default settings modul untuk program Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms_core.settings')

app = Celery('lms_core')

# Baca config Celery dari settings.py Django (variabel yang diawali CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules dari semua aplikasi Django yang terdaftar
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')