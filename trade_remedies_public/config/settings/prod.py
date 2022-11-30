from .base import *  # noqa
from .hardening import *  # noqa

LOGGING = ENVIRONMENT_LOGGING  # noqa: F405

INSTALLED_APPS += [  # noqa: F405
    "django_audit_log_middleware",
]

MIDDLEWARE += [  # noqa: F405
    "config.middleware.CustomAuditLogMiddleware",
    "csp.middleware.CSPMiddleware",
]
