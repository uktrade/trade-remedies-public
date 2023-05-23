from django.core.exceptions import PermissionDenied
from sentry_sdk import capture_exception, configure_scope


class LogToSentryError(Exception):
    """Base class for suspicious operations which should be logged to sentry and alert the team"""

    def __init__(self, message=None, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        with configure_scope() as scope:
            scope.set_tag("alert_team", True)
            capture_exception(self)


class SentryPermissionDenied(PermissionDenied, LogToSentryError):
    """Raises a 403 PermissionDenied error but also logs to sentry"""
