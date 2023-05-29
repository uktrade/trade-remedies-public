from django.core.exceptions import PermissionDenied
from v2_api_client.shared.logging import audit_logger


class SentryPermissionDenied(PermissionDenied):
    """Raises a 503 PermissionDenied error but also logs to sentry"""

    def __init__(self, message=None, *args, **kwargs):
        super().__init__(message, *args, **kwargs)

        # first we send to sentry
        from sentry_sdk import capture_exception

        capture_exception(self)

        # then we log to the django logger
        audit_logger.warning(message)
