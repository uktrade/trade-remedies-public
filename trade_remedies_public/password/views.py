# Views to handle the forgotten and reset password functionality

from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import TemplateView

from trade_remedies_client.exceptions import APIException
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin


class ForgotPasswordRequested(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "password/password_reset_requested.html"


class ForgotPasswordView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "password/reset_password_request.html"

    def post(self, request, *args, **kwargs):
        if email := request.POST.get("email"):
            self.trusted_client.request_password_reset(email)
            return redirect(reverse("forgot_password_requested"))
        return redirect(request.path)


class ResetPasswordView(TemplateView, TradeRemediesAPIClientMixin):
    def get(self, request, user_pk, token, *args, **kwargs):
        token_is_valid = self.trusted_client.validate_password_reset(user_pk=user_pk, token=token)
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

    def post(self, request, user_pk, token, *args, **kwargs):
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")
        if password and password_confirm and password == password_confirm:
            try:
                self.trusted_client.reset_password(token, user_pk, password)
                # todo - alert user that their password reset was successful
            except APIException as exc:
                return self.get(request, user_pk, token, error=exc.message)
        elif password != password_confirm:
            return self.get(request, user_pk, token, error="The passwords do not match")
        return redirect_to_login(reverse("dashboard"), reverse("login"), "next")
