from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import ImproperlyConfigured
from django.views.generic import TemplateView
from core.constants import (
    ORG_INDICATOR_TYPE_LARGE,
    ORG_INDICATOR_TYPE_SMALL,
)
from core.exceptions import SentryPermissionDenied
from core.utils import to_word
from core.utils import deep_index_items_by
from cases.submissions import SUBMISSION_TYPE_HELPERS
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin


class GroupRequiredMixin(AccessMixin):
    """Verify that the current user is a member of a group."""

    groups_required = None

    def get_group_required(self):
        """
        Override this method to override the groups_required attribute.
        Must return an iterable.
        """
        if self.groups_required is None:
            raise ImproperlyConfigured(
                "{0} is missing the groups_required attribute. "
                "Define {0}.groups_required, or override "
                "{0}.get_groups_required().".format(self.__class__.__name__)
            )
        if isinstance(self.groups_required, str):
            groups = (self.groups_required,)
        else:
            groups = self.groups_required
        return groups

    def has_group(self):
        """
        Override this method to customize the way groups are checked.
        """
        groups = self.get_group_required()
        return self.request.user.has_group(groups)

    def dispatch(self, request, *args, **kwargs):
        if not self.has_group():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class BasePublicView(TemplateView, TradeRemediesAPIClientMixin):
    """
    Base view for Case driven views.
    The request is set up with the case record and evaluated against any provided organisation id.
    If one is not provided,
    and the case has one organisation in the context of this user, it is used.
    otherwise, if the case has multiple organisations in the context of this user, the user will be
    redirected to an organisation selection page and returned to the original request's URI.
    If no organisation is determined, or the user is not allowed access the request will fail.

    Implementing views will have (based on incoming kwargs/query)
        - self.case
        - self.submission
        - self.organisation
    """

    required_keys = []
    reset_current_organisation = False
    case_page = False
    submission_type_key = None

    def dispatch(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            token = self.request.user.token
            # if a case/org id combo is passed, unpack it first
            self.representing_id = None
            case_org_id = self.request.POST.get("case_org_id")
            if case_org_id:
                self.case_id, self.representing_id = case_org_id.split(":")
            else:
                self.case_id = kwargs.get("case_id") or self.request.GET.get("case_id")
            organisation_id = kwargs.get("organisation_id") or self.request.GET.get(
                "organisation_id"
            )
            self._client = self.client(self.request.user)
            self.user_token = self.request.user.token
            self.submission_id = kwargs.get("submission_id") or self.request.GET.get(
                "submission_id"
            )
            self.case = {}
            self.submission = {}
            self.organisation = {}
            self.submission_helper = None
            self.user = self.request.user
            self.organisation_id = self.get_organisation_id(
                self.request, organisation_id=organisation_id
            )
            if self.case_id:
                self.case = self._client.get_case(case_id=self.case_id)
                if self.submission_id:
                    self.submission = self._client.get_submission_public(
                        case_id=self.case_id, submission_id=self.submission_id
                    )
                    self.submission_type_key = self.submission["type"]["key"]
            # if a submission type key is set, load a helper if applicable
            if self.submission_type_key:
                SubmissionHelper = SUBMISSION_TYPE_HELPERS.get(self.submission_type_key)
                if SubmissionHelper:
                    self.submission_helper = SubmissionHelper(
                        submission=self.submission,
                        user=self.request.user,
                        view=self,
                        case_id=self.case_id,
                    )
                    # self.organisation_id = self.submission['organisation']['id']
            if self.organisation_id:
                if self.organisation_id not in [
                    each["id"] for each in self.request.user.organisations
                ]:
                    # the user is trying to access an organisation's view that they should not
                    # have access to
                    raise SentryPermissionDenied(
                        f"User {self.user.id} tried to access organisation {self.organisation_id} "
                        f"that they do not have access to - "
                        f"{self.request.path} - {self.request.GET}"
                    )
                self.organisation = self._client.get_organisation(
                    organisation_id=self.organisation_id, case_id=self.case_id
                )
            self.case_page_counter(self.request)
            self.alert_message = self.request.GET.get("alert")
            self.error_message = self.request.GET.get("error")
        return super().dispatch(*args, **kwargs)

    # helpers to call methods from the submission helper
    def get_submission_context(self, base_context=None):
        """
        If a submission is present in this request and it has a context helper available,
        return the relevant context for this submission.
        Otherwise returns an empty dict.
        This is usually called from views to enhance template context with submission specific
        one.
        """
        if self.submission_helper:
            return self.submission_helper.get_context(base_context=base_context)
        return base_context or {}

    def on_assign_company(self, params):
        if self.submission_helper:
            return self.submission_helper.on_assign_company(**params)
        return (None, None, None, None)

    def on_submission_update(self, params):
        if self.submission_helper:
            return self.submission_helper.on_update(**params)
        return None

    def on_submission_submit(self):
        if self.submission_helper:
            return self.submission_helper.on_submit()
        return None

    def get_submit_urls(self, key=None, **kwargs):
        if self.submission_helper:
            submit_urls = self.submission_helper.submit_urls(**kwargs)
            if key and key in submit_urls:
                return submit_urls[key]
            return submit_urls
        return None

    def case_page_counter(self, request):
        self.org_indicator_type = None
        if self.case_page and self.case:
            case_counter = request.session.get("_case") or {"id": None, "count": 0}
            if case_counter["id"] == self.case["id"]:
                case_counter["count"] += 1
            else:
                case_counter["id"] = self.case["id"]
                case_counter["count"] = 1
            request.session["_case"] = case_counter
            request.session.modified = True
            self.org_indicator_type = (
                ORG_INDICATOR_TYPE_SMALL if case_counter["count"] > 1 else ORG_INDICATOR_TYPE_LARGE
            )
            return case_counter
        return None

    def setup_request(self, request, *args, **kwargs):
        self.organisation_id = self.get_organisation_id(
            request, organisation_id=kwargs.get("organisation_id")
        )
        if kwargs.get("case_id"):
            self.case = self._client.get_case(case_id=kwargs["case_id"])
            if kwargs.get("submission_id"):
                self.submission = self._client.get_submission_public(
                    case_id=kwargs["case_id"], submission_id=kwargs["submission_id"]
                )
                self.organisation_id = self.submission["organisation"]["id"]
        # f'/organisation/set/?next={request.GET.get('next', request.POST.get('next'))}'

    def get_organisation_id(self, request, organisation_id=None):
        if request.session.get("organisation_id"):
            organisation_id = request.session.get("organisation_id")
        elif not organisation_id:
            organisation_id = request.GET.get(
                "organisation_id", request.POST.get("organisation_id")
            )
        return organisation_id

    def check_required_keys(self, request):
        """
        Evaluate a POST request for the existence and truthfulness of all required
        keys if applicable
        """
        errors = {}
        if self.required_keys:
            for key in self.required_keys:
                if not request.POST.get(key):
                    errors[key] = f"{to_word(key)} is required"
        return errors

    def populate_objects(self, request, case_id, submission_type_id, submission_id):
        """
        Sets up objects from case and either submission_id or submission_type
        """
        self.user_token = request.user.token
        self.case_id = case_id
        self.organisation_id = request.session["organisation_id"]
        if submission_id:
            self.submission = self._client.get_submission_public(case_id, submission_id)
            self.submission_id = submission_id
            self.submission_type = self.submission["type"]
            self.submission_type_id = self.submission_type["id"]
            self.organisation_id = (
                self.submission.get("organisation", {}).get("id")
                or request.session["organisation_id"]
            )
        else:
            self.submission_type = self._client.get_submission_type(submission_type_id)
            self.submission_type_id = submission_type_id

    def get_submission_documents(self, documents=None, request_for_sub_org=False):
        """
        Return an index of all the documents of this submission.
        Deficiency documents are retrieved from the parent if applicable.
        By default, the request is made on behalf of the requesting user's organisations.
        In some cases, it is needed to request for the organisation represented, i.e.,
        the one set on the submission (which might or might not be the same organisation).
        If that is the case, set request_for_sub_org to True.
        """
        if not documents:
            request_for = (
                self.organisation_id
                if not request_for_sub_org
                else self.submission["organisation"]["id"]
            )
            sub_documents = self._client.get_submission_documents(
                self.case_id, self.submission_id, request_for_organisation_id=request_for
            )
            documents = sub_documents.get("documents", [])

        submission_documents = deep_index_items_by(documents, "type/key")
        submissions_from_public = submission_documents.get("respondent", [])

        document_conf_index = deep_index_items_by(submissions_from_public, "confidential")

        caseworker_conf_index = deep_index_items_by(
            submission_documents.get("caseworker", []), "confidential"
        )

        document_deficient_index = deep_index_items_by(submissions_from_public, "deficient")
        loa_deficient_index = deep_index_items_by(submission_documents.get("loa", []), "deficient")

        # Get the deficiency documents from the parent if applicable
        parent_deficiency_documents = []

        if self.submission and self.submission.get("previous_version"):
            _def_docs = self._client.get_submission_documents(
                self.case_id, self.submission["previous_version"]["id"]
            )
            parent_deficiency_documents = _def_docs["deficiency_documents"]
        return {
            "caseworker": submission_documents.get("caseworker", []),
            "respondent": submissions_from_public,
            "deficiency": parent_deficiency_documents,
            "issued": [doc for doc in documents if doc.get("issued")],
            "confidential": document_conf_index.get("true", []),
            "non_confidential": [
                doc
                for doc in (document_conf_index.get("false", []))
                if not doc["block_from_public_file"]
            ],
            "tra_non_confidential": caseworker_conf_index.get("false", []),
            "deficient": document_deficient_index.get("true", []),
            "loa_deficient": loa_deficient_index.get("true", []),
            "loa": submission_documents.get("loa", []),
        }

    def clear_docs_reviewed(
        self,
    ):
        # If the submission has the docs reviewed flag set, clear it.
        if self.submission and self.submission.get("doc_reviewed_at"):
            response = self._client.update_submission_public(
                case_id=self.case_id,
                organisation_id=self.organisation_id,
                submission_id=self.submission_id,
                data={"doc_reviewed_at": ""},
            )
            try:
                del self.submission["doc_reviewed_at"]
            except KeyError:
                pass
