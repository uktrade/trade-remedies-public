# Views to handle the login and logout functionality

import json

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout

from core.utils import validate
from django.views.generic import TemplateView
from trade_remedies_client.client import Client
from trade_remedies_client.exceptions import APIException

from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
from core.validators import base_registration_validators
from core.utils import internal_redirect
from registration.views import BaseRegisterView


class LandingView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "v2/landing.html"


class LoginView(BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "v2/login/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_errors"] = self.request.session.pop("errors", None)
        return context

    def post(self, request, *args, **kwargs):
        email = request.POST["email"]
        password = request.POST["password"]
        invitation_code = kwargs.get("invitation_code", None)
        try:
            response = self.trusted_client.authenticate(
                email=email,
                password=password,
                user_agent=request.META["HTTP_USER_AGENT"],
                ip_address=request.META["REMOTE_ADDR"],
                invitation_code=invitation_code
            )
            if response and response.get("token"):
                request.session.clear()
                request.session["application"] = {}
                request.session["force_2fa"] = True  # Force 2fa for every public login
                request.session["token"] = response["token"]
                request.session["user"] = response["user"]
                redirection_url = request.POST.get("next", reverse("dashboard"))
                if len(request.session["user"].get("organisations", [])) == 1:
                    request.session["organisation_id"] = request.session["user"]["organisations"][
                        0
                    ]["id"]
                if response["user"]["should_two_factor"]:
                    # sending the two_factor code if appropriate
                    r = Client(response["token"]).two_factor_request()
                    request.session["two_factor_delivery_type"] = r["result"]["delivery_type"]
                request.session.modified = True
                request.session.cycle_key()
                return internal_redirect(redirection_url, reverse("dashboard"))
        except APIException as exc:
            request.session["errors"] = exc.detail
            return redirect(request.path)


class RequestNewTwoFactorView(LoginRequiredMixin, TradeRemediesAPIClientMixin, View):
    def get(self, request, *args, **kwargs):
        if two_factor_code_last_sent := request.session.get("2fa_code_last_sent"):
            if (timezone.now() - two_factor_code_last_sent).seconds <= \
                    settings.TWO_FACTOR_RESEND_TIMEOUT_SECONDS:
                # The last 2fa message was within the last 20 seconds ago, don't send again
                # todo - feedback to user
                return redirect(reverse("two_factor"))

        delivery_type = request.GET.get("delivery_type", "sms")
        r = self.client(request.user).two_factor_request(delivery_type=delivery_type)
        request.session["two_factor_delivery_type"] = r["result"]["delivery_type"]
        request.session["2fa_code_last_sent"] = timezone.now()
        return redirect(reverse("two_factor"))


class TwoFactorView(TemplateView, LoginRequiredMixin, TradeRemediesAPIClientMixin):
    template_name = "v2/login/two_factor.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_errors"] = self.request.session.pop("errors", None)
        return context

    def post(self, request, *args, **kwargs):
        two_factor_code = request.POST["2fa_code"]
        try:
            response = self.client(request.user).two_factor_auth(
                code=two_factor_code,
                user_agent=request.META["HTTP_USER_AGENT"],
                ip_address=request.META["REMOTE_ADDR"],
            )
            request.session["user"] = response["result"]
            request.session.pop("force_2fa", None)
            request.session.modified = True
            return redirect(reverse("dashboard"))
        except APIException as exc:
            request.session["errors"] = exc.detail
            return redirect(request.path)


def logout_view(request):
    if "token" in request.session:
        del request.session["token"]
    if "user" in request.session:
        del request.session["user"]
    logout(request)
    return redirect("/accounts/login/")
