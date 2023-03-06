import os


def pytest_configure(config):
    os.environ["HEALTH_CHECK_TOKEN"] = "xxx"
    os.environ["FEATURE_FLAGS_TTL"] = "300"
    os.environ["SYSTEM_PARAMS_TTL"] = "300"
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.local"
    os.environ["REDIS_BASE_URL"] = "redis://localhost:6379"
    os.environ["DEBUG"] = "1"
