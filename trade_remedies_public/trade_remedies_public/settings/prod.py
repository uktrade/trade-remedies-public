from .base import *  # noqa

LOGGING = ENVIRONMENT_LOGGING  # noqa: F405

INSTALLED_APPS += [  # noqa: F405
    "django_audit_log_middleware",
]

MIDDLEWARE += [  # noqa: F405
    "django_audit_log_middleware.AuditLogMiddleware",
]
