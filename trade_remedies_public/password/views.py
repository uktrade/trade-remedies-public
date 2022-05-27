# Views to handle the forgotten and reset password functionality
from http import HTTPStatus

import requests
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import TemplateView
from requests import HTTPError

from trade_remedies_client.mixins import TradeRemediesAPIClientMixin

from password.decorators import v2_error_handling

from config.settings.base import API_BASE_URL, HEALTH_CHECK_TOKEN, ENVIRONMENT_KEY

API_HEADERS = {
    "Authorization": f"Token {HEALTH_CHECK_TOKEN}",  # /PS-IGNORE
    "X-Origin-Environment": ENVIRONMENT_KEY,
    "X-User-Agent": "",
    "X-Forwarded-For": "",
}


class ForgotPasswordRequested(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "password/password_reset_requested.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        request_id = request.GET.get("request_id")
        url = f"{API_BASE_URL}/api/v2/accounts/password/request_reset/"
        if request_id:
            response = requests.get(url, headers=API_HEADERS, params={"request_id": request_id})
            response.raise_for_status()
        return self.render_to_response(context)


class ForgotPasswordView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "password/reset_password_request.html"

    @v2_error_handling()
    def post(self, request, *args, **kwargs):
        email = request.POST.get("email")
        self.trusted_client.request_password_reset(email)
        return redirect(reverse("forgot_password_requested"))


class ResetPasswordView(TemplateView, TradeRemediesAPIClientMixin):
    def get(self, request, request_id, token, *args, **kwargs):
        url = f"{API_BASE_URL}/api/v2/accounts/password/reset_form/"
        response = requests.get(
            url, headers=API_HEADERS, params={"request_id": request_id, "token": token}
        )
        response.raise_for_status()
        response = response.json()
        token_is_valid = response.get("response").get("result")
        if not token_is_valid:
            return render(
                request,
                "v2/password/reset_password_expired.html",
                {
                    "request_id": request_id,
                },
            )
        error_message = kwargs.get("error", None)
        return render(
            request,
            "password/reset_password.html",
            {
                "token_is_valid": token_is_valid,
                "request_id": request_id,
                "token": token,
                "error": error_message,
            },
        )

    @v2_error_handling()
    def post(self, request, request_id, token, *args, **kwargs):
        password = request.POST.get("password")
        url = f"{API_BASE_URL}/api/v2/accounts/password/reset_form/"
        response = requests.post(
            url,
            headers=API_HEADERS,
            data={"request_id": request_id, "token": token, "password": password},
        )
        response.raise_for_status()
        return redirect(reverse("reset_password_success"))


class ResetPasswordSuccessView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "v2/password/reset_password_success.html"

    def post(self, request, *args, **kwargs):
        return redirect(reverse("login"))
