from .base import *  # noqa: F403,  F401

INSTALLED_APPS += [  # noqa
    "behave_django",
]

# SELENIUM
SELENIUM_BROWSER = "chrome"
SELENIUM_HUB_HOST = "selenium-hub"
SELENIUM_HOST = "public"
