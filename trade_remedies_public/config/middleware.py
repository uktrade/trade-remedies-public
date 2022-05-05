import time

from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from core.models import TransientUser
from django_audit_log_middleware import AuditLogMiddleware
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin

SESSION_TIMEOUT_KEY = "_session_init_timestamp_"

# URLS that will not redirect to either 2fa or email_verify
NON_2FA_URLS = (
    reverse("email_verify"),
    reverse("two_factor"),
    reverse("logout"),
    reverse("request_new_two_factor"),
    reverse("cookie_preferences"),
    reverse("terms_and_conditions_and_privacy"),
    reverse("accessibility_statement"),
)

# URLS that do not display the back button
NON_BACK_URLS = reverse("landing")


class APIUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def should_2fa(self, request):
        """Return True/False if a request should trigger 2FA

        Arguments:
            request {object} -- Request

        Returns:
            bool -- True if should 2FA
        """
        is_public = self.public_request(request)
        should_two_factor = request.session.get("force_2fa")
        return (
            settings.USE_2FA
            and not is_public
            and should_two_factor
            and request.path not in NON_2FA_URLS
        )

    def should_verify_email(self, request):
        """Return True/False if request should trigger email verification

        Arguments:
            request {object} -- Request

        Returns:
            bool -- True if should email verify
        """
        is_public = self.public_request(request)
        return (
            settings.VERIFY_EMAIL
            and not is_public
            and not request.user.email_verified_at
            and request.path not in NON_2FA_URLS
        )

    def public_request(self, request):
        return request.path.startswith("/public")

    def __call__(self, request, *args, **kwargs):
        request.session["show_back_button"] = request.path not in NON_BACK_URLS
        if request.session and request.session.get("token") and request.session.get("user"):
            back_link_url = request.META.get("HTTP_REFERER", reverse("dashboard"))
            if request.path in back_link_url:
                back_link_url = reverse("dashboard")
            request.session["back_link_url"] = back_link_url
            if request.path in NON_2FA_URLS:
                request.session["back_link_url"] = reverse("logout")

            user = request.session["user"]
            request.user = TransientUser(token=request.session.get("token"), **user)
            request.args = args
            request.kwargs = kwargs
            request.token = request.session["token"]
            if self.should_verify_email(request):
                return redirect(reverse("email_verify"))
            if self.should_2fa(request):
                return redirect(reverse("two_factor"))
        else:
            request.session["back_link_url"] = reverse("landing")
        response = self.get_response(request)
        return response


class SessionTimeoutMiddleware(MiddlewareMixin):
    """
    Based on the middelware in django-session-timeout.
    Modified to set the request user to `AnonymousUser` rather than redirect
    to the login page.  This prevents redirects when the session has expired
    but the target view does not require an authenticated user.
    """

    def process_request(self, request):
        if not hasattr(request, "session") or request.session.is_empty():
            return

        if "upload" in request.path and request.method == "POST":
            return

        init_time = request.session.setdefault(SESSION_TIMEOUT_KEY, time.time())

        expire_seconds = getattr(settings, "SESSION_EXPIRE_SECONDS", settings.SESSION_COOKIE_AGE)

        session_is_expired = time.time() - init_time > expire_seconds

        if session_is_expired:
            request.session.flush()
            # Set request user to AnonymousUser instead of redirect to login.
            request.user = AnonymousUser()

        expire_since_last_activity = getattr(settings, "SESSION_EXPIRE_AFTER_LAST_ACTIVITY", False)
        if expire_since_last_activity:
            request.session[SESSION_TIMEOUT_KEY] = time.time()


class CacheControlMiddleware:
    """
    Send headers to prevent caching by the browser
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwargs):
        response = self.get_response(request)
        response["Cache-Control"] = "no-store"
        response["Pragma"] = "no-cache"
        response["X-Robots-Tag"] = "noindex"
        return response


class HoldingPageMiddleware(TradeRemediesAPIClientMixin):
    """
    Redirect to holding page if active
    """

    holding_page_path = "/holding_page/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwargs):
        holding_page_text = self.trusted_client.get_system_boolean("HOLDING_PAGE_TEXT", "")
        if holding_page_text:
            if request.path != self.holding_page_path:
                return redirect(self.holding_page_path)
        else:
            if request.path == self.holding_page_path:
                return redirect("/dashboard/")

        return self.get_response(request)


class CustomAuditLogMiddleware(AuditLogMiddleware):
    def _get_first_name(self):
        if self.request.user.is_authenticated:
            try:
                return self.request.user.first_name
            except AttributeError:
                pass

        return ""

    def _get_last_name(self):
        if self.request.user.is_authenticated:
            try:
                return self.request.user.last_name
            except AttributeError:
                pass
        return ""
