# Views to handle the login and logout functionality

import json
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout

from core.utils import (
    validate,
    get,
    set_cookie,
)
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
from core.validators import (
    registration_validators,
    base_registration_validators,
)
from core.utils import internal_redirect
from registration.views import BaseRegisterView


class LoginChoiceView(BaseRegisterView):
    template_name = "login/login_choice.html"

    @never_cache
    def get(self, request, code=None, case_id=None, *args, **kwargs):
        error = request.GET.get("error")
        if error is None:
            request.session["errors"] = None
        return render(
            request,
            self.template_name,
            {
                "code": code,
                "case_id": case_id,
                "errors": request.session.get("errors", None),
            },
        )


class LoginView(BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "login/login.html"

    @never_cache
    def get(self, request, code=None, case_id=None, *args, **kwargs):
        error = request.GET.get("error")
        email_verified = request.session.get("email_verified")
        request.session["next"] = request.GET.get("next")
        if error is None:
            request.session["errors"] = None
        if email_verified:
            request.session["email_verified"] = None
        request.session.modified = True
        request.session.cycle_key()
        if code and case_id:
            # We're processing an invite URL
            return redirect("register_invite", code=code, case_id=case_id)
        return render(
            request,
            self.template_name,
            {
                "all_organisations": True,
                "email": request.GET.get("email") or "",
                "code": code,
                "case_id": case_id,
                "short_code": request.GET.get("short_code"),
                "welcome": request.GET.get("welcome"),
                "expired": request.GET.get("expired"),
                "errors": request.session.get("errors", None),
                "email_verified": email_verified,
                "next": request.GET.get("next"),
            },
        )

    def post(self, request, *args, **kwargs):  # noqa: C901
        email = request.POST.get("email")
        password = request.POST.get("password")
        code = request.POST.get("code")
        short_code = request.POST.get("short_code")
        case_id = request.POST.get("case_id")
        errors = validate({"email": email, "password": password}, base_registration_validators)
        if errors:
            request.session["errors"] = errors
            return redirect("/accounts/login/?error")
        try:
            response = self.trusted_client.authenticate(
                email,
                password,
                user_agent=request.META["HTTP_USER_AGENT"],
                ip_address=request.META["REMOTE_ADDR"],
                code=code,
                case_id=case_id,
            )
            if response and response.get("token"):
                # TODO: Temporary application state initialisation
                request.session.clear()
                request.session["application"] = {}
                # TODO: Tmp app state end
                # Force 2fa for every public login
                request.session["force_2fa"] = True
                request.session["token"] = response["token"]
                request.session["user"] = response["user"]
                request.session["version"] = response.get("version")
                redirection_url = request.POST.get("next") or "/dashboard/"
                if len(request.session["user"].get("organisations", [])) == 1:
                    request.session["organisation_id"] = request.session["user"]["organisations"][
                        0
                    ]["id"]
                request.session.modified = True
                request.session.cycle_key()
                return internal_redirect(redirection_url, "/dashboard/")
            else:
                if case_id and code:
                    return redirect(f"/accounts/login/{code}/{case_id}/?error=t")
                elif short_code:
                    return redirect(f"/accounts/login/?error=t&short_code={short_code}")
                else:
                    return redirect("/accounts/login/?error=t")
        except Exception as exc:
            detail = ""
            if hasattr(exc, "response"):
                try:
                    if exc.response.status_code == 401:
                        try:
                            detail = exc.response.json().get("detail")
                        except Exception:
                            detail = """You have entered an incorrect email address or password.
                                        Please try again or click on the
                                        Forgotten password link below."""
                    else:
                        response = exc.response.json()
                        detail = response.get("detail")
                except json.decoder.JSONDecodeError:
                    detail = exc.response.text
            else:
                detail = str(exc)
            request.session["errors"] = {"email": detail}
            request.session.modified = True
            if case_id and code:
                return redirect(f"/accounts/login/{code}/{case_id}/?error")
            else:
                return redirect("/accounts/login/?error")


def logout_view(request):
    if "token" in request.session:
        del request.session["token"]
    if "user" in request.session:
        del request.session["user"]
    logout(request)
    return redirect("/accounts/login/")
