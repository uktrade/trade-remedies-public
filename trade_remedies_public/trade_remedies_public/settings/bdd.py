from .local import *  # noqa: F403,  F401
from .local import API_PREFIX

INSTALLED_APPS += [  # noqa
    "behave_django",
]

API_BASE_URL = "http://apitest:8000"
API_URL = f"{API_BASE_URL}/{API_PREFIX}"

# SELENIUM
SELENIUM_BROWSER = "chrome"
SELENIUM_HUB_HOST = "selenium-hub"
SELENIUM_HOST = "public"
