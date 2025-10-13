# api/__init__.py
from autotask_backend.celery import app as celery_app

__all__ = ('celery_app',)

# Cargar señales
default_app_config = 'api.apps.ApiConfig'