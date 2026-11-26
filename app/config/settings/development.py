from copy import deepcopy
from .base import *

DEBUG = True
ENVIRONMENT_NAME = "DEVELOPMENT"


# Django 4.1+ caches compiled templates by default, even with DEBUG=True.
# In development, use non-caching template loaders so HTML changes
# appear on browser refresh without restarting Gunicorn or Docker.
# Production retains the default cached template loader for performance.
TEMPLATES = deepcopy(TEMPLATES)

TEMPLATES[0]["APP_DIRS"] = False

TEMPLATES[0]["OPTIONS"]["loaders"] = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]