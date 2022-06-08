# Views to handle the login and logout functionality

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

from .decorators import v2_error_handling


class LandingView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "v2/landing.html"


class LoginView(BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "v2/login/login.html"

    @v2_error_handling()
    def post(self, request, *args, **kwargs):
        email = request.POST["email"]
        request.session["login_email"] = email
        password = request.POST["password"]
        invitation_code = kwargs.get("invitation_code", None)
        response = self.trusted_client.authenticate(
            email=email,
            password=password,
            user_agent=request.META["HTTP_USER_AGENT"],
            ip_address=request.META["REMOTE_ADDR"],
            invitation_code=invitation_code,
        )
        if response and response.get("token"):
            request.session.clear()
            request.session["application"] = {}
            request.session["force_2fa"] = True  # Force 2fa for every public login
            request.session["token"] = response["token"]
            request.session["user"] = response["user"]
            redirection_url = request.POST.get("next", reverse("dashboard"))
            if len(request.session["user"].get("organisations", [])) == 1:
                request.session["organisation_id"] = request.session["user"]["organisations"][0][
                    "id"
                ]
            # sending the two_factor code
            r = Client(response["token"]).two_factor_request()
            request.session["two_factor_delivery_type"] = r["delivery_type"]
            request.session.modified = True
            request.session.cycle_key()
            return internal_redirect(redirection_url, reverse("dashboard"))


class RequestNewTwoFactorView(LoginRequiredMixin, TradeRemediesAPIClientMixin, View):
    @v2_error_handling(redirection_url_resolver="two_factor")
    def get(self, request, *args, **kwargs):
        delivery_type = request.GET.get("delivery_type", "sms")
        r = self.client(request.user).two_factor_request(delivery_type=delivery_type)
        request.session["two_factor_delivery_type"] = r["delivery_type"]
        return redirect(reverse("two_factor"))


class TwoFactorView(TemplateView, LoginRequiredMixin, TradeRemediesAPIClientMixin):
    template_name = "v2/login/two_factor.html"

    @v2_error_handling()
    def post(self, request, *args, **kwargs):
        two_factor_code = request.POST["code"]
        response = self.client(request.user).two_factor_auth(
            code=two_factor_code,
            user_agent=request.META["HTTP_USER_AGENT"],
            ip_address=request.META["REMOTE_ADDR"],
        )
        request.session["user"] = response
        request.session.pop("force_2fa", None)
        request.session.modified = True
        return redirect(reverse("dashboard"))


def logout_view(request):
    if "token" in request.session:
        del request.session["token"]
    if "user" in request.session:
        del request.session["user"]
    logout(request)
    return redirect(reverse("landing"))
