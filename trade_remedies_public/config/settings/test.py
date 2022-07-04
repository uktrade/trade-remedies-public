from .base import *  # noqa

LOGGING = ENVIRONMENT_LOGGING  # noqa: F405

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    },
}
