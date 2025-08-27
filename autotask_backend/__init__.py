# __init__.py (en la carpeta de tu proyecto)
from .celery import app as celery_app

__all__ = ('celery_app',)