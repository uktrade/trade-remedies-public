# Views to handle the login and logout functionality
import logging
import secrets

from django.conf import settings
from django.core.cache import caches
from v2_api_client.shared.logging import audit_logger

from core.decorators import catch_form_errors
from core.utils import internal_redirect
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from registration.views import BaseRegisterView
from trade_remedies_client.client import Client
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin

logger = logging.getLogger(__name__)


class LandingView(TemplateView):
    template_name = "v2/landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse("dashboard"))
        else:
            return super().dispatch(request, *args, **kwargs)


class LoginView(BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "v2/login/login.html"

    @catch_form_errors()
    def post(self, request, *args, **kwargs):
        email = request.POST["email"]
        request.session["login_email"] = email
        password = request.POST["password"]
        invitation_code = kwargs.get("invitation_code", None)
        response = self.trusted_client.authenticate(
            email=email, password=password, invitation_code=invitation_code
        )
        if response and response.get("token"):
            request.session.clear()
            request.session["application"] = {}

            if settings.USE_2FA:
                request.session["force_2fa"] = True  # Force 2fa for every public login
                # sending the two_factor code
                r = Client(response["token"]).two_factor_request()
                request.session["two_factor_delivery_type"] = r["delivery_type"]
            request.session["token"] = response["token"]
            request.session["user"] = response["user"]
            redirection_url = request.POST.get("next", reverse("dashboard"))
            if len(request.session["user"].get("organisations", [])) == 1:
                request.session["organisation_id"] = request.session["user"]["organisations"][0][
                    "id"
                ]
            request.session.modified = True
            request.session.cycle_key()

            # setting a random key to both the request.session and the django cache. This is checked
            # in middleware every request and if it doesn't match, the user is logged out.
            # this is to stop concurrent logins, when the user logs in from another browser, a new
            # secret is set and suddenly the old one doesn't equal the one in the cache.
            concurrent_logins_caches = caches["concurrent_logins"]
            random_key = secrets.token_urlsafe(16)
            concurrent_logins_caches.set(email, random_key)
            request.session["random_key"] = random_key
            return internal_redirect(redirection_url, reverse("dashboard"))


class RequestNewTwoFactorView(LoginRequiredMixin, TradeRemediesAPIClientMixin, View):
    @catch_form_errors(redirection_url_resolver="two_factor")
    def get(self, request, *args, **kwargs):
        delivery_type = request.GET.get("delivery_type", "sms")
        r = self.client(request.user).two_factor_request(delivery_type=delivery_type)
        request.session["two_factor_delivery_type"] = r["delivery_type"]
        return redirect(reverse("two_factor"))


class TwoFactorView(TemplateView, LoginRequiredMixin, TradeRemediesAPIClientMixin):
    template_name = "v2/login/two_factor.html"

    @catch_form_errors()
    def post(self, request, *args, **kwargs):
        two_factor_code = request.POST["code"]
        response = self.client(request.user).two_factor_auth(
            code=two_factor_code,
            user_agent=request.META["HTTP_USER_AGENT"],
            ip_address=request.META["REMOTE_ADDR"],
        )
        audit_logger.info("User logged in", extra={"user": response["id"]})
        request.session["user"] = response
        request.session.pop("force_2fa", None)
        request.session.modified = True
        return redirect(reverse("dashboard"))


def logout_view(request):
    # logout view

    # we want to pick this up from the session here before it gets deleted
    logged_out_by_other_session = request.session.get("logged_out_by_other_session", False)
    audit_logger.info("User logged out", extra={"user": request.user.id})
    if "token" in request.session:
        del request.session["token"]
    if "user" in request.session:
        del request.session["user"]
    logout(request)
    if logged_out_by_other_session:
        return redirect(f"{reverse('login')}?logged_out_by_other_session=true")
    return redirect(reverse("landing"))
