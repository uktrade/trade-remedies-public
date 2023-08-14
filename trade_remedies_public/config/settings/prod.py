from v2_api_client.shared.logging import PRODUCTION_LOGGING

from .base import *  # noqa
from .hardening import *  # noqa

LOGGING = PRODUCTION_LOGGING

INSTALLED_APPS += [
    "django_audit_log_middleware",
]

MIDDLEWARE += [
    "config.middleware.CustomAuditLogMiddleware",
    "csp.middleware.CSPMiddleware",
]
