import os


def pytest_configure(config):
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.test"
