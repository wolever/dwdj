try:
    from .shortcuts import r2r
    from .views import redirect_next, guess_next
except ImportError as e:
    if "DJANGO_SETTINGS_MODULE" not in str(e):
        raise

__version__ = (0, 5, 0)
