# Views to handle the forgotten and reset password functionality
import requests
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import TemplateView

from trade_remedies_client.mixins import TradeRemediesAPIClientMixin

from password.decorators import v2_error_handling

from config.settings.base import API_BASE_URL, HEALTH_CHECK_TOKEN, ENVIRONMENT_KEY


class ForgotPasswordRequested(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "password/password_reset_requested.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        user_pk = request.GET.get("user_pk")
        headers = {
            "Authorization": f"Token {HEALTH_CHECK_TOKEN}",  # /PS-IGNORE
            "X-Origin-Environment": ENVIRONMENT_KEY,
            "X-User-Agent": "",
            "X-Forwarded-For": "",
        }
        url = f"{API_BASE_URL}/api/v2/accounts/password/pk_request_reset/"
        if user_pk:
            requests.get(url, headers=headers, params={"user_pk": user_pk})
        return self.render_to_response(context)


class ForgotPasswordView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "password/reset_password_request.html"

    @v2_error_handling()
    def post(self, request, *args, **kwargs):
        email = request.POST.get("email")
        self.trusted_client.request_password_reset(email)
        return redirect(reverse("forgot_password_requested"))


class ResetPasswordView(TemplateView, TradeRemediesAPIClientMixin):
    def get(self, request, user_pk, token, *args, **kwargs):
        token_is_valid = self.trusted_client.validate_password_reset(user_pk=user_pk, token=token)
        if not token_is_valid:
            return render(
                request,
                "v2/password/reset_password_expired.html",
                {
                    "user_pk": user_pk,
                },
            )
        error_message = kwargs.get("error", None)
        return render(
            request,
            "password/reset_password.html",
            {
                "token_is_valid": token_is_valid,
                "user_pk": user_pk,
                "token": token,
                "error": error_message,
            },
        )

    @v2_error_handling()
    def post(self, request, user_pk, token, *args, **kwargs):
        password = request.POST.get("password")
        self.trusted_client.reset_password(token, user_pk, password)
        return redirect(reverse("reset_password_success"))


class ResetPasswordSuccessView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "v2/password/reset_password_success.html"
