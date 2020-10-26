import json
import re
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from core.models import TransientUser
from django.contrib.auth import logout
from django_countries import countries
from core.utils import (
    validate,
    get,
    set_cookie,
)
from core.constants import ALERT_MAP
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
from core.validators import (
    registration_validators,
    base_registration_validators,
)


def logout_view(request):
    if "token" in request.session:
        del request.session["token"]
    if "user" in request.session:
        del request.session["user"]
    logout(request)
    return redirect("/accounts/login/")


class BaseRegisterView(TemplateView):
    def reset_session(self, request, initial_data=None):
        initial_data = initial_data or {}
        request.session["registration"] = initial_data
        request.session.modified = True
        return request.session

    def update_session(self, request, update_data):
        request.session.setdefault("registration", {})
        request.session["registration"].update(update_data)
        request.session.modified = True
        return request.session

    def vaidate_session(self, request, fields, message=None):
        message = message or "Required"
        request.session["registration"].setdefault("errors", {})
        for key in fields:
            if not request.session["registration"][key]:
                request.session["registration"]["errors"][key] = message
        request.session.modified = True
        return request.session

    def default_session(self, request):
        if "registration" not in request.session:
            request.session["registration"] = {}
        request.session.modified = True
        return request.session


class LoginChoiceView(BaseRegisterView):
    template_name = "registration/login_choice.html"

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
    template_name = "registration/login.html"

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
                return redirect(redirection_url)
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


class RegisterView(BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "registration/register.html"

    @never_cache
    def get(self, request, errors=None, code=None, case_id=None, *args, **kwargs):
        confirm_invited_org = request.session.get("registration", {}).get("confirm_invited_org")
        self.default_session(request)
        template_name = self.template_name
        if (
            "error" not in request.GET and confirm_invited_org is None
        ):  # Only clear the session if this is not a return with 'error' set on the url
            self.reset_session(request)
        initial_context = {
            "countries": countries,
            "country": "GB",
            **request.session.get("registration", {}),
        }
        if code and case_id:
            invite_details = self.trusted_client.get_case_invitation_by_code(code, case_id)
            confirm_invited_org = request.session["registration"].get("confirm_invited_org")
            if confirm_invited_org is None:
                template_name = "registration/invited_organisation.html"
            initial_context.update(
                {
                    "code": code,
                    "case_id": case_id,
                    "confirm_invited_org": confirm_invited_org,
                    "invite": invite_details,
                }
            )
            if confirm_invited_org == "true":
                initial_context.update(
                    {
                        "name": invite_details.get("contact", {}).get("name", ""),
                        "email": invite_details.get("contact", {}).get("email", ""),
                        "phone": invite_details.get("contact", {}).get("phone", ""),
                    }
                )
        self.update_session(request, initial_context)
        return render(request, template_name, request.session["registration"])

    def post(self, request, code=None, case_id=None, *args, **kwargs):
        self.default_session(request)
        redirect_postfix = f"{code}/{case_id}/" if code and case_id else ""
        confirm_invited_org = request.POST.get("confirm_invited_org")
        if confirm_invited_org is not None:
            request.session["registration"]["confirm_invited_org"] = confirm_invited_org
            request.session.modified = True
            # if confirm_invited_org == 'false' and not request.POST.get('organisation_name'):
            return redirect(f"/accounts/register/{code}/{case_id}/")
            # elif confirm_invited_org == 'true':
            #     return redirect(f'/accounts/register/{code}/{case_id}/')
        request.session["registration"].update(request.POST.dict())
        errors = validate(request.session["registration"], registration_validators)
        if request.session["registration"].get("password") != request.session["registration"].get(
            "password_confirm"
        ):
            errors["password_confirm"] = "Passwords do not match"
        if not request.session["registration"].get("email"):
            errors["email"] = "Email is required"
        if not errors:
            session_reg = request.session.get("registration", {})
            if (
                session_reg.get("code")
                and session_reg.get("case_id")
                and session_reg.get("confirm_invited_org") == "true"
            ):
                organisation_id = get(request.session["registration"], "invite/organisation/id")
                organisation = self.trusted_client.get_organisation(organisation_id=organisation_id)
                field_map = {
                    "id": "organisation_id",
                    "name": "organisation_name",
                    "address": "organisation_address",
                }
                out = {}
                company_code = get(organisation, "country/code")
                if company_code:
                    out["uk_company"] = "yes" if company_code == "GB" else "no"
                for field, value in organisation.items():
                    out_field = field_map.get(field) or field
                    out[out_field] = value
                self.update_session(request, out)
                if company_code:
                    return redirect("/accounts/register/3/")
                return redirect("/accounts/register/2/")
            elif (
                session_reg.get("code")
                and session_reg.get("case_id")
                and session_reg.get("confirm_invited_org") == "false"
            ):
                return redirect(f"/accounts/register/2/{redirect_postfix}")
            return redirect("/accounts/register/2/")
        return redirect(f"/accounts/register/{redirect_postfix}?error")


class RegisterOrganisationCountryView(BaseRegisterView):
    template_name = "registration/register_organisation_country.html"
    validators = [
        {"key": "uk_company", "message": "You must make a selection", "re": "(?:yes)|(?:no)"}
    ]

    @never_cache
    def get(self, request, code=None, case_id=None, *args, **kwargs):
        return render(request, self.template_name, request.session["registration"])

    def post(self, request, code=None, case_id=None, *args, **kwargs):
        self.update_session(request, request.POST.dict())
        errors = validate(request.session["registration"], self.validators)
        redirect_postfix = f"{code}/{case_id}/" if code and case_id else ""
        if not errors:
            return redirect(f"/accounts/register/3/{redirect_postfix}")
        else:
            return redirect(f"/accounts/register/2/{redirect_postfix}")


class RegisterOrganisationView(BaseRegisterView):
    template_name = "registration/register_organisation.html"
    validators = [
        {"key": "organisation_name", "message": "Company name is mandatory", "re": ".+"},
        {"key": "organisation_address", "message": "Company address is mandatory", "re": ".+"},
        {"key": "same_contact_address", "message": "You must make a selection", "re": ".+"},
        {"key": "companies_house_id", "message": "Company number is mandatory", "re": ".+"},
    ]

    country_validator = [
        {"key": "organisation_country", "message": "You must select a country", "re": ".+"}
    ]

    @never_cache
    def get(self, request, code=None, case_id=None, errors=None, *args, **kwargs):
        return render(
            request, self.template_name, {"countries": countries, **request.session["registration"]}
        )

    def post(self, request, code=None, case_id=None, *args, **kwargs):
        redirect_postfix = f"{code}/{case_id}/" if code and case_id else ""
        if "registration" not in request.session:
            return redirect(f"/accounts/register/{redirect_postfix}")

        self.update_session(request, request.POST.dict())
        errors = validate(request.session["registration"], self.validators) or {}
        if get(request.session["registration"], "uk_company") == "no":
            errors.update(validate(request.session["registration"], self.country_validator) or {})

        if not errors:
            next_page = (
                "5" if request.session["registration"].get("same_contact_address") == "yes" else "4"
            )
            return redirect(f"/accounts/register/{next_page}/{redirect_postfix}")
        else:
            request.session["registration"]["errors"] = errors
            request.session.modified = True
            return redirect(f"/accounts/register/3/{redirect_postfix}")


class RegisterContactAddressView(BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "registration/register_contact_address.html"

    validators = [{"key": "contact_address", "message": "Contact address is mandatory", "re": ".+"}]

    @never_cache
    def get(self, request, errors=None, code=None, case_id=None, *args, **kwargs):
        return render(
            request, self.template_name, {"countries": countries, **request.session["registration"]}
        )

    def post(self, request, code=None, case_id=None, *args, **kwargs):
        redirect_postfix = f"{code}/{case_id}/" if code and case_id else ""
        if "registration" not in request.session:
            return redirect(f"/accounts/register/{redirect_postfix}")

        self.update_session(request, request.POST.dict())
        errors = validate(request.session["registration"], self.validators)
        if not errors:
            return redirect(f"/accounts/register/5/{redirect_postfix}")
        else:
            request.session["registration"]["errors"] = errors
            request.session.modified = True
            return redirect(f"/accounts/register/4/{redirect_postfix}")


class RegisterIdsView(BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "registration/register_organisation_extras.html"
    required_fields = [
        "name",
        "email",
        "password",
        "uk_company",
        "organisation_name",
        "organisation_country",
        "organisation_address",
    ]

    validators = [
        {
            "key": "duns_number",
            "message": "The duns number should be exactly 9 digits",
            "re": "^(?:\\d{9})?$",
        },
        {
            "key": "organisation_website",
            "message": "Your website should be a complete, valid URL.",
            "re": "^(?:http(s)?:\\/\\/[\\w.-]+(?:\\.[\\w\\.-]+)+[\\w\\-\\._~:/?#[\\]@!\\$&'\\(\\)\\*\\+,;=.]+)?$",  # noqa: E501
        },
    ]

    @never_cache
    def get(self, request, errors=None, code=None, case_id=None, *args, **kwargs):
        return render(
            request, self.template_name, {"countries": countries, **request.session["registration"]}
        )

    def post(self, request, code=None, case_id=None, *args, **kwargs):
        redirect_postfix = f"{code}/{case_id}/" if code and case_id else ""
        if "registration" not in request.session:
            return redirect("/accounts/register/")

        self.update_session(request, request.POST.dict())
        # prepend http to the url if not provided
        _website = request.session["registration"].get("organisation_website")
        if _website and not _website.startswith("http"):
            request.session["registration"]["organisation_website"] = "http://" + _website
            request.session.modified = True
        errors = validate(request.session["registration"], self.validators)
        if not errors:
            if "countries" in request.session["registration"]:
                del request.session["registration"]["countries"]
            if all(
                [bool(request.session["registration"].get(key)) for key in self.required_fields]
            ):
                session_reg = request.session["registration"]
                response = self.trusted_client.register_public(**session_reg)
                if response.get("success"):
                    request.session.modified = True
                    if settings.AUTO_LOGIN:
                        auth_response = self.trusted_client.authenticate(
                            session_reg["email"], session_reg["password"]
                        )
                        if auth_response and auth_response.get("token"):
                            request.session.clear()
                            request.session["token"] = auth_response["token"]
                            request.session["user"] = auth_response["user"]
                            return redirect("/dashboard/?welcome=true")
                    request.session["registration"] = {}
                    return redirect("/email/verify/")
                else:
                    request.session["registration"]["errors"] = response.get("error")
                    request.session.modified = True
        return redirect(f"/accounts/register/5/{redirect_postfix}")


class UpdateUserDetailsView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "registration/update.html"

    def get(self, request, invite_id, *args, **kwargs):
        invite = self.client(request.user).get_invite_details(invite_id)
        context = {
            "invite": invite,
        }
        return render(request, self.template_name, context)


class ForgotPasswordView(TemplateView, TradeRemediesAPIClientMixin):
    def get(self, request, *args, **kwargs):
        return render(
            request, "registration/forgot_password.html", {"requested": "requested" in request.GET}
        )

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email")
        if email:
            response = self.trusted_client.request_password_reset(email)
        return redirect("/accounts/forgotpassword/?requested")


class ResetPasswordView(TemplateView, TradeRemediesAPIClientMixin):
    def get(self, request, code, *args, **kwargs):
        code_valid = self.trusted_client.validate_password_reset(code)
        error_code = request.GET.get("error")
        error_message = ALERT_MAP.get(error_code) if error_code else ""
        if kwargs.get("error"):
            error_message = f"{error_message}<br/>{kwargs['error']}"
        return render(
            request,
            "registration/reset_password.html",
            {
                "invalid_code": not code_valid,
                "code": code,
                "error": error_message,
            },
        )

    def post(self, request, code, *args, **kwargs):
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")
        if password and password_confirm and password == password_confirm:
            try:
                response = self.trusted_client.reset_password(code, password)
            except Exception as exc:
                return self.get(request, code, error=str(exc), *args, **kwargs)
        elif password != password_confirm:
            return redirect(f"/accounts/password/reset/{code}/?error=pass_conf")
        return redirect("/accounts/login/choice/?next=/dashboard/")


class TermsAndConditionsView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, "registration/terms_and_conditions.html", {})


class CookiePolicyView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, "registration/cookie_policy.html", {})


class CookieSettingsView(BaseRegisterView):
    def get(self, request, *args, **kwargs):
        redirect_url = request.GET.get("url") or ""
        cookie_policy = {"accept_gi": "off"}
        try:
            cookie_policy = json.loads(request.COOKIES.get("cookie_policy"))
        except Exception as exception:
            print("Bad one", exception)
        return render(
            request,
            "registration/cookies.html",
            {
                "cookie_policy": cookie_policy,
                "redirect_url": redirect_url,
            },
        )

    def post(self, request, *args, **kwargs):
        accept_gi = request.POST.get("accept_gi")
        redirect_url = request.POST.get("redirect_url") or "/dashboard/"
        separator = "?" if redirect_url.find("?") == -1 else "#"
        redirect_url = f"{redirect_url}{separator}cookie-policy-updated=1"
        response = redirect(redirect_url)
        policy = json.dumps({"accept_gi": accept_gi})

        if accept_gi != "on":
            # delete ga cookies by regex
            regex = r"^_g(a|i)"
            for key, value in request.COOKIES.items():
                if re.search(regex, key):
                    response.delete_cookie(key)
        set_cookie(response, "cookie_policy", policy)
        return response


class AccessibilityStatementView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, "registration/accessibility_statement.html", {})


class RegistrationCompletionView(BaseRegisterView, TradeRemediesAPIClientMixin):
    """
    Complete a registration triggered by a user creation and invite
    """

    def get(self, request, code, org_id, user_id=None, *args, **kwargs):
        template_name = "registration/registration_completion.html"
        context = {
            "errors": kwargs.get("errors", {}),
            "countries": countries,
        }
        try:
            invite_validation = self.trusted_client.validate_user_invitation(code, org_id)
            context.update(invite_validation)
        except Exception:
            context["errors"]["invalid_invite"] = "Invalid invitation details"
        return render(request, template_name, context)

    def post(self, request, code, org_id, user_id=None, *args, **kwargs):
        errors = {}
        invite_validation = {}
        try:
            invite_validation = self.trusted_client.validate_user_invitation(code, org_id)
        except Exception as exc:
            errors["invalid_invite"] = "Invalid invitation details"
        invite = invite_validation["invite"]
        params = {
            "password": request.POST.get("password"),
            "password_confirm": request.POST.get("password_confirm"),
            "email": invite["meta"]["email"],
            "country_code": request.POST.get("country"),
            "phone": request.POST.get("phone"),
            "name": request.POST.get("name"),
            "terms": request.POST.get("terms"),
        }
        if errors:
            return self.get(request, code, org_id, errors=errors)
        response = None
        try:
            invited_by = TransientUser(token=invite["invited_by"])
            client = self.client(invited_by)
            response = client.complete_user_registration(invite["id"], org_id, params=params)
        except Exception as exc:  # TODO: Refactor this exc handling.
            if hasattr(exc, "detail") and exc.detail and isinstance(exc.detail, dict):
                errors = exc.detail["errors"]
            return self.get(request, code, org_id, errors=errors)
        return redirect("/email/verify/")
