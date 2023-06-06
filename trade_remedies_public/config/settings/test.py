from v2_api_client.shared.logging import PRODUCTION_LOGGING

from .base import *  # noqa

LOGGING = PRODUCTION_LOGGING  # noqa: F405

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    },
}

# speed up tests by using an easier hashing function
# https://docs.djangoproject.com/en/3.0/topics/testing/overview/#password-hashing
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
