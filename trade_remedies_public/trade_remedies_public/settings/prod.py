from .base import *  # noqa

LOGGING = ENVIRONMENT_LOGGING  # noqa: F405

INSTALLED_APPS += [
    "django_audit_log_middleware",
]

MIDDLEWARE += [
    "django_audit_log_middleware.AuditLogMiddleware",
]
