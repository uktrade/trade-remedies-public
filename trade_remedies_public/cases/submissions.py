import json
from django.utils import timezone
from trade_remedies_client.client import Client
from django_countries import countries
from core.utils import get
from cases.constants import (
    CASE_DOCUMENT_TYPE_LETTER_OF_AUTHORISATION,
    SUBMISSION_TYPE_ASSIGN_TO_CASE,
    SUBMISSION_TYPE_INVITE_3RD_PARTY,
    CASE_ROLE_PREPARING,
)


class BaseSubmissionHelper:
    """
    A base class for submission helpers.
    Enhance a task list with submission specific data.
    """

    type_ids = None

    def __init__(self, submission, user, view=None, case_id=None):
        self.case_id = case_id
        self.submission = submission
        self.case = submission["case"] if submission else None
        if not self.case_id and self.case:
            self.case_id = self.case["id"]
        self.user = user
        self.view = view

    def get_context(self, base_context=None):
        return base_context or {}

    def on_update(self, **kwargs):
        return None

    def on_submit(self, **kwargs):
        """
        Triggered when a submission is complete and submitted (final step).
        Can return an overriden redirect url
        """
        return None

    def on_assign_company(self, **kwargs):
        """
        Returns a tuple of:
            (organisation_id, case_id, submission_id, case_created_bool)
        """
        return (None, None, None, None)

    def submit_urls(self, **kwargs):
        """
        Return a dict with relevant form submission urls for specific forms in the tasklist
        process
        """
        return {
            "company": None,
        }

    @property
    def client(self):
        try:
            return self._client
        except AttributeError:
            self._client = Client(self.user.token)
        return self._client


class InviteThirdPartySubmission(BaseSubmissionHelper):
    type_ids = []

    def get_context(self, base_context=None):
        context = super().get_context()
        if not self.case:
            return context

        invites = []
        documents = []
        if self.submission:
            invites = self.client.get_third_party_invites(self.case_id,
                                                          self.submission["id"])
            case_documents = self.client.get_case_documents(
                self.case_id, CASE_DOCUMENT_TYPE_LETTER_OF_AUTHORISATION)
            documents = [doc for doc in case_documents]
        context["invites"] = invites
        context["case_documents"] = documents
        if 'documents' in context:
            context['documents']['caseworker'] += documents
        else:
            context['documents'] = {"caseworker": documents}
        return context

    def on_submit(self, **kwargs):
        super().on_update(**kwargs)


class AssignUserSubmission(BaseSubmissionHelper):
    type_ids = []

    def get_context(self, base_context=None):
        context = base_context or {}
        if self.submission:
            has_documents = any(
                [
                    subdoc.get("type", {}).get("key") == "respondent"
                    for subdoc in self.submission["documents"]
                ]
            )
            context["primary"] = (
                self.submission.get("deficiency_notice_params", {})
                .get("assign_user", {})
                .get("contact_status")
            )
            context["is_primary"] = context["primary"]
            context["assign_user"] = self.submission["contact"]["user"]
            context["representing"] = self.submission["organisation"]
            context["representing_third_party"] = get(self.submission, "organisation/id") != get(
                self.submission, "contact/organisation/id"
            )
            context["has_documents"] = has_documents
            context["enable_submit"] = context["primary"] and (
                context["representing"]["id"] == self.user.organisation["id"] or has_documents
            )
            context["organisation"] = context.get("current_organisation")
            if self.view:
                documents = self.view.get_submission_documents(request_for_sub_org=True)
                context["all_documents"] = documents
                context["documents"] = documents.get("caseworker", [])
        return context

    def on_update(self, **kwargs):
        """
        Handles updates or creation of a submission
        Returns the submission.
        """
        response = None
        is_primary = kwargs.get("primary")
        organisation_id = kwargs.get("organisation_id")
        representing_id = kwargs.get("representing_id")
        user_id = kwargs.get("user_id")
        remove = kwargs.get("remove")
        own_organisation = self.user.organisation
        representing_third_party = representing_id and representing_id != own_organisation["id"]
        assign_user = self.client.get_user(user_id=user_id, organisation_id=own_organisation["id"])
        if remove:
            self.client.remove_user_from_case(
                organisation_id, user_id, self.case_id, representing_id
            )
            return None
        if self.submission:
            current_primary_state = (
                self.submission.get("deficiency_notice_params", {})
                .get("assign_user", {})
                .get("contact_status")
            )
            if is_primary is not None and is_primary != current_primary_state:
                deficiency_notice_params = self.submission.get("deficiency_notice_params", {})
                deficiency_notice_params["assign_user"] = {"contact_status": kwargs["primary"]}
                response = self.client.update_submission(
                    case_id=self.case["id"],
                    submission_id=self.submission["id"],
                    **{"deficiency_notice_params": json.dumps(deficiency_notice_params)},
                )
        else:
            if organisation_id != assign_user.get("organisation", {}).get("id"):
                representing = self.client.get_organisation(organisation_id)
            else:
                representing = own_organisation
            exists = self.client.submission_type_exists_for_case(
                self.case_id, representing["id"], SUBMISSION_TYPE_ASSIGN_TO_CASE
            )
            if exists.get("exists"):
                self.submission = exists["submission"]
            else:
                response = self.client.create_submission(
                    case_id=self.case_id,
                    organisation_id=representing["id"],
                    submission_type=SUBMISSION_TYPE_ASSIGN_TO_CASE,
                    contact_id=assign_user["contact"]["id"],
                    name="Assign user to case",
                    deficiency_notice_params=json.dumps(
                        {"assign_user": {"contact_status": is_primary}}
                    ),
                )
                self.submission = response.get("submission")
        return self.submission

    def on_submit(self, **kwargs):
        """
        Triggered when user assignment is submitted. If the assignment is to own case,
        the user will be assigned.
        Returns an overriden redirect url if the assignment was successful.
        """
        user_organisation_id = (
            get(self.submission, "contact/organisation/id")
            or get(self.submission, "contact/user/organisation/id")
            or get(self.user.organisation, "id")
        )
        user_id = get(self.submission, "contact/user/id")
        if get(self.submission, "organisation/id") == user_organisation_id:
            # make the case assignment.
            is_primary = (
                self.submission.get("deficiency_notice_params", {})
                .get("assign_user", {})
                .get("contact_status")
                == "primary"
            )
            self.client.assign_user_to_case(
                user_organisation_id=user_organisation_id,
                representing_id=get(self.submission, "organisation/id"),
                user_id=user_id,
                case_id=self.case["id"],
                primary=is_primary,
            )
            self.client.set_submission_state(self.case["id"], self.submission["id"], "sufficient")
            return f"/accounts/team/{user_organisation_id}/user/{user_id}/?alert=user-assigned"
        return f"/accounts/team/{user_organisation_id}/user/{user_id}/?alert=user-assigned-req"


class RegisterInterestSubmission(BaseSubmissionHelper):
    type_ids = []

    def get_context(self, base_context=None):
        context = base_context or {}
        context.update(
            {
                "case_id": self.case_id,
                "countries": countries,
                "country": "GB",
                "representing": "",
            }
        )
        return context

    def submit_urls(self, **kwargs):
        company_url = "/case/interest/"
        if kwargs.get("case_id"):
            company_url = f"{company_url}{kwargs['case_id']}/company/"
        if kwargs.get("submission_id"):
            company_url = f"{company_url}{kwargs['submission_id']}/company/"
        return {
            "company": company_url,
        }

    def on_assign_company(self, **kwargs):
        response = self.client.register_interest_in_case(self.case_id, **kwargs)
        submission = response["submission"]
        organisation = submission["organisation"]
        return organisation, submission["case"], submission, False

    def on_submit(self, **kwargs):
        """
        On submission of reg-interest submission, set the case role
        """
        case_id = self.case["id"]
        submission_id = self.submission["id"]
        current_role_id = self.submission.get("organisation_case_role", {}).get("id")
        if not current_role_id or current_role_id in (CASE_ROLE_PREPARING,):
            response = self.client.set_organisation_case_role(
                case_id=case_id,
                organisation_id=self.submission["organisation"]["id"],
                role_key="awaiting_approval",
            )
        return f"/case/{case_id}/submission/{submission_id}/submitted/"


class ApplicationSubmission(BaseSubmissionHelper):
    type_ids = []

    def submit_urls(self, **kwargs):
        if kwargs.get("case_id"):
            company_url = f"/case/{kwargs['case_id']}/company/"
            if kwargs.get("submission_id"):
                company_url = (
                    f"/case/{kwargs['case_id']}/submission/{kwargs['submission_id']}/company/"
                )
        else:
            company_url = "/case/company/"
        return {
            "company": company_url,
        }

    def on_assign_company(self, **kwargs):
        case = None
        submission = None
        organisation = None
        case_created = False
        if self.case_id:
            organisation = self.client.submit_organisation_information(
                case_id=self.case_id, country=kwargs.get("organisation_country"), **kwargs
            )
        else:
            organisation, case, submission = self.client.initiate_new_application(**kwargs)
            case_created = True
        return organisation, case, submission, case_created

    def on_submit(self, **kwargs):
        response = self.client.update_case(
            case_id=self.case["id"],
            update_spec={
                "submitted_at": timezone.now(),
                "stage_id": "8aadc503-c1a5-427f-808b-88e794e2f919",
                "next_action": "INIT_ASSESS",
            },
        )
        return f"/case/{self.case['id']}/submission/{self.submission['id']}/submitted/"


SUBMISSION_TYPE_HELPERS = {
    "invite": InviteThirdPartySubmission,
    "assign": AssignUserSubmission,
    "interest": RegisterInterestSubmission,
    "application": ApplicationSubmission,
}
