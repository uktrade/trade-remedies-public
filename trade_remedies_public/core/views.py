import json
import logging
import os

import pytz
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import TemplateView, View
from django_countries import countries
from requests.exceptions import HTTPError
from trade_remedies_client.exceptions import APIException
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
from v2_api_client.client import TRSAPIClient

from cases.constants import CASE_TYPE_REPAYMENT
from cases.utils import decorate_due_status, decorate_rois
from config.constants import (
    SECURITY_GROUP_ORGANISATION_OWNER,
    SECURITY_GROUP_ORGANISATION_USER,
    SECURITY_GROUP_THIRD_PARTY_USER,
)
from core.base import BasePublicView, GroupRequiredMixin
from core.constants import ALERT_MAP
from core.utils import (
    deep_index_items_by,
    get,
    proxy_stream_file_download,
    split_public_documents,
    to_word,
    validate,
)
from core.validators import user_create_validators
from registration.views.views import BaseRegisterView

health_check_token = os.environ.get("HEALTH_CHECK_TOKEN")

logger = logging.getLogger(__name__)


class TradeRemediesBaseView(TemplateView):
    """
    Base view for Trade Remedies generic template views
    """

    def check_required_keys(self, request):
        errors = {}
        if hasattr(self, "required_keys") and self.required_keys:
            for key in self.required_keys:
                if not request.POST.get(key):
                    errors[key] = f"{to_word(key)} is required"
        return errors


class HealthCheckView(View, TradeRemediesAPIClientMixin):
    def get(self, request):
        response = self.trusted_client.health_check()
        if all([response[k] == "OK" for k in response]):
            return HttpResponse("OK")
        else:
            return HttpResponse(f"ERROR: {response}")


class HomeView(TemplateView):
    def get(self, request, *args, **kwargs):
        return redirect("/dashboard/")


class HoldingView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "holding_page.html"
    holding_page_controller = None

    def get(self, request, *args, **kwargs):
        message = self.trusted_client.get_system_boolean("HOLDING_PAGE_TEXT", "")
        return render(request, self.template_name, {"message": message})


class StartView(TemplateView):
    template_name = "home.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {})


class TwoFactorView(TemplateView, LoginRequiredMixin, TradeRemediesAPIClientMixin):
    template_name = "registration/two_factor.html"

    def get(self, request, *args, **kwargs):
        if isinstance(request.user, AnonymousUser):
            return redirect("/accounts/login/")
        twofactor_error = None
        locked_until = None
        locked_for_seconds = None
        resend = request.GET.get("resend")
        delivery_type = request.GET.get("delivery_type")
        email_verified = request.session.get("email_verified")
        if email_verified:
            request.session["email_verified"] = None
            request.session.modified = True
        should_two_factor = request.user.should_two_factor or request.session.get("force_2fa")
        if hasattr(request.user, "token") and should_two_factor:
            if request.session.get("twofactor_error"):
                twofactor_error = request.session["twofactor_error"]
                del request.session["twofactor_error"]
                request.session.modified = True
            if delivery_type != "email" and not request.user.phone:
                delivery_type = "email"
            result = None
            if resend or twofactor_error:
                try:
                    result = self.client(request.user).two_factor_request(
                        delivery_type=delivery_type,
                        user_agent=request.META["HTTP_USER_AGENT"],
                        ip_address=request.META["REMOTE_ADDR"],
                    )
                    if result.get("error"):
                        twofactor_error = result["error"]
                        locked_until = result.get("locked_until")
                        locked_for_seconds = result.get("locked_for_seconds")
                except Exception:
                    twofactor_error = (
                        f"We could not send the code to your phone ({request.user.phone}). "
                        f"Please select to use email delivery of the access code."
                    )
                    result = "An error occurred"
            return render(
                request,
                self.template_name,
                {
                    "locked_until": locked_until,
                    "locked_for_seconds": locked_for_seconds,
                    "two_factor_request": result,
                    "twofactor_error": twofactor_error,
                    "delivery_type": delivery_type,
                    "email_verified": email_verified,
                },
            )
        else:
            return redirect("/dashboard")

    def post(self, request, *args, **kwargs):
        code = request.POST.get("code")
        if not hasattr(request.user, "token"):
            return redirect("/accounts/login/?expired=1")
        try:
            result = self.client(request.user).two_factor_auth(
                code=code,
                user_agent=request.META["HTTP_USER_AGENT"],
                ip_address=request.META["REMOTE_ADDR"],
            )
            request.session["user"] = result
            if "force_2fa" in request.session:
                del request.session["force_2fa"]

            request.session.modified = True
            return redirect("/dashboard")
        except APIException as exc:
            request.session["twofactor_error"] = f"{exc}"
            request.session.modified = True
            return redirect("/dashboard")


@method_decorator(cache_page(settings.PUBLIC_FILE_CACHE_MINUTES * 60), name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class PublicCaseListView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "cases/public_cases.html"
    archive = False

    def get(self, request, *args, **kwargs):
        fetch_mode = "archived" if self.archive else "all"
        cases = self.trusted_client.get_all_cases(
            param=fetch_mode, exclude_types=[CASE_TYPE_REPAYMENT]
        )
        cases.sort(key=lambda ca: ca.get("initiated_at") or "", reverse=True)
        fields = ["COMMODITY_NAME", "COUNTRY", "LAST_PUBLICATION"]
        case_ids = []
        for case in cases:
            case_ids.append(case.get("id"))
        states = self.trusted_client.get_case_state(fields=fields, case_ids=case_ids)
        for case in cases:
            state = states.get(case.get("id"))
            if state:
                case["state"] = state
        notices = self.trusted_client.get_latest_notices(limit=5) if not self.archive else None

        archived_count = self.trusted_client.get_case_counts(
            params={"archived": True, "initiated": True}
        )

        template_name = "cases/public_archive.html" if self.archive else self.template_name
        return render(
            request,
            template_name,
            {
                "cases": cases,
                "notices": notices,
                "show_archive_link": archived_count > 0,
            },
        )


@method_decorator(cache_page(settings.PUBLIC_FILE_CACHE_MINUTES * 60), name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class PublicCaseView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "cases/public_case.html"

    def get(self, request, case_number, submission_id=None, *args, **kwargs):
        case = self.trusted_client.get_public_case_record(case_number)
        if case:
            case_submissions = self.trusted_client.get_submissions_public(
                case_id=case.get("id"), private=False, get_global=True
            )
            case_submissions = [
                submission for submission in case_submissions if submission.get("issued_at")
            ]
            case["submissions"] = sorted(
                case_submissions, key=lambda su: su.get("issued_at") or "", reverse=True
            )
            # Get a specific set of states for rendering
            fields = [
                "PRODUCT_DESCRIPTION",
                "TARIFF_CLASSIFICATION",
                "REGISTRATION_OF_INTEREST_TIMER",
            ]
            case_state = self.trusted_client.get_case_state(
                case_ids=[case.get("id")], fields=fields
            ).get(case.get("id"))
            return render(request, self.template_name, {"case": case, "state": case_state})
        return redirect(reverse("public_cases"))


@method_decorator(cache_page(settings.PUBLIC_FILE_CACHE_MINUTES * 60), name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class PublicSubmissionView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "cases/submissions/public_view.html"

    @staticmethod
    def get_sort_key_from_document(document):
        return document.get("name", "")

    def get(self, request, case_number, submission_id, *args, **kwargs):
        case = self.trusted_client.get_public_case_record(case_number)
        submission = self.trusted_client.get_submission_public(
            case.get("id"), submission_id, private=False
        )

        template_docs, public_docs = split_public_documents(submission["documents"])

        public_docs.sort(key=self.get_sort_key_from_document)
        template_docs.sort(key=self.get_sort_key_from_document)

        return render(
            request,
            self.template_name,
            {
                "case": case,
                "submission": submission,
                "documents": {"non_confidential": public_docs, "template": template_docs},
            },
        )


@method_decorator(cache_page(settings.PUBLIC_FILE_CACHE_MINUTES * 60), name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class PublicDownloadView(TemplateView, TradeRemediesAPIClientMixin):
    template_name = ""

    def get(self, request, case_number, submission_id, document_id, *args, **kwargs):
        case = self.trusted_client.get_public_case_record(case_number)
        # submission = self.trusted_client.get_submission_public(case.get('id'),
        # submission_id, private=False)
        document = self.trusted_client.get_document(document_id, case.get("id"), submission_id)
        document_stream = self.trusted_client.get_document_download_stream(
            document_id=document_id,
            submission_id=submission_id,
        )
        return proxy_stream_file_download(document_stream, document["name"])


class InvitationView(BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "invite_home.html"

    def get(self, request, code=None, case_id=None, *args, **kwargs):
        self.default_session(request)
        try:
            invitation = self.trusted_client.get_trusted_invitation_details(case_id, code)
        except HTTPError as exc:
            # an invalid or delete invite
            return redirect(reverse("login"))
        new_session_data = {"code": code, "case_id": case_id, "invite": invitation}
        if request.session.get("token"):
            # The user is logged in already
            pass
        self.update_session(request, new_session_data)
        return render(request, self.template_name, context=new_session_data)


class InvitationConfirmOrganisation(BaseRegisterView, TradeRemediesAPIClientMixin):
    template_name = "registration/invited_organisation.html"

    def get(self, request, code=None, case_id=None, *args, **kwargs):
        if not self.request.session.get("registration", {}).get("invite"):
            # Redirect to the original invitation screen
            return redirect(reverse("start", kwargs={"code": code, "case_id": case_id}))
        return super().get(request, code=code, case_id=case_id, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invite"] = self.request.session["registration"]["invite"]
        context["confirm_invited_org"] = self.request.session["registration"].get(
            "confirm_invited_org", None
        )
        return context

    def post(self, request, code, case_id, *args, **kwargs):
        if request.POST.get("confirm_invited_org", None) == "true":
            # The user have verified they are the user the invitation is meant for
            self.update_session(request, {"confirm_invited_org": True})
        else:
            self.update_session(request, {"confirm_invited_org": False})

        # Now we check if the invitation belongs to a user who is already registered
        invitation = request.session["registration"]["invite"]
        invited_user_email = invitation["email"]
        try:
            user = self.trusted_client.get_user_by_email(user_email=invited_user_email)
            # The user is already registered on the TRS, we want to make them log in,
            # so we can add them to this case
            self.update_session(request, {"user_already_exists": True, "registering_user": user})
            return redirect(reverse("login_invite", kwargs={"code": code, "case_id": case_id}))
        except APIException as e:
            if e.status_code == 404:
                # The user was not found, continue with the invitation as normal
                return redirect(
                    reverse("register_invite", kwargs={"code": code, "case_id": case_id})
                )
            raise e


class DashboardView(
    LoginRequiredMixin, GroupRequiredMixin, TemplateView, TradeRemediesAPIClientMixin
):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "dashboard.html"

    @never_cache
    def get(self, request, *args, **kwargs):
        request.session["organisation_id"] = None
        request.session["_case"] = None
        request.session.modified = True
        client = self.client(request.user)
        # Return all cases for all of the user's organisations
        cases = client.get_user_cases()
        # aggregate the statuses across organisations
        for case in cases:
            due = None
            submission_count = 0
            for org in case.get("user_organisations"):
                state = org.get("org_state")
                submission_count += state["submission_count"]
                this_due = state.get("due_at")
                if this_due:
                    state.update(decorate_due_status(this_due))
                    if due is None or due > this_due:
                        due = this_due

            case["due_state"] = {"submission_count": submission_count}
            case["due_state"].update(decorate_due_status(due))
            # set an 'is draft' flag based on whether case is past sufficient to proceed.
            stage = (case.get("stage") or {}).get("key", "NO_STAGE")
            case["is_draft"] = stage in [
                "NO_STAGE",
                "CASE_CREATED",
                "INSUFFICIENT_TO_PROCEED",
                "DRAFT_RECEIVED",
                "DRAFT_REVIEW",
            ]

        # and any registration of interest
        all_interests = client.get_registration_of_interest()
        interests_idx = deep_index_items_by(all_interests, "status/draft")
        interest_cases_draft = decorate_rois(interests_idx.get("true"), date_warnings=True)
        interest_cases = decorate_rois(interests_idx.get("false"))

        # get any 3rd party invites
        organisation = request.user.organisation
        invite_submissions = []
        if organisation:
            invite_submissions = client.get_organisation_invite_submissions(organisation["id"])

        # Let's get the cases where the user is awaiting approval
        v2_client = TRSAPIClient(token=request.user.token)
        invitations = v2_client.invitations(
            contact_id=request.user.contact["id"],
            fields=["submission", "case", "invitation_type", "rejected_at", "approved_at"],
        )
        unapproved_rep_invitations_cases = [
            invite.case
            for invite in invitations
            if invite.invitation_type == 2
            if invite.submission and not invite.rejected_at and not invite.approved_at
        ]
        return render(
            request,
            self.template_name,
            {
                "all_organisations": True,
                "cases": [case for case in cases if not case.get("is_draft")],
                "applications": [case for case in cases if case.get("is_draft")],
                "interest_cases_draft": interest_cases_draft,
                "interest_cases": interest_cases,
                "case_count": len(cases),
                "invite_submissions": invite_submissions,
                "alert_message": ALERT_MAP.get(self.request.GET.get("alert")),
                "error_message": ALERT_MAP.get(self.request.GET.get("error")),
                "pre_invitations": client.get_system_boolean("PRE_RELEASE_INVITATIONS"),
                "pre_manage_team": client.get_system_boolean("PRE_MANAGE_TEAM"),
                "pre_applications": client.get_system_boolean("PRE_APPLICATIONS"),
                "pre_register_interest": client.get_system_boolean("PRE_REGISTER_INTEREST"),
                "is_org_owner": SECURITY_GROUP_ORGANISATION_OWNER
                in request.user.organisation_groups,
                "unapproved_rep_invitations_cases": unapproved_rep_invitations_cases,
            },
        )


class SetOrganisationView(LoginRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):
    template_name = "cases/select_org.html"

    def get(self, request, case_id):
        redirect_to = request.GET.get("next")
        organisations = self.client(request.user).get_user_case_organisations(case_id)
        return render(
            request,
            self.template_name,
            {
                "organisations": organisations,
                "next": redirect_to,
            },
        )

    def post(self, request, organisation_id=None, *args, **kwargs):
        organisation_id = organisation_id or request.POST.get("organisation_id")
        redirect_to = request.POST.get("next")
        request.session["organisation_id"] = str(organisation_id) if organisation_id else ""
        request.session.modified = True
        return redirect(redirect_to)


class StubView(TemplateView):
    def get(self, request):
        return render(request, "stub.html")


class TeamView(LoginRequiredMixin, GroupRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER]
    template_name = "account/team.html"

    def get(self, request, *args, **kwargs):
        users = []
        pending_assignments = []
        pending_invites = []
        pending_third_party_invites = []
        request.session["create-user"] = {}
        request.session.modified = True
        client = self.client(request.user)
        organisation = request.user.contact["organisation"]
        if SECURITY_GROUP_ORGANISATION_OWNER in request.user.groups:
            pending_assignments = client.get_pending_user_case_assignments(organisation["id"])
            users = client.get_team_users()
            _user_emails = [user["email"] for user in users]
            _invites = client.get_user_invitations()
            pending_invites = [
                invite
                for invite in _invites
                if invite["email"] not in _user_emails and invite["meta"]
            ]

            # Get any 3rd party invites
            if organisation:
                pending_submissions = client.get_organisation_invite_submissions(organisation["id"])
                for submission in pending_submissions:
                    case_id = submission["case"]["id"]
                    submission_id = submission["id"]
                    submission_invites = client.get_third_party_invites(
                        case_id=case_id, submission_id=submission_id
                    )
                    for submission_invite in submission_invites:
                        submission_invite["locked"] = (
                            submission.get("locked", True)
                            or submission.get("deficiency_sent_at") is not None
                        )
                        pending_third_party_invites.append(submission_invite)

        return render(
            request,
            self.template_name,
            {
                "all_organisations": True,
                "users": users,
                "pending_assignments": pending_assignments,
                "invites": pending_invites,
                "third_party_invites": pending_third_party_invites,
                "alert_message": ALERT_MAP.get(request.GET.get("alert")),
            },
        )


class UserInviteView(TemplateView, TradeRemediesAPIClientMixin):
    def get(self, request, invitation_id, *args, **kwargs):
        invite = self.client(request.user).get_invite_details(invitation_id)
        case_spec = invite.get("meta", {}).get("case_spec", [])
        case_spec_index = deep_index_items_by(case_spec, "id")
        request.session["create-user"] = {
            "invitation": invite,
            "user": {
                **invite.get("meta", {}),
                "email": invite["email"],
                "case_index": case_spec_index,
            },
        }
        request.session.modified = True
        return redirect(
            f"/accounts/team/{invite['organisation']['id']}/invite/{invite['id']}/edit/"
        )


class TeamUserView(LoginRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):
    template_name = "account/user.html"
    self_details = False

    def init_data(self, invitation=None, user=None, case_spec=None):
        invitation = invitation or {}
        user = user or {}
        case_spec = case_spec or invitation.get("meta", {}).get("case_spec", []) or []
        if isinstance(case_spec, str):
            case_spec = json.loads(case_spec)
        case_spec_index = {case["case"]: case["primary"] for case in case_spec}
        return {
            "user": {
                "email": invitation.get("email", ""),
                "case_index": case_spec_index,
                **invitation.get("meta", {}),
                **user,
            },
            "invitation": invitation,
        }

    def get(  # noqa: C901
        self,
        request,
        user_id=None,
        organisation_id=None,
        section=None,
        invitation_id=None,
        *args,
        **kwargs,
    ):
        invitation_id = invitation_id or request.GET.get("invitation_id")
        organisation_id = organisation_id or request.user.organisation.get("id")
        _session_data = request.session.get("create-user", {})
        user = _session_data.get("user", {"active": True})
        invite = _session_data.get("invitation", {})
        case_spec = _session_data.get("user", {}).get("case_spec", [])
        client = self.client(request.user)
        if self.self_details:
            base_url = "/accounts/info/user/"
            user_id = request.user.id
            section = "contact"
        else:
            base_url = f"/accounts/team/{organisation_id}/user/"
        if user_id:
            user = client.get_user(user_id=user_id, organisation_id=organisation_id)
            user_cases = client.get_user_cases(request_for=user_id)
            user["case_ids"] = [case["id"] for case in user_cases]
            user["case_index"] = {case["id"]: case["primary"] for case in user_cases}
            request.session["create-user"] = {"user": user}
            code = user.get("country_code")
            if code:
                user["country"] = {"code": code, "name": countries.countries[code]}
        elif invitation_id:
            invite = client.get_invite_details(invitation_id)
            case_spec = invite.get("meta", {}).get("case_spec", [])
            user = self.init_data(invite).get("user")
        have_draft_user = user.get("email")
        if section == "create" or not have_draft_user:
            request.session["create-user"] = self.init_data(invite, user, case_spec)
            if section != "edit":
                section = "contact"
        if not user.get("group"):
            user["group"] = user.get("groups", ["unset"])[0]
        organisation = client.get_organisation(request.user.organisation["id"])
        if not user.get("address"):
            user["address"] = organisation.get("address", "")
        if kwargs.get("errors") and kwargs.get("data"):
            user.update(kwargs["data"])
        create_mode = user.get("case_ids") is None
        create_mode = create_mode and not request.GET.get("edit")

        filter_user_id = str(user.get("id"))
        user_org_cases = list(
            filter(
                lambda uc: str(get(uc, "user/id")) == filter_user_id,
                client.get_user_cases(outer=True),
            )
        )

        # Get outstanding assignments and splice onto the case list
        pending_assignments = client.get_pending_user_case_assignments(
            request.user.organisation["id"], user_id=user.get("id")
        )
        for pending_assignment in pending_assignments:
            if get(pending_assignment, "contact/user/id") == filter_user_id:
                user_org_cases.append(
                    {
                        "user": get(pending_assignment, "contact/user"),
                        "case": get(pending_assignment, "case"),
                        "representing": get(pending_assignment, "organisation"),
                        "role": get(pending_assignment, "organisation_case_role"),
                        "submission": pending_assignment,
                    }
                )

        cases_dict = {}
        for user_org_case in user_org_cases:
            case_id = get(user_org_case, "case/id")
            cases_dict.setdefault(
                case_id, {"case": get(user_org_case, "case"), "organisations": []}
            )
            cases_dict[case_id].get("organisations").append(user_org_case.get("representing"))
        cases = list(cases_dict.values())
        cases.sort(key=lambda ca: ca.get("reference") or "")
        if section in ["contact", "permissions", "cases", "status"]:
            self.template_name = f"account/user-edit-{section}.html"
        return render(
            request,
            self.template_name,
            {
                "base_url": base_url,
                "self_details": self.self_details,
                "all_organisations": True,
                "is_owner": request.user.has_group("Organisation Owner"),
                "self": user.get("id") == request.user.id,
                "existing_user_id": user.get("id"),
                "organisation_id": organisation_id,
                "user_record": user,
                "invitation_id": invitation_id,
                "countries": countries,
                "groups": client.get_public_security_groups(),
                "timezones": pytz.common_timezones,
                "user_cases": user_org_cases,
                "cases": cases,
                "create_mode": create_mode,
                "page_title": "Invite colleague" if not user.get("id") else user.get("name"),
                "section": section,
                "alert_message": "Colleague invited"
                if request.GET.get("alert") == "added-employee"
                else None,
                "errors": kwargs.get("errors"),
            },
        )

    def post(  # noqa: C901
        self,
        request,
        user_id=None,
        organisation_id=None,
        section=None,
        invitation_id=None,
        *args,
        **kwargs,
    ):
        if not section:
            section = request.POST.get("section")
        user_group = request.POST.get("group")
        create_mode = request.POST.get("create_mode")
        if user_group == SECURITY_GROUP_THIRD_PARTY_USER and create_mode:
            return redirect("/case/invite")

        client = self.client(request.user)
        if section == "delete":
            delete_response = client.delete_pending_invite(invitation_id, organisation_id)
            return redirect("/accounts/team/?alert=invite-deleted")

        if self.self_details and not user_id:
            user_id = request.user.id
        elif request.session.get("create-user", {}).get("user", {}).get("id") and not user_id:
            user_id = request.session["create-user"]["user"]["id"]
        organisation_id = organisation_id or request.user.organisations[0]["id"]
        redirect_url = (
            request.POST.get("redirect") or f"/accounts/team/{organisation_id}/user/{user_id}/"
            if user_id
            else f"/accounts/team/{organisation_id}/user/"
        )
        data = {
            "organisation_id": organisation_id,
            "group": user_group,
        }
        data.update(request.POST.dict())
        if data.get("active"):
            data["active"] = data["active"] == "yes"
        if request.POST.get("section") == "contact":
            _validator = user_create_validators
            if not self.self_details and not user_id:
                user_create_validators.extend(
                    [
                        {"key": "group", "message": "You must select a security group", "re": ".+"},
                    ]
                )
                _validator = user_create_validators
            errors = validate(data, _validator)
            if errors:
                return self.get(
                    request,
                    user_id=user_id,
                    organisation_id=organisation_id,
                    section=request.POST.get("section"),
                    errors=errors,
                    data=data,
                )

        # Check that the confirm box is checked
        if request.POST.get("review") == "required":
            return self.get(
                request,
                user_id=user_id,
                organisation_id=organisation_id,
                section=request.POST.get("section"),
                errors={"review": "You must check the confirmation box"},
                data=data,
            )

        case_ids = request.POST.getlist("case_id")
        all_cases = request.POST.getlist("all_cases") or []
        if all_cases:

            case_spec = []
            for case_id in case_ids:
                primary = request.POST.get(case_id + "_is_primary")
                case_spec.append({"case": case_id, "primary": primary == "on"})
            data["case_spec"] = json.dumps(case_spec)
            data["case_index"] = {case["case"]: case["primary"] for case in case_spec}
            data["unassign_case_id"] = [cid for cid in all_cases if cid not in case_ids]
        if not user_id:
            # In create mode, stash in the session
            user = request.session.get("create-user") or {"user": {}, "invitation": {}}
            if not request.POST.get("btn-value") == "create":
                user["user"].update(data)
                code = user["user"].get("selected_country_code", user.get("country_code"))
                user["user"]["country"] = {"code": code, "name": countries.countries[code]}
                request.session["create-user"] = user
                request.session.modified = True
                # if we are in the forward create path,
                redirect_url = f"/accounts/team/{organisation_id}/user/"
                return redirect(request.POST.get("redirect") or redirect_url)
            else:
                # Create json payload for case spec
                if user["user"].get("case_spec"):
                    user["user"]["case_spec"] = json.dumps(user["user"]["case_spec"])
                try:
                    response = client.create_and_invite_user(
                        organisation_id=organisation_id,
                        data=user["user"],
                        invitation_id=request.session.get("invitation", {}).get("id"),
                    )
                except APIException as e:
                    logger.warning(f"Problem calling API to invite user: {e}")
                    return self.get(
                        request, user_id=user_id, organisation_id=organisation_id, data=data
                    )

                return redirect("/accounts/team/?alert=added-employee")

        try:
            # Update existing user's details
            user = client.get_user(user_id, organisation_id)
            data.setdefault("active", user["active"])
            data["country_code"] = data.get("selected_country_code", user.get("country_code"))
            # If user is Third Party but owner of *their* organisation, don't update group
            if SECURITY_GROUP_THIRD_PARTY_USER in user["groups"]:
                data.pop("group")
            response = client.update_create_team_user(organisation_id, data, user_id)
            request.session["create-user"] = response
            if not self.self_details:
                redirect_url = f"/accounts/team/{organisation_id}/user/{user_id}/edit/"
            else:
                redirect_url = "/accounts/info/?alert=details-updated"
        except APIException as e:
            logger.warning(f"Problem calling API to update user details: {e}")
            return self.get(request, user_id=user_id, organisation_id=organisation_id, data=data)
        user_id = user_id or response.get(user_id)
        if str(user_id) == str(request.user.id):
            request.user.reload(request)
        if response.get("response", {}).get("success") is False:
            return self.get(
                request, user_id, errors=response.get("response", {}).get("error"), data=data
            )
        return redirect(redirect_url or f"/accounts/team/{organisation_id}/user/{user_id}/")


class AssignUserToCaseView(LoginRequiredMixin, BasePublicView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER]
    template_name = "cases/submissions/assign/tasklist.html"
    submission_type_key = "assign"
    remove = None

    def get(self, request, user_id, case_id=None, submission_id=None, **kwargs):
        documents = []
        invite = None
        representing = None
        user_id = user_id or request.GET.get("user_id")
        errors = kwargs.get("errors") or request.GET.get("errors")
        own_organisation = request.user.organisation
        assign_user = self._client.get_user(user_id=user_id, organisation_id=own_organisation["id"])

        return render(
            request,
            self.template_name,
            {
                "errors": kwargs.get("errors"),
                "enable_submit": self.case and (not representing or self.submission),
                "user_id": user_id,
                "assign_user": assign_user,
                "representing": representing,
                "current_page_name": "Assign user to case",
                "all_organisations": True,
                "case_id": self.case_id,
                "case": self.case,
                "submission": self.submission,
                "submission_id": self.submission["id"] if self.submission else None,
                "invite": invite,
                "organisation": own_organisation,
                "organisation_name": own_organisation.get("name"),
                "documents": documents,
                "application": None,
            },
        )

    def post(self, request, user_id, case_id=None, submission_id=None):
        representing_id = request.POST.get("representing_id")
        organisation_id = request.POST.get("organisation_id")
        case_org_id = request.POST.get("case_org_id")
        case_org_selection = request.POST.get("case_org_selection")
        is_primary = request.POST.get("is_primary")
        redirect_url = request.POST.get("redirect")
        if case_org_id:
            case_id, organisation_id = case_org_id.split(":")
        elif case_org_selection:
            return redirect(
                f"/case/select/organisation/for/{user_id}/"
                f"?redirect=assign_user_to_case|user_id={user_id}&alert=no-selection"
            )
        submission = self.on_submission_update(
            {
                "primary": is_primary,
                "organisation_id": organisation_id,
                "representing_id": representing_id,
                "user_id": user_id,
                "remove": self.remove,
            }
        )
        if self.remove:
            return redirect(f"{redirect_url}?alert=user_unassigned")
        return redirect(f"/case/{self.case_id}/submission/{submission['id']}/")


class AssignUserToCaseContactView(LoginRequiredMixin, BasePublicView, TradeRemediesAPIClientMixin):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER]
    template_name = "cases/submissions/assign/contact.html"

    def get(self, request, user_id, case_id, organisation_id=None, submission_id=None, **kwargs):
        submission = None
        representing = None
        primary = True
        organisation_id = organisation_id or request.GET.get("organisation_id")
        assign_user = self._client.get_user(
            user_id=user_id, organisation_id=request.user.organisation["id"]
        )
        if self.submission:
            primary = (
                self.submission.get("deficiency_notice_params", {})
                .get("assign_user", {})
                .get("contact_status")
            )
            representing = self.submission["organisation"]
        elif organisation_id and organisation_id != assign_user.get("organisation", {}).get("id"):
            representing = self._client.get_organisation(organisation_id)
        else:
            organisation_id = assign_user["organisation"]["id"]

        return render(
            request,
            self.template_name,
            {
                "errors": kwargs.get("errors"),
                "is_primary": primary,
                "user_id": user_id,
                "assign_user": assign_user,
                "representing": representing,
                "current_page_name": "Assign user to case",
                "all_organisations": True,
                "case_id": case_id,
                "case": self.case,
                "submission": self.submission,
                "submission_id": self.submission["id"] if self.submission else None,
                "organisation": self.organisation or assign_user["organisation"],
                "organisation_name": self.organisation.get(
                    "name", assign_user["organisation"]["name"]
                ),
                "application": None,
                "form_action": f"/accounts/team/assign/{user_id}"
                f"/case/{case_id}/submission/{submission_id}/",
            },
        )


class AccountInfo(LoginRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):
    template_name = "account/info.html"

    def get(self, request, *args, **kwargs):
        client = self.client(request.user)
        if "create-user" in request.session:
            del request.session["create-user"]
        if SECURITY_GROUP_THIRD_PARTY_USER in request.user.groups:
            organisation_id = request.user.contact.get("organisation", {}).get("id")
        else:
            organisation_id = request.user.organisation.get("id")
        return render(
            request,
            self.template_name,
            {
                "all_organisations": True,
                "user": request.user,
                "countries": countries,
                "is_owner": request.user.has_group("Organisation Owner"),
                "organisation_id": organisation_id,
                "alert_message": ALERT_MAP.get(request.GET.get("alert")),
                "pre_manage_team": client.get_system_boolean("PRE_MANAGE_TEAM"),
                "organisation": client.get_organisation(organisation_id)
                if organisation_id
                else None,
            },
        )


class AccountEditInfo(LoginRequiredMixin, TemplateView):
    template_name = "account/update.html"

    def get(self, request, *args, **kwargs):
        organisation_id = request.user.organisations[0]["id"]
        return render(
            request,
            self.template_name,
            {
                "all_organisations": True,
                "user": request.user,
                "countries": countries,
                "timezones": pytz.common_timezones,
                "organisation_id": organisation_id,
            },
        )


class FeedbackView(TemplateView, TradeRemediesAPIClientMixin):
    inner = False

    def get(self, request, form_id, placement_id, *args, **kwargs):
        feedback_form = self.trusted_client.get_feedback_form(form_id)
        template = "feedback_form_inner.html" if self.inner else "feedback_form.html"
        return render(request, template, {"form": feedback_form, "placement_id": placement_id})

    def post(self, request, form_id, placement_id):
        client = self.trusted_client
        feedback_form = client.get_feedback_form(form_id)
        response = client.submit_feedback(
            form_key=form_id, placement_id=placement_id, data=request.POST
        )
        template = (
            "feedback_complete_inner.html"
            if request.POST.get("inner", False)
            else "feedback_complete.html"
        )
        return render(request, template, {"form": feedback_form})


class EmailVerifyView(TemplateView, TradeRemediesAPIClientMixin):
    def get(self, request, *args, **kwargs):
        code = request.GET.get("code")
        if code:
            client = (
                self.client(request.user) if request.user.is_authenticated else self.trusted_client
            )
            try:
                response = client.verify_email(code)
                request.session["user"] = response
                request.session["email_verified"] = True
                request.session.modified = True
                if not request.user.is_authenticated:
                    return redirect("/accounts/login/")
                else:
                    result_2fa = self.client(request.user).two_factor_request(
                        delivery_type="sms",
                        user_agent=request.META["HTTP_USER_AGENT"],
                        ip_address=request.META["REMOTE_ADDR"],
                    )
                return redirect("/dashboard/")
            except Exception:
                return redirect("/email/verify/?error=invalid")

        elif request.user.is_authenticated:
            request.user.reload(request)
            if request.user.email_verified_at:
                return redirect("/dashboard/")
        return render(
            request,
            "registration/email_verify.html",
            {
                "email": request.user.email if request.user.is_authenticated else None,
                "error": request.GET.get("error"),
            },
        )

    def post(self, request):
        response = self.client(request.user).verify_email()
        return redirect("/email/verify/")


class CompaniesHouseSearch(TemplateView, TradeRemediesAPIClientMixin):
    def get(self, request, *args, **kwargs):
        query = request.GET.get("term")
        results = self.trusted_client.companies_house_search(query)
        return HttpResponse(json.dumps(results), content_type="application/json")
