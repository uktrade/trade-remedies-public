from .base import *

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "verbose": {"format": "%(asctime)s %(filename)s %(lineno)d - %(levelname)s - %(message)s"},
    },
    "handlers": {
        "console": {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": True,},
        "requests": {"handlers": ["console"], "level": "WARNING", "propagate": False,},
        "urllib3": {"handlers": ["console"], "level": "WARNING", "propagate": True,},
        "cases": {"handlers": ["console"], "level": "DEBUG", "propagate": True,},
    },
}
