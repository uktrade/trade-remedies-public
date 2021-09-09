from .base import *  # noqa: F403,  F401

INSTALLED_APPS += [  # noqa
    "behave_django",
]

# speed up tests
# https://docs.djangoproject.com/en/3.0/topics/testing/overview/#password-hashing
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# SELENIUM
SELENIUM_BROWSER = "chrome"
SELENIUM_HUB_HOST = "selenium-hub"
SELENIUM_HOST = "public"
