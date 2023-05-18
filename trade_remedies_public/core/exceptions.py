from django.core.exceptions import PermissionDenied


class SentryPermissionDenied(PermissionDenied):
    """Raises a 503 PermissionDenied error but also logs to sentry"""

    def __init__(self, message=None, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        from sentry_sdk import capture_exception

        capture_exception(self)
