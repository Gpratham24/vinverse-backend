"""
VinVerse Django project initialization.
"""
# Import Celery app to ensure it's loaded when Django starts
# Make it optional so Django can start even if Celery isn't installed yet
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery not installed yet - Django can still run
    __all__ = ()
