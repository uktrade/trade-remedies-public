# Views to handle the registration functionality and legal pages
import json

from config.constants import SECURITY_GROUP_THIRD_PARTY_USER
from login.decorators import v2_error_handling
from core.models import TransientUser
from core.utils import get, validate
from core.validators import (
    registration_validators,
)
from django.conf import settings
from django.http import QueryDict
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic import FormView, TemplateView
from django_countries import countries
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin

from registration.forms import (
    NonUkEmployerForm,
    OrganisationFurtherDetailsForm,
    PasswordForm,
    RegistrationStartForm,
    TwoFactorChoiceForm,
    UkEmployerForm,
    YourEmployerForm,
)


class BaseRegisterView(TemplateView):
    def dispatch(self, *args, **kwargs):
        self.default_session(self.request)
        return super().dispatch(*args, **kwargs)

    def reset_session(self, request, initial_data=None):
        initial_data = initial_data or {}
        request.session["registration"] = initial_data
        request.session.modified = True
        return request.session

    def update_session(self, request, update_data):
        request.session.setdefault("registration", {})
        if isinstance(update_data, QueryDict):
            # If it's a QueryDict, we need to convert it to a normal dictionary as Django's
            # internal representation of QueryDicts store individual values as lists, regardless
            # of how many elements are in that list:
            # https://www.ianlewis.org/en/querydict-and-update
            update_data = update_data.dict()
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


class RegisterView(BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "registration/register.html"

    @never_cache
    def get(self, request, errors=None, code=None, case_id=None, *args, **kwargs):
        self.default_session(request)
        confirm_invited_org = request.session["registration"].get("confirm_invited_org")
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
            initial_context.update(
                {
                    "code": code,
                    "case_id": case_id,
                    "confirm_invited_org": confirm_invited_org,
                    "invite": invite_details,
                }
            )
            if confirm_invited_org:
                initial_context.update(
                    {
                        "name": invite_details.get("contact", {}).get("name", ""),
                        "email": invite_details.get("contact", {}).get("email", ""),
                        "phone": invite_details.get("contact", {}).get("phone", ""),
                    }
                )
        self.update_session(request, initial_context)
        return render(request, template_name, request.session["registration"])

    def post(self, request, code=None, case_id=None, *args, **kwargs):  # noqa: C901
        self.default_session(request)
        redirect_postfix = f"{code}/{case_id}/" if code and case_id else ""

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
                    and session_reg.get("confirm_invited_org") is True
            ):
                invitee_sec_group = get(
                    request.session["registration"], "invite/organisation_security_group"
                )
                if invitee_sec_group == SECURITY_GROUP_THIRD_PARTY_USER:
                    # Use the third party invitee's organisation
                    organisation_id = get(
                        request.session["registration"], "invite/contact/organisation/id"
                    )
                else:
                    organisation_id = get(request.session["registration"], "invite/organisation/id")
                organisation = self.trusted_client.get_organisation(organisation_id=organisation_id)
                field_map = {
                    "id": "organisation_id",
                    "name": "organisation_name",
                    "address": "organisation_address",
                }
                out = {}
                organisation_country_code = get(organisation, "country/code")
                if organisation_country_code:
                    out["organisation_country_code"] = organisation_country_code
                    out["uk_company"] = "yes" if organisation_country_code == "GB" else "no"
                for field, value in organisation.items():
                    out_field = field_map.get(field) or field
                    out[out_field] = value
                self.update_session(request, out)
                if organisation_country_code:
                    return redirect("/accounts/register/3/")
                return redirect("/accounts/register/2/")
            elif (
                    session_reg.get("code")
                    and session_reg.get("case_id")
                    and not session_reg.get("confirm_invited_org")
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
        request.session["registration"].pop("errors", None)  # Clear existing
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
            "re": "^(?:http(s)?:\\/\\/[\\w.-]+(?:\\.[\\w\\.-]+)"
                  "+[\\w\\-\\._~:/?#[\\]@!\\$&'\\(\\)\\*\\+,;=.]+)?$",
            # noqa: E501
        },
    ]

    @never_cache
    def get(self, request, errors=None, code=None, case_id=None, *args, **kwargs):
        return render(
            request, self.template_name, {"countries": countries, **request.session["registration"]}
        )

    def post(self, request, code=None, case_id=None, *args, **kwargs):  # noqa: C901
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
                        if auth_response:
                            if auth_response.get("needs_verify"):
                                request.session["registration"] = {}
                                return redirect("/email/verify/")
                            elif auth_response.get("token"):
                                request.session.clear()
                                request.session["token"] = auth_response["token"]
                                request.session["user"] = auth_response["user"]
                                return redirect("/dashboard/?welcome=true")
                else:
                    request.session["registration"]["errors"] = response.get("error")
                    request.session.modified = True
        return redirect(f"/accounts/register/5/{redirect_postfix}")


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


class UpdateUserDetailsView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "registration/update.html"

    def get(self, request, invite_id, *args, **kwargs):
        invite = self.client(request.user).get_invite_details(invite_id)
        context = {
            "invite": invite,
        }
        return render(request, self.template_name, context)


class TermsAndConditionsView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, "registration/terms_and_conditions.html", {})


class AccessibilityStatementView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, "registration/accessibility_statement.html", {})


# ------------------------------------------V2 REGISTRATION JOURNEY--------------------------------#
class V2BaseRegisterView(FormView):
    next_url_resolver = ""

    def dispatch(self, *args, **kwargs):
        if "registration" not in self.request.session:
            self.request.session["registration"] = {}
        self.request.session.modified = True
        return super().dispatch(*args, **kwargs)

    def reset_session(self, request, initial_data=None):
        initial_data = initial_data or {}
        request.session["registration"] = initial_data
        request.session.modified = True
        return request.session

    def update_session(self, request, update_data):
        request.session.setdefault("registration", {})
        if isinstance(update_data, QueryDict):
            # If it's a QueryDict, we need to convert it to a normal dictionary as Django's
            # internal representation of QueryDicts store individual values as lists, regardless
            # of how many elements are in that list
            # https://www.ianlewis.org/en/querydict-and-update
            update_data = update_data.dict()
        request.session["registration"].update(update_data)
        request.session.modified = True
        return request.session

    def form_invalid(self, form):
        form.assign_errors_to_request(self.request)
        return super().form_invalid(form)

    def form_valid(self, form):
        self.update_session(self.request, form.cleaned_data)
        return redirect(self.get_next_url(form))

    def get_next_url(self, form=None):
        return reverse(self.next_url_resolver)


class V2RegistrationViewStart(V2BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "v2/registration/registration_start.html"
    form_class = RegistrationStartForm
    next_url_resolver = "v2_register_set_password"

    def get(self, request, *args, **kwargs):
        self.reset_session(request)
        return super().get(request, *args, **kwargs)


class V2RegistrationViewSetPassword(V2BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "v2/registration/registration_set_password.html"
    form_class = PasswordForm
    next_url_resolver = "v2_register_2fa_choice"


class V2RegistrationView2FAChoice(V2BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "v2/registration/registration_2fa_choice.html"
    form_class = TwoFactorChoiceForm
    next_url_resolver = "v2_register_your_employer"


class V2RegistrationViewYourEmployer(V2BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "v2/registration/registration_your_employer.html"
    form_class = YourEmployerForm

    def get_next_url(self, form=None):
        if form.cleaned_data["uk_employer"] == "yes":
            return reverse("v2_register_your_uk_employer")
        else:
            return reverse("v2_register_your_non_uk_employer")


class V2RegistrationViewUkEmployer(V2BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "v2/registration/registration_your_uk_employer.html"
    form_class = UkEmployerForm
    next_url_resolver = "v2_register_organisation_further_details"


class V2RegistrationViewNonUkEmployer(V2BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "v2/registration/registration_your_non_uk_employer.html"
    next_url_resolver = "v2_register_organisation_further_details"
    form_class = NonUkEmployerForm


class V2RegistrationViewOrganisationFurtherDetails(V2BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "v2/registration/registration_organisation_further_details.html"
    form_class = OrganisationFurtherDetailsForm

    @v2_error_handling()
    def form_valid(self, form):
        # we're done, let's create the new user
        self.update_session(self.request, form.cleaned_data)
        registration_data = {"registration_data": json.dumps(self.request.session["registration"])}
        response = self.trusted_client.v2_register(registration_data)
        self.update_session(self.request, response)
        self.request.session["account_created"] = True
        return redirect(reverse("request_email_verify_code", kwargs={"user_pk": response["pk"]}))


class RequestEmailVerifyCode(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "v2/registration/email_verification.html"

    def get(self, request, *args, **kwargs):
        # Sometimes we just want to show the user the page to resend their code and not send it yet.
        if not request.GET.get("dont_send"):
            response = self.trusted_client.send_email_verification_link(kwargs["user_pk"])
            request.session["email_verification_link_resent"] = True
            request.session["email"] = response["email"] if response else None
        return super().get(request, *args, **kwargs)


class VerifyEmailVerifyCode(View, TradeRemediesAPIClientMixin):
    @v2_error_handling(redirection_url_resolver="landing")
    def get(self, request, user_pk, email_verify_code, *args, **kwargs):
        response = self.trusted_client.verify_email_verification_link(user_pk, email_verify_code)
        # Getting the organisation security groups of this user, so we know what permissions we
        # tell them they have
        owner = False
        if "organisations" in response and response["organisations"]:
            if response["organisations"][0]["security_group"] == "Organisation Owner":
                owner = True
        if request.user.is_authenticated:
            request.user.reload(request)  # Getting the new email_verified_at fields from the API
        return render(
            request, "v2/registration/registration_email_verified.html", context={"owner": owner}
        )
