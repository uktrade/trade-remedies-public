import logging

import json

from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django_countries import countries
from django.utils import timezone
from django.urls import reverse

from django_chunk_upload_handlers.clam_av import VirusFoundInFileException

from core.base import GroupRequiredMixin, BasePublicView
from cases.constants import (
    SUBMISSION_TYPE_EX_OFFICIO,
    SUBMISSION_TYPE_ALL_ORGANISATIONS,
    SUBMISSION_TYPE_ADHOC,
    DIRECTION_BOTH,
    DIRECTION_PUBLIC_TO_TRA,
    ALL_COUNTRY_CASE_TYPES,
    SUBMISSION_TYPE_INVITE_3RD_PARTY,
)
from core.constants import ALERT_MAP
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
from trade_remedies_client.exceptions import APIException
from cases.utils import (
    decorate_due_status,
    get_org_parties,
    decorate_submission_updated,
    validate_hs_code,
    structure_documents,
)
from core.utils import (
    deep_index_items_by,
    proxy_stream_file_download,
    pluck,
    first,
    get,
    validate,
    parse_redirect_params,
    internal_redirect,
)
from config.constants import (
    ROLE_APPLICANT,
    SECURITY_GROUP_ORGANISATION_OWNER,
    SECURITY_GROUP_ORGANISATION_USER,
    SECURITY_GROUP_THIRD_PARTY_USER,
)

from core.validators import (
    company_form_validators,
    review_form_validators,
    third_party_validators_base,
    third_party_validators_uk,
    third_party_validators_non_uk,
)
import dpath

from cases.forms import (
    ClientTypeForm,
    PrimaryContactForm,
    YourEmployerForm,
    UkEmployerForm,
    NonUkEmployerForm,
    ClientFurtherDetailsForm,
    ExistingClientForm,
)

logger = logging.getLogger(__name__)


TASKLIST_BY_CASE_ROLE = {
    ROLE_APPLICANT: "application",
    "DEFAULT": "questionnaire",
}


def process_company_parameters(request):
    # process a submission from the company selection page.
    params = pluck(
        request.POST,
        [
            "organisation_name",
            "companies_house_id",
            "organisation_post_code",
            "organisation_address",
            "organisation_country",
            "representing_value",
            "organisation_id",
            "previous_organisation_id",
            "vat_number",
            "eori_number",
            "duns_number",
            "organisation_website",
        ],
    )

    errors = []
    representing = params.get("representing_value")
    if representing == "previous":
        params["organisation_id"] = params.get("previous_organisation_id")
    if representing == "other":
        del params["organisation_id"]
        errors = validate(params, company_form_validators)
    if not representing:
        errors = {"representing_value", "You must choose an organisation type"}
    return params, errors


class CaseOrganisationSelectView(
    LoginRequiredMixin, GroupRequiredMixin, TemplateView, TradeRemediesAPIClientMixin
):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
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


class CasesView(LoginRequiredMixin, GroupRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER]
    template_name = "cases/cases.html"
    reset_current_organisation = True

    def get(self, request, *args, **kwargs):
        all_cases = request.user.has_perm("can_view_all_org_cases")
        archived = request.GET.get("archived", "false") == "true"
        request.session["organisation_id"] = None
        request.session.modified = True
        client = self.client(request.user)
        user_org_cases = client.get_user_cases(archived=archived, outer=True)
        all_interests = client.get_registration_of_interest(all_interests=all_cases)
        # splice inerests onto cases
        for interest in all_interests:
            user_org_cases.append(
                {
                    "user": interest.get("created_by"),
                    "case": interest.get("case"),
                    "representing": interest.get("organisation"),
                    "organisation": request.user.organisation,
                    "roi_sent": (interest.get("status") or {}).get("sent"),
                }
            )
        org_cases = {}
        for uoc in user_org_cases:
            ref = dpath.util.get(uoc, "case/id") + ":" + dpath.util.get(uoc, "representing/id")
            org_cases.setdefault(ref, []).append(uoc)

        return render(
            request,
            self.template_name,
            {
                "archived": archived,
                "org_cases": org_cases,
                "order": sorted(
                    org_cases.keys(),
                    key=lambda oc_key: org_cases.get(oc_key)[0].get("case").get("reference"),
                ),
            },
        )


class CaseSummaryView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER]
    template_name = "cases/case_summary.html"

    def get(self, request, case_id, organisation_id, *args, **kwargs):
        # all_cases = request.user.has_perm('can_view_all_org_cases')
        user_org_cases = self._client.get_user_cases(archived=False, outer=True)
        # all_interests = self._client.get_registration_of_interest(all_interests=True)
        case_id = str(case_id)
        organisation_id = str(organisation_id)
        filtered_uoc = []
        orgs = {}
        for uoc in user_org_cases:
            org_id = uoc.get("representing").get("id")
            if uoc.get("case").get("id") == case_id and org_id == organisation_id:
                orgs.setdefault(org_id, [])
                orgs[org_id].append(uoc)
        case = self._client.get_case(case_id=case_id, organisation_id=organisation_id)
        return render(
            request,
            self.template_name,
            {"case": case, "orgs": orgs, "user_org_cases": list(filtered_uoc)},
        )


class TaskListView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    """
    Task list view of a case submission
    """

    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "cases/tasklist.html"
    case_page = True

    def get(
        self,
        request,
        case_id=None,
        submission_id=None,
        organisation_id=None,
        public_str=None,
        *args,
        **kwargs,
    ):
        # Handle 3rd party invite unless submission locked or is a deficiency notice
        if self.submission.get("type", {}).get("id") == SUBMISSION_TYPE_INVITE_3RD_PARTY:
            if not self.submission["locked"] and self.submission["deficiency_sent_at"] is None:
                # Handle with CaseInviteView
                return redirect(f"/case/invite/{case_id}/submission/{submission_id}")

        public = public_str == "public"
        just_submitted = public_str == "submitted"
        state = {}
        org_case_role = {}
        tasklist_template = self.submission_type_key or "application"
        if self.organisation and case_id:
            org_case_role = self.organisation["case_role"]
            state = self._client.get_application_state(self.organisation_id, case_id)
        if self.submission:
            if not self.organisation:
                organisation_id = request.session.get("organisation_id")
                self.organisation = self.submission.get("organisation")
        documents = self.get_submission_documents() if self.submission else []
        submission_org_id = self.submission.get("organisation", {}).get("id")
        global_submission = not bool(submission_org_id)
        if (
            state
            and not state.get("source")
            and self.case
            and self.case.get("type")
            and int(self.case.get("type", {}).get("id")) in ALL_COUNTRY_CASE_TYPES
        ):
            state["source"] = True
        # This is the user's submission if he's representing the company, or created it
        not_own_org_submission = not global_submission and not (
            request.user.is_representing(submission_org_id, request)
            or request.user.id == self.submission["created_by"]["id"]
        )
        if public or not_own_org_submission or self.submission.get("status", {}).get("locking"):
            if public or not_own_org_submission:
                template_name = f"cases/submissions/{tasklist_template}/view_public.html"
            else:
                template_name = f"cases/submissions/{tasklist_template}/view.html"
        else:
            template_name = f"cases/submissions/{tasklist_template}/tasklist.html"
        _context = {
            "all_organisations": True
            if not self.organisation
            else False,  # tasklist_template in SUBMISSION_TYPE_ALL_ORGANISATIONS,
            "ROLE_APPLICANT": ROLE_APPLICANT,
            "case_id": case_id,
            "case": self.case,
            "state": state,
            "submission": self.submission,
            "submission_id": submission_id,
            "documents": documents,
            "current_organisation": self.organisation,
            "organisation_name": self.organisation.get("name"),
            "case_role": org_case_role,
            "org_indicator_type": self.org_indicator_type,
            "public": public,
            "just_submitted": just_submitted,
        }
        _submission_context = self.get_submission_context(base_context=_context)
        # temp hack to support assign submission
        if _context.get("all_documents"):
            _context["documents"] = _context["all_documents"]
        return render(request, template_name, _submission_context)


class CaseSubmissionsView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "cases/submissions.html"

    def get(self, request, case_id, *args, **kwargs):
        submissions = self._client.get_submissions_public(case_id=case_id, private=True)
        return render(
            request,
            self.template_name,
            {
                "case_id": case_id,
                "application": request.session["application"],
                "submissions": submissions,
            },
        )


class CaseView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    """
    A single case view, showing all submissions
    """

    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "cases/case.html"
    case_page = True

    def get(self, request, case_id, organisation_id=None, *args, **kwargs):
        case_enums = self._client.get_all_case_enums(case_id=case_id)
        if not self.organisation_id:
            user_orgs = self._client.get_user_case_organisations(case_id)
            if len(user_orgs) == 1:
                self.organisation_id = str(user_orgs[0]["id"])
                request.session["organisation_id"] = self.organisation_id
                request.session.modified = True
                self.organisation = self._client.get_organisation(self.organisation_id)
            elif user_orgs:
                return redirect(f"/case/{case_id}/organisation/select/?next=/case/{case_id}/")
            else:
                return redirect(f"/dashboard/{case_id}")
        tab = request.GET.get("tab") or "your_file"
        case_users = None
        submissions = None

        if tab == "case_members":
            case_users = self._client.get_organisation_users(self.organisation_id, case_id)
            case_users.sort(key=lambda cu: cu.get("name") or "", reverse=True)
        else:
            private = tab == "your_file"
            case_submissions = self._client.get_submissions_public(
                organisation_id=self.organisation_id,
                case_id=case_id,
                private=private,
                get_global=not private,
            )
            submissions = [
                submission
                for submission in case_submissions
                if submission.get("issued_at") or tab == "your_file"
            ]
            for submission in submissions:
                # Add due flags and last updated date
                submission.update(decorate_due_status(submission.get("due_at")))
                submission.update(decorate_submission_updated(submission))
            submissions.sort(key=lambda su: su.get("updated_at") or "", reverse=True)

        tabs = {
            "tabList": [
                {"label": "Your file", "value": "your_file", "selected": True},
                {"label": "Public file", "value": "case_record"},
                {"label": "Case members", "value": "case_members"},
            ],
            "value": tab,
            "urlExt": f"&organisation_id={self.organisation_id}",
        }
        # If the user is a 3rd party collaborator we want to show the organisation
        # they are representing in this case.
        is_third_party = SECURITY_GROUP_THIRD_PARTY_USER in request.user.groups
        inviting_organisation_name = "Unknown"
        if is_third_party:
            all_submissions = self._client.get_submissions(case_id)
            invite_to_case_submission = {
                s.get("invitations")[0]["name"]: s
                for s in all_submissions
                if s["type"].get("name") == "Invite 3rd party"
            }[self.user.name]
            inviting_organisation_name = invite_to_case_submission.get("organisation_name")
        return render(
            request,
            self.template_name,
            {
                "case_id": case_id,
                "case": self.case,
                "submissions": submissions,
                "current_organisation": self.organisation,
                "tabs": tabs,
                "tab": tab,
                "ex_officio_submission_type": SUBMISSION_TYPE_EX_OFFICIO,
                "case_enums": case_enums,
                "org_indicator_type": self.org_indicator_type,
                "this_user": request.user,
                "case_users": case_users if case_users else None,
                "is_org_owner": SECURITY_GROUP_ORGANISATION_OWNER in request.user.groups,
                "is_third_party": is_third_party,
                "inviting_organisation_name": inviting_organisation_name,
                "alert_message": ALERT_MAP.get(self.request.GET.get("alert")),
            },
        )


class InterestStep2BaseView(LoginRequiredMixin, GroupRequiredMixin, FormView):
    def form_invalid(self, form):
        form.assign_errors_to_request(self.request)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.kwargs)
        return context


class InterestClientTypeStep2(BasePublicView, InterestStep2BaseView):    
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "v2/registration_of_interest/who_is_registering.html"
    form_class = ClientTypeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.request.GET)
        # a list of dictionaries
        existing_clients_list = get_org_parties(self._client, self.request.user)
        context["existing_clients"] = True if existing_clients_list else False
        return context

    def form_valid(self, form):
        case_id = self.get_context_data()["case_id"]
        
        if form.cleaned_data.get("org") == "new-org":
            return redirect(f"/case/interest/{case_id}/contact/")  # noqa: E501
        elif form.cleaned_data.get("org") == "my-org":
            api_client = self.client(self.request.user)
            response = api_client.register_interest_in_case(
                case_id=case_id,
                representing="own",
                organisation_id = self.request.user.organisation.get("id"),
            )
            submission = response["submission"]
            submission_id = submission["id"]
            organisation_id = submission["organisation"]["id"]
            api_client.update_submission(
                case_id=case_id,
                submission_id=submission_id,
                # contact_id=contact_id,  # TODO: Is this required for 'own' or 'previous' organisations?
            )
            return redirect(
                f"/case/{case_id}/organisation/{organisation_id}/submission/{submission_id}/"
            )
        elif form.cleaned_data.get("org") == "existing-org":
            return redirect(f"/case/interest/{case_id}/organisation/")


class InterestExistingClientStep2(BasePublicView, InterestStep2BaseView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "v2/registration_of_interest/who_you_representing_existing.html"
    form_class = ExistingClientForm

    def get_existing_clients(self):
        org_parties = get_org_parties(self._client, self.request.user)
        # extract and return tuples of id and name in a list (from a 
        # list of dictionaries)
        return [(d["id"], d["name"]) for d in org_parties]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.request.GET)
        context["existing_clients"] = self.get_existing_clients()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["existing_clients"] = self.get_existing_clients()
        return kwargs

    def form_valid(self, form):
        case_id = self.get_context_data()["case_id"]
        organisation_id = form.cleaned_data.get("org")
        return redirect(f"/case/interest/{case_id}/{organisation_id}/contact/")


class InterestPrimaryContactStep2(TradeRemediesAPIClientMixin, InterestStep2BaseView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "v2/registration_of_interest/primary_client_contact.html"
    form_class = PrimaryContactForm

    def form_valid(self, form):
        context = self.get_context_data()
        case_id = context["case_id"]
        # organisation_id only exists if registering ROI for existing client
        organisation_id = context.get("organisation_id", "")
        response = self.client(self.request.user).create_contact(
            {
                "contact_email": form.cleaned_data.get("email"),
                "contact_name": form.cleaned_data.get("name"),
            }
        )
        contact_id = response["id"]
        # If ROI is for existing client
        if organisation_id:
            api_client = self.client(self.request.user)
            response = api_client.register_interest_in_case(
                case_id=case_id,
                representing="previous",
                organisation_id=organisation_id,
            )
            submission = response["submission"]
            submission_id = submission["id"]
            organisation_id = submission["organisation"]["id"]
            api_client.update_submission(
                case_id=case_id,
                submission_id=submission_id,
                contact_id=contact_id,
            )
            return redirect(
                f"/case/{case_id}/organisation/{organisation_id}/submission/{submission_id}/"
            )
        else:
            return redirect(f"/case/interest/{case_id}/{contact_id}/ch/")  # noqa: E501


class InterestUkRegisteredYesNoStep2(InterestStep2BaseView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "v2/registration_of_interest/is_client_uk_company.html"
    form_class = YourEmployerForm

    def form_valid(self, form):
        context = self.get_context_data()
        case_id = context["case_id"]
        contact_id = context["contact_id"]
        if form.cleaned_data.get("uk_employer") == "yes":
            return redirect(f"/case/interest/{case_id}/{contact_id}/ch/yes/")  # noqa: E501
        elif form.cleaned_data.get("uk_employer") == "no":
            return redirect(f"/case/interest/{case_id}/{contact_id}/ch/no/")  # noqa: E501


class InterestNonUkRegisteredStep2(InterestStep2BaseView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "v2/registration_of_interest/your_client_details.html"
    form_class = NonUkEmployerForm

    def form_valid(self, form):
        context = self.get_context_data()
        case_id = context["case_id"]
        contact_id = context["contact_id"]
        return redirect(
            f"/case/interest/{case_id}/{contact_id}/submit/?organisation_name="
            f"{form.cleaned_data.get('organisation_name')}&companies_house_id="
            f"{form.cleaned_data.get('company_number')}&"
            f"organisation_post_code={form.cleaned_data.get('post_code')}&non_uk_registered=true&"
            f"organisation_address={form.cleaned_data.get('address_snippet')}&"
            f"organisation_country={form.cleaned_data.get('country')}"  # noqa: E501
        )


class InterestIsUkRegisteredStep2(InterestStep2BaseView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "v2/registration_of_interest/who_you_representing.html"
    form_class = UkEmployerForm

    def form_valid(self, form):
        context = self.get_context_data()
        case_id = context["case_id"]
        contact_id = context["contact_id"]
        return redirect(
            f"/case/interest/{case_id}/{contact_id}/submit/?organisation_name="
            f"{form.cleaned_data.get('organisation_name')}&"
            f"companies_house_id={form.cleaned_data.get('companies_house_id')}&"
            f"organisation_post_code={form.cleaned_data.get('organisation_post_code')}&"
            f"organisation_address={form.cleaned_data.get('organisation_address')}"  # noqa: E501
        )


class InterestUkSubmitStep2(TradeRemediesAPIClientMixin, InterestStep2BaseView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "v2/registration_of_interest/about_your_client.html"
    form_class = ClientFurtherDetailsForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.request.GET)
        if not context.get("organisation_country"):
            context["organisation_country"] = "GB"
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        case_id = context["case_id"]
        contact_id = context["contact_id"]
        organisation_name = context["organisation_name"]
        companies_house_id = context["companies_house_id"]
        organisation_post_code = context["organisation_post_code"]
        organisation_address = context["organisation_address"]
        organisation_country = context["organisation_country"]
        eori_number = form.cleaned_data.get("company_eori_number")
        duns_number = form.cleaned_data.get("company_duns_number")
        organisation_website = form.cleaned_data.get("company_website")
        vat_number = form.cleaned_data.get("company_vat_number")
        api_client = self.client(self.request.user)
        response = api_client.register_interest_in_case(
            case_id=case_id,
            representing="other",
            eori_number=eori_number,
            duns_number=duns_number,
            organisation_website=organisation_website,
            vat_number=vat_number,
            organisation_name=organisation_name,
            companies_house_id=companies_house_id,
            organisation_post_code=organisation_post_code,
            organisation_address=organisation_address,
            organisation_country=organisation_country,
        )
        submission = response["submission"]
        submission_id = submission["id"]
        organisation_id = submission["organisation"]["id"]
        api_client.update_submission(
            case_id=case_id,
            submission_id=submission_id,
            contact_id=contact_id,
        )
        return redirect(
            f"/case/{case_id}/organisation/{organisation_id}/submission/{submission_id}/"
        )


class CompanyView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    required_keys = ["representing"]
    case_page = True

    def get(self, request, case_id=None, submission_id=None, *args, **kwargs):
        # form_action = '/case/company/'
        form_action = self.get_submit_urls("company", case_id=case_id, submission_id=submission_id)
        sub_type_key = self.submission_type_key or "application"
        template_name = f"cases/submissions/{sub_type_key}/company_info.html"
        if sub_type_key == "interest" and "FEATURE_FLAG_UAT_TEST" in request.user.groups:
            return redirect(f"/case/interest/{case_id}/type/")  # noqa: E501

        page = request.GET.get("page") or 1
        return render(
            request,
            template_name,
            {
                "form_action": form_action,
                "case_id": case_id,
                "case": self.case,
                "submission_id": submission_id,
                "submission": self.submission,
                "errors": kwargs.get("errors"),
                "org_indicator_type": self.org_indicator_type,
                "org_parties": get_org_parties(self._client, request.user),
                "page": page,
                "submission_type_key": sub_type_key,
                "no_context_back_link": "/case/",
                "representing_value": kwargs.get("representing_value"),
                **kwargs,
                **self.get_submission_context(),
            },
        )

    def post(self, request, case_id=None, submission_id=None, *args, **kwargs):  # noqa: C901
        page = request.POST.get("page")
        if page == "role":
            params = request.session["organisation"]
            params["organisation_role"] = request.POST.get("organisation_role")
            try:
                organisation, case, submission, created = self.on_assign_company(params)
            except APIException as exc:
                return self.get(
                    request, case_id=case_id, submission_id=submission_id, errors=exc.detail
                )
            if created:
                request.user.reload(request)
            request.session["organisation_id"] = organisation["id"]
            request.session.modified = True
            return redirect(
                f"/case/{case['id']}/organisation/{organisation['id']}/submission/{submission['id']}/"  # noqa: E501
            )
        else:
            representing_value = request.POST.get("representing_value")
            # check for a no-js save, and show the selected page if so
            if (request.POST.get("btn-action") == "no-js-save") and representing_value:
                return self.get(
                    request,
                    case_id=case_id,
                    submission_id=submission_id,
                    representing_value=representing_value,
                )
            params, errors = process_company_parameters(request)
            request.session["organisation"] = params
            if errors:
                return self.get(request, case_id=case_id, submission_id=submission_id, **params)
            enable_review_process = self._client.get_system_boolean("PRE_REVIEW_APPLICATIONS")
            if self.submission_type_key == "application" and enable_review_process:
                request.session.modified = True
                return redirect("/case/company/?page=role")
            else:
                params["representing"] = params.get("representing_value")
                try:
                    organisation, case, submission, created = self.on_assign_company(params)
                except APIException as exc:
                    return self.get(
                        request, case_id=case_id, submission_id=submission_id, errors=exc.detail
                    )
            if created:
                request.user.reload(request)
            request.session["organisation_id"] = organisation["id"]
            request.session.modified = True
            return redirect(
                f"/case/{case['id']}/organisation/{organisation['id']}/submission/{submission['id']}/"  # noqa: E501
            )


class ProductView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "cases/product.html"
    required_keys = ["product_name", "sector"]
    case_page = True

    def get(self, request, case_id=None, submission_id=None, product_id=None, *args, **kwargs):
        sectors = self._client.get_sectors()
        organisation_id = get(self.submission, "organisation/id", {}) or request.session.get(
            "organisation_id"
        )
        product = self._client.get_product(organisation_id, case_id)
        product.setdefault("hs_codes", [])
        product["hs_codes"].append({"code": ""})
        if kwargs.get("errors"):
            product.update(
                {
                    "sector": {
                        "id": int(request.POST.get("sector"))
                        if request.POST.get("sector")
                        else None
                    },
                    "description": request.POST.get("description"),
                    "name": request.POST.get("product_name"),
                }
            )
        return render(
            request,
            self.template_name,
            {
                "case_id": case_id,
                "sectors": sectors,
                "product": product,
                "submission_id": submission_id,
                "errors": kwargs.get("errors"),
                "org_indicator_type": self.org_indicator_type,
                "pre_review_applications": self._client.get_system_boolean(
                    "PRE_REVIEW_APPLICATIONS"
                ),
            },
        )

    def post(self, request, case_id=None, submission_id=None, product_id=None, *args, **kwargs):
        organisation_id = get(self.submission, "organisation/id") or request.session.get(
            "organisation_id"
        )
        if request.POST.get("delete"):
            self._client.remove_product_hs_code(
                organisation_id, case_id, product_id, request.POST["delete"]
            )
            return redirect(f"/case/{case_id}/submission/{submission_id}/product/")
        hs_codes = request.POST.getlist("hs_code")
        errors = self.check_required_keys(request)
        valid_codes = False
        if hs_codes:
            for code in hs_codes:
                if not validate_hs_code(code):
                    errors["hs_code"] = f"Invalid HS Code: {code}. You must enter 6, 8 or 10 digits"
                    break
                elif code:
                    valid_codes = True
        if not valid_codes:
            errors["hs_code"] = get(errors, "hs_code") or "You must provide at least one HS code"
        json_data = get(self.submission, "deficiency_notice_params") or {}
        json_data["case_category"] = request.POST.get("case_category")
        self._client.update_submission(
            case_id=case_id,
            submission_id=submission_id,
            deficiency_notice_params=json.dumps(json_data),
        )
        if errors:
            return self.get(
                request, case_id, submission_id=submission_id, product_id=None, errors=errors
            )

        response = self._client.submit_product_information(
            organisation_id=organisation_id,
            case_id=case_id,
            sector_id=request.POST.get("sector"),
            description=request.POST.get("description"),
            product_id=product_id,
            hs_codes=hs_codes,
            name=request.POST.get("product_name"),
        )
        if request.POST.get("btn-action") == "add":
            return redirect(f"/case/{case_id}/submission/{submission_id}/product/")
        return redirect(f"/case/{case_id}/submission/{submission_id}")


class SourceView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    """
    Export Sources
    """

    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "cases/submissions/application/source.html"
    case_page = True

    def get(
        self,
        request,
        case_id=None,
        submission_id=None,
        export_source_id=None,
        options=None,
        reference_case=None,
        *args,
        **kwargs,
    ):
        # We need to work out if the user needs to select a case
        # (for reviews, new exporter or refunds)
        # If so, we will need a case list.
        # If not, just have the original source page
        case_category = get(self.submission, "deficiency_notice_params/case_category")
        organisation_role = get(self.submission, "deficiency_notice_params/organisation_role")
        page = request.GET.get("page")
        notices = []
        if self._client.is_feature_flag_enabled("NOTICES"):
            notices = self._client.get_notices()
        if page != "source" and (
            (organisation_role and organisation_role != "producer") or case_category in ["review"]
        ):
            return render(
                request,
                self.template_name,
                {
                    "page": "case",
                    "notices": notices,
                    "case_category": case_category,
                    "organisation_role": get(
                        self.submission, "deficiency_notice_params/organisation_role"
                    ),
                    "reference_cases": self._client.get_cases(archived=True),
                    "case": self.case,
                    "submission": self.submission,
                    "case_id": self.case and self.case.get("id"),
                    "submission_id": self.submission and self.submission.get("id"),
                    "options": options,
                    "reference_case": reference_case,
                    "errors": kwargs.get("errors"),
                },
            )
        else:
            organisation_id = request.session.get("organisation_id")
            can_select_all = int(self.case["type"]["id"]) in ALL_COUNTRY_CASE_TYPES
            has_sources = False
            sources = self._client.get_source_of_exports(organisation_id, case_id)
            if sources:
                has_sources = True
            sources.append({})
            return render(
                request,
                self.template_name,
                {
                    "evidence_of_subsidy": self.case["evidence_of_subsidy"],
                    "case_id": case_id,
                    "case": self.case,
                    "submission": self.submission,
                    "sources": sources,
                    "notices": notices,
                    "can_select_all": can_select_all,
                    "has_sources": has_sources,
                    "countries": countries,
                    "submission_id": submission_id,
                    "errors": kwargs.get("errors"),
                    "org_indicator_type": self.org_indicator_type,
                },
            )

    def post(  # noqa: C901
        self, request, case_id=None, submission_id=None, export_source_id=None, *args, **kwargs
    ):

        page = request.POST.get("page")

        if page == "source":
            countries = request.POST.getlist("country")
            evidence_of_subsidy = request.POST.get("evidence_of_subsidy")
            action = request.POST.get("btn-action")
            remove = request.POST.get("btn-remove")
            sources = []
            if remove:
                sources = [{"id": remove}]
            elif countries:
                for value in countries:
                    if value:
                        if value == "ALL":
                            sources = ["ALL"]
                            break
                        sources.append({"country": value})
            if sources:
                organisation_id = request.session.get("organisation_id")
                response = self._client.submit_source_of_exports_public(
                    organisation_id=organisation_id,
                    case_id=case_id,
                    sources=sources,
                    evidence_of_subsidy=evidence_of_subsidy,
                )

            if action == "save_add" or remove:
                return redirect(f"/case/{case_id}/submission/{submission_id}/source/?page=source")
            else:
                return redirect(f"/case/{case_id}/submission/{submission_id}/")
        else:
            if request.POST.get("btn-action") == "no-js-save":
                # no JS, so we need to get the selected case and populate the review type options
                reference_case = request.POST.get("reference_case")
                options = self._client.available_review_types(reference_case)
                return self.get(
                    request,
                    case_id=case_id,
                    submission_id=submission_id,
                    export_source_id=export_source_id,
                    options=options,
                    reference_case=reference_case,
                )

            params = pluck(request.POST, ["reference_case", "review_type"])
            errors = validate(params, review_form_validators)
            if errors:
                return self.get(
                    request, case_id=case_id, submission_id=submission_id, errors=errors
                )
            result = self._client.set_review_type(
                submission_id=submission_id,
                case_id=case_id,
                reference_case=params.get("reference_case"),
                review_type=params.get("review_type"),
            )
            return redirect(f"/case/{case_id}/submission/{submission_id}/source/?page=source")


class AvailableReviewTypesView(
    LoginRequiredMixin, GroupRequiredMixin, TemplateView, TradeRemediesAPIClientMixin
):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]

    def get(self, request, case_id, *args, **kwargs):
        selected_case_type = request.GET.get("select")
        organisation_role = request.GET.get("organisation_role")
        is_notice = request.GET.get("is_notice", False)
        results = self.client(request.user).available_review_types(case_id, is_notice=is_notice)
        return render(
            request,
            "cases/submissions/application/review_types.html",
            {
                "selected_case_type": selected_case_type,
                "organisation_role": organisation_role,
                "options": results,
            },
        )


class SubmissionMetaView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    case_page = True
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]

    def name_sort(context, obj):
        return obj.get("name", "")

    def get(
        self, request, case_id=None, submission_id=None, submission_type_id=None, *args, **kwargs
    ):
        case_id = case_id or request.GET.get("case_id")
        self.populate_objects(request, case_id, submission_type_id, submission_id)
        template_key = self.submission_type["key"]
        template_name = f"cases/submissions/{template_key}/meta.html"
        form_action = "/case/interest/"
        if case_id:
            form_action = f"{form_action}{case_id}/"
        if submission_id and case_id:
            form_action = f"{form_action}{submission_id}/"
        enums = self._client.get_all_case_enums(case_id=case_id)
        # Get only the submission types in the adhoc family that are public->tra or both directions
        available_submission_types = [
            sub_type
            for sub_type in enums["submission_types"]
            if sub_type["direction"] in (DIRECTION_BOTH, DIRECTION_PUBLIC_TO_TRA)
            and sub_type["key"] in ("adhoc",)
            and (
                not sub_type.get("requires")
                or enums.get("available_submission_types", {}).get(str(sub_type["id"]))
            )
        ]
        has_general = any([st["id"] == SUBMISSION_TYPE_ADHOC for st in available_submission_types])
        if not has_general:
            available_submission_types.append(
                {
                    "id": SUBMISSION_TYPE_ADHOC,
                    "key": "adhoc",
                    "name": "General",
                    "direction": 1,
                    "requires": None,
                    "has_requirement": True,
                    "notify_template": "NOTIFY_AD_HOC_EMAIL",
                }
            )
        return render(
            request,
            template_name,
            {
                "submission": self.submission,
                "submission_type": self.submission_type,
                "case_id": case_id,
                "submission_id": submission_id,
                "organisation_id": self.organisation_id,
                "org_indicator_type": self.org_indicator_type,
                "submission_types": available_submission_types,
            },
        )

    def post(
        self, request, case_id=None, submission_id=None, submission_type_id=None, *args, **kwargs
    ):
        submission_name = request.POST.get("submission_name")
        submission_type_id = request.POST.get("submission_type_id", submission_type_id)
        self.populate_objects(request, case_id, submission_type_id, submission_id)
        if submission_name:
            if not self.submission:
                # We need to create the submission here and add the name
                self.submission = self._client.create_submission(
                    case_id=self.case_id,
                    organisation_id=self.organisation_id,
                    submission_type=self.submission_type_id,
                    name=submission_name,
                )["submission"]
                self.submission_id = self.submission["id"]
            else:
                data = {"name": submission_name, "submission_type_id": submission_type_id}
                self._client.update_submission_public(
                    case_id=self.case_id,
                    organisation_id=self.organisation_id,
                    submission_id=self.submission_id,
                    data=data,
                    **kwargs,
                )
            return redirect(f"/case/{self.case_id}/submission/{self.submission_id}/")

        return redirect(
            f"/case/{self.case_id}/organisation/{self.organisation_id}/submission/create/"
        )


class ApplicationFormsView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    case_page = True

    def get(self, request, case_id=None, submission_id=None, document_type=None, *args, **kwargs):
        if document_type not in ("deficiency", "caseworker"):
            document_type = "caseworker"
        self.setup_request(request, case_id=case_id)
        submission = self._client.get_submission_public(case_id, submission_id)
        organisation_id = submission["organisation"]["id"]
        case = submission.get("case")
        template_grp = submission["type"]["key"]
        submission_docs = self.get_submission_documents(request_for_sub_org=True)
        documents = submission_docs.get(document_type, [])
        template_postfix = "_deficiency" if document_type == "deficiency" else ""
        template_name = f"cases/submissions/{template_grp}/download{template_postfix}.html"
        return render(
            request,
            template_name,
            {
                "case_id": case_id,
                "case": case,
                "organisation_id": organisation_id,
                "submission_id": submission_id,
                "submission": submission["previous_version"]
                if document_type == "deficiency"
                else submission,
                "download_template": f"{template_grp}/download.html",
                "documents": documents,
                "org_indicator_type": self.org_indicator_type,
            },
        )

    def post(self, request, case_id=None, submission_id=None, *args, **kwargs):
        request.session["application"]["download"] = "COMPLETE"
        request.session.modified = True
        return redirect(f"/case/{case_id}/submission/{submission_id}/")


class UploadDocumentsView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    """
    Submission document upload
    """

    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    case_page = True

    def get(
        self,
        request,
        case_id=None,
        submission_id=None,
        submission_type_id=None,
        public_str=None,
        *args,
        **kwargs,
    ):
        public = public_str == "public"
        if submission_id:
            submission = self._client.get_submission_public(case_id, submission_id)
            organisation_id = submission.get("organisation", {}).get("id")
        else:
            submission_type = self._client.get_submission_type(submission_type_id)
            submission = {"type": submission_type}
            organisation_id = request.session["organisation_id"]

        case = self._client.get_case(case_id=case_id, organisation_id=organisation_id)
        template_grp = submission["type"]["key"]
        public_url_str = ("_" + public_str) if public_str else ""
        template_name = f"cases/submissions/{template_grp}/upload{public_url_str}.html"

        all_documents = self.submission.get("documents", [])
        respondant_docs = deep_index_items_by(all_documents, "is_tra").get("false", [])
        documents, doc_idx = structure_documents(respondant_docs)
        # Flag a document that's just been added so the pair can be shown in green rather than grey.
        new_document = first(doc_idx.get(request.GET.get("new", "")))
        if new_document:
            parent_id = new_document.get("parent_id")
            if parent_id:
                new_document = first(doc_idx.get(parent_id))

        return render(
            request,
            template_name,
            {
                "all_organisations": template_grp in SUBMISSION_TYPE_ALL_ORGANISATIONS,
                "case": case,
                "case_id": case_id,
                "submission_id": submission_id,
                "organisation_id": organisation_id,
                "submission": submission,
                "new_document": new_document,
                "documents": documents,
                "public": public,
                "public_str": public_str,
                "submission_document_type": "loa" if public_str == "loa" else None,
                "org_indicator_type": self.org_indicator_type,
                "message": request.GET.get("message"),
                "error": request.GET.get("error"),
            },
        )

    def post(
        self,
        request,
        case_id=None,
        submission_id=None,
        submission_type_id=None,
        public_str=None,
        *args,
        **kwargs,
    ):
        redirect_path = request.POST.get("redirect")
        public = public_str == "public"
        documents = self.submission.get("documents", [])
        new_documents = []
        self.populate_objects(request, case_id, None, submission_id)
        self.clear_docs_reviewed()
        if request.FILES:
            replace_id = request.POST.get("replace-file")
            if replace_id:
                response = self._client.remove_document(
                    organisation_id=self.organisation_id,
                    case_id=case_id,
                    submission_id=submission_id,
                    document_id=replace_id,
                )
            try:
                for _file in request.FILES.getlist("file"):
                    _file.readline()  # Important, will raise VirusFoundInFileException if infected
                    original_file_name = _file.original_name
                    data = {
                        "name": "Uploaded from UI",
                        "submission_type_id": submission_type_id,
                        "confidential": not public,
                        "parent_id": request.POST.get("parent_id"),
                        "replace_id": request.POST.get("replace_id"),
                        "document_name": original_file_name,
                        "file_name": _file.name,
                        "file_size": _file.file_size,
                        "submission_document_type": request.POST.get("submission_document_type"),
                    }
                    new_documents.extend(
                        self._client.upload_document(
                            organisation_id=self.organisation_id,
                            case_id=case_id,
                            submission_id=submission_id,
                            data=data,
                        )
                    )
            except (VirusFoundInFileException, APIException) as e:
                if isinstance(e, VirusFoundInFileException):
                    msg = "File upload aborted, malware detected in file!"
                else:
                    msg = str(e)
                return redirect(f"/case/{case_id}/submission/{submission_id}/upload/?error={msg}")
        self._client.set_submission_status_public(case_id, submission_id, status_context="draft")
        new_docs = new_documents[0].get("id") if new_documents else None
        if redirect_path:
            return redirect(f"{redirect_path}?new={new_docs}")
        return redirect(f"/case/{case_id}/submission/{submission_id}/upload/?new={new_docs}")


class RemoveDocumentView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "cases/upload.html"

    def post(self, request, case_id=None, submission_id=None, document_id=None, *args, **kwargs):
        redirect_path = request.POST.get("redirect")
        self.populate_objects(request, case_id, None, submission_id)
        self.clear_docs_reviewed()
        # organisation_id = this.submission.get('organisation', {}).get('id')
        # or request.session['organisation_id']
        if case_id and submission_id and document_id:
            response = self._client.remove_document(
                organisation_id=self.organisation_id,
                case_id=case_id,
                submission_id=submission_id,
                document_id=document_id,
            )

            self._client.set_submission_status_public(
                case_id, submission_id, status_context="draft"
            )
            if response:
                if redirect_path:
                    feedback_message = "Document(s) deleted"
                    return internal_redirect(
                        f"{redirect_path}?message={feedback_message}", "/dashboard/"
                    )
                else:
                    return redirect(f"/case/{case_id}/submission/{submission_id}/upload/")
            else:
                documents = self._client.get_documents(self.organisation_id, case_id, submission_id)
                return render(
                    request,
                    self.template_name,
                    {
                        "case_id": case_id,
                        "submission_id": submission_id,
                        "documents": documents,
                        "errors": response,
                    },
                )


class ReviewView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]

    case_page = True

    def get(self, request, case_id=None, submission_id=None, *args, **kwargs):
        submission = self._client.get_submission_public(
            case_id=case_id, submission_id=submission_id
        )
        template_grp = submission["type"]["key"]
        template_name = f"cases/submissions/{template_grp}/review.html"

        return render(
            request,
            template_name,
            {
                "case_id": case_id,
                "case": self.case,
                "submission_id": str(submission_id),
                "current_organisation": self.organisation,
                "org_indicator_type": self.org_indicator_type,
                "errors": kwargs.get("errors"),
            },
        )

    def post(self, request, case_id=None, submission_id=None, *args, **kwargs):
        if not self.organisation:
            self.organisation = self.submission.get("organisation", {})
        review = request.POST.get("review")
        errors = {}
        if request.POST.get("review") == "required":
            errors["review"] = "You must check the 'Review' box"
        if errors:
            return self.get(request, case_id, submission_id, errors=errors)

        self._client.set_review_flag(self.organisation["id"], case_id, submission_id, bool(review))
        return redirect(f"/case/{case_id}/submission/{submission_id}/")


class ReviewDocumentsView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    """
    Review submission confidential and non confidential documents
    """

    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    case_page = True

    def name_sort(context, obj):
        return obj.get("name", "")

    def get(self, request, case_id=None, submission_id=None, errors=None, *args, **kwargs):
        organisation_id = self.submission["organisation"]["id"]
        table = []
        if self.submission:
            template_grp = self.submission["type"]["key"]

            self.template_name = f"cases/submissions/{template_grp}/review_documents.html"
        all_documents = self.submission.get("documents", [])
        respondant_docs = deep_index_items_by(all_documents, "is_tra").get("false", [])
        documents, doc_idx = structure_documents(respondant_docs)
        return render(
            request,
            self.template_name,
            {
                "case_id": case_id,
                "case": self.case,
                "submission": self.submission,
                "organisation_id": organisation_id,
                "submission_id": submission_id,
                "documents": documents,
                "org_indicator_type": self.org_indicator_type,
                "errors": errors,
            },
        )

    def post(self, request, case_id=None, submission_id=None, *args, **kwargs):
        reviewed = request.POST.get("documents_reviewed")
        organisation_id = self.submission["organisation"]["id"]
        docs_reviewed = timezone.now() if reviewed else ""
        if docs_reviewed:
            response = self._client.update_submission_public(
                case_id=case_id,
                organisation_id=organisation_id,
                submission_id=submission_id,
                data={"doc_reviewed_at": docs_reviewed},
            )
            return redirect(f"/case/{case_id}/submission/{submission_id}/")
        else:
            errors = {
                "documents_reviewed": "You must check the box to indicate that you have reviewed the documents."  # noqa: E501
            }
            return self.get(request, case_id=case_id, submission_id=submission_id, errors=errors)


class SubmitApplicationView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    case_page = True

    def get(self, request, case_id=None, submission_id=None, *args, **kwargs):
        case = self._client.get_case(case_id=case_id)
        organisation_id = request.session.get("organisation_id")
        submission = self._client.get_submission_public(case_id, submission_id, organisation_id)
        template_name = f"cases/submissions/{submission['type']['key']}/submit.html"
        errors = kwargs.get("errors")
        context = {
            "case_id": case_id,
            "case": case,
            "submission": submission,
            "template_name": template_name,
            "submission_id": submission_id,
            "org_indicator_type": self.org_indicator_type,
            "errors": errors,
            **self.get_submission_context(),
        }
        if errors:
            context["non_conf"] = request.POST.get("non_conf")
            context["confirm"] = request.POST.get("confirm")

        return render(request, template_name, context)

    def post(self, request, case_id=None, submission_id=None, *args, **kwargs):
        errors = {}
        if not request.POST.get("confirm"):
            errors["confirm"] = "You must confirm your authority"
        if not request.POST.get("non_conf"):
            errors["non_conf"] = "You must include non-confidential documents"
        if errors:
            return self.get(request, case_id, submission_id, errors=errors)

        self._client.set_submission_status_public(case_id, submission_id, status_context="received")
        # trigger the on_submit event handler for this submission's helper, if applicable
        redirect_url = self.on_submission_submit()
        # If user does not have access to case (eg registration of interest),
        # don't go to the case, but the dashboard instead
        if redirect_url:
            return redirect(redirect_url)
        elif self._client.get_user_case_organisations(case_id):
            return redirect(f"/case/{case_id}/submission/{submission_id}/submitted/")
        else:
            return redirect("/dashboard/")


class RemoveSubmissionView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]

    def post(self, request, case_id, submission_id, *args, **kwargs):
        submission = self._client.get_submission_public(
            case_id=case_id, submission_id=submission_id
        )
        redirect_to = request.POST.get("redirect")
        organisation_id = submission["organisation"]["id"]
        res = self._client.remove_submission(case_id, organisation_id, submission_id)
        redirect_to = redirect_to or f"/case/{case_id}/"
        if res and res.get("deleted"):
            redirect_to += "?alert=cancel_sub"
        else:
            redirect_to += "?error=cancel_fail"
        return redirect(redirect_to)


class DocumentDownloadView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]

    def get(self, request, case_id, submission_id, document_id, *args, **kwargs):
        submission = self._client.get_submission_public(
            case_id=case_id, submission_id=submission_id
        )
        organisation_id = submission["organisation"]["id"]

        document = self._client.get_document_download_url(document_id, submission_id=submission_id)
        return redirect(document.get("download_url"))


class DocumentDownloadStreamView(
    LoginRequiredMixin, GroupRequiredMixin, TemplateView, TradeRemediesAPIClientMixin
):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]

    def get(self, request, case_id, submission_id, document_id, *args, **kwargs):
        client = self.client(request.user)
        submission = client.get_submission_public(case_id=case_id, submission_id=submission_id)
        organisation_id = submission["organisation"]["id"]
        if str(submission.get("case", {}).get("id")) != str(case_id):
            raise APIException("Invalid request parameters")
        document = client.get_document(document_id, case_id, submission_id)
        document_stream = client.get_document_download_stream(
            document_id=document_id, submission_id=submission_id, organisation_id=organisation_id
        )

        return proxy_stream_file_download(document_stream, document["name"])


class CreateSubmissionView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "cases/tasklist.html"

    def get(
        self, request, case_id=None, organisation_id=None, submission_type_id=None, *args, **kwargs
    ):
        submission_type_id = submission_type_id or SUBMISSION_TYPE_ADHOC
        submission_type = self._client.get_submission_type(submission_type_id)
        template_key = submission_type["key"]
        template_name = f"cases/submissions/{template_key}/tasklist.html"
        return render(
            request,
            template_name,
            {
                "case_id": case_id,
                "upload_template": f"{template_key}/upload.html",
                "current_organisation": self.organisation,
                "submission_type": submission_type,
                "submission_type_id": submission_type_id,
                "tasklist_template": f"{template_key}/tasklist.html",
            },
        )


class SelectCaseView(
    LoginRequiredMixin, GroupRequiredMixin, TemplateView, TradeRemediesAPIClientMixin
):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "cases/select_case.html"

    def get(self, request, *args, **kwargs):
        redirect_key, redirect_kwargs = parse_redirect_params(request.GET.get("redirect"))
        redirect_url = reverse(redirect_key, kwargs=redirect_kwargs)
        if "/interest/" in redirect_url:
            param = "registration-of-interest"
        else:
            param = "all"
        cases = self.client(request.user).get_all_cases(param)
        return render(request, self.template_name, {"cases": cases, "redirect": redirect_url})


class SelectOrganisationCaseView(
    LoginRequiredMixin, GroupRequiredMixin, TemplateView, TradeRemediesAPIClientMixin
):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "cases/select_org_case.html"

    def get(self, request, for_user_id=None, *args, **kwargs):
        interests = request.GET.get("interests", "true") == "true"
        for_user = for_user_id or request.GET.get("for")
        redirect_key, redirect_kwargs = parse_redirect_params(request.GET.get("redirect"))
        redirect_url = reverse(redirect_key, kwargs=redirect_kwargs)
        organisation_id = request.user.organisation["id"]
        user_case_ids = {}
        client = self.client(request.user)
        if for_user:
            assign_user = client.get_user(user_id=for_user, organisation_id=organisation_id)
            user_cases = client.get_user_cases(request_for=for_user)
            for user_case in user_cases:
                for org in user_case.get("user_organisations"):
                    uc_id = user_case.get("id") + ":" + org.get("id")
                    user_case_ids[uc_id] = True
        cases = client.get_organisation_cases(
            organisation_id, initiated_only=False, all_cases=True, outer=True
        )
        if interests:
            all_interests = client.get_registration_of_interest(all_interests=True)
            for interest in all_interests:
                cases.append(
                    {
                        "interest": True,
                        "case": interest.get("case"),
                        "organisation": interest.get("organisation"),
                    }
                )
        return render(
            request,
            self.template_name,
            {
                "cases": cases,
                "user_case_ids": user_case_ids,
                "redirect": redirect_url,
                "assign_user": assign_user,
                "organisation_id": organisation_id,
                "back_url": f"/accounts/team/assign/{for_user}/",
            },
        )


class CaseReviewView(LoginRequiredMixin, GroupRequiredMixin, TemplateView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "reviews/main.html"


class CaseInviteView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER]
    template_name = "cases/submissions/invite/tasklist.html"

    def get(self, request, case_id=None, submission_id=None, *args, **kwargs):
        invites = []
        invitee_name = None
        documents = []
        if self.submission:
            invites = self._client.get_third_party_invites(case_id, self.submission["id"])
            if invites:
                invitee = invites[0]
                invitee_name = invitee["contact"]["name"]
            documents = self.get_submission_documents()
        return render(
            request,
            self.template_name,
            {
                "errors": kwargs.get("errors"),
                "current_page_name": "Invite 3rd party",
                "all_organisations": True,
                "case_id": self.case_id,
                "submission_id": self.submission_id,
                "case": self.case,
                "submission": self.submission,
                "invites": invites,
                "organisation": request.user.organisation,
                "organisation_name": request.user.organisation.get("name", "unknown"),
                "documents": documents,
                "application": request.session.get("application", "unknown"),
                "invitee_name": invitee_name,
            },
        )


class CaseInvitePeopleView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER]
    template_name = "cases/submissions/invite/invites.html"

    def get(self, request, case_id=None, submission_id=None, *args, **kwargs):
        contact = {}
        session_data = request.session.get("invite_form_data", {})
        uk_company = non_uk_company = False  # initial state
        if self.submission:
            invites = self._client.get_third_party_invites(case_id, self.submission["id"])
            contact = invites[0].get("contact") if invites else {"organisation": {"country": {}}}
            org_country_code = contact["organisation"]["country"].get("code")
            contact["organisation"]["country_code"] = org_country_code  # bubble up for convenience
            # Prep which radio button checked
            uk_company = org_country_code == "GB"
            non_uk_company = not uk_company
        else:
            # Use what we have in the session
            contact["name"] = session_data.get("name")
            contact["email"] = session_data.get("email")
            contact["organisation"] = {}
            contact["organisation"]["name"] = session_data.get("organisation_name")
            contact["organisation"]["address"] = session_data.get("organisation_address")
            contact["organisation"]["companies_house_id"] = session_data.get("companies_house_id")
            if country_code := session_data.get("country_code"):
                # A country was stashed in the session
                contact["organisation"]["country_code"] = country_code
                uk_company = country_code == "GB"
                non_uk_company = not uk_company
            elif uk_company_choice := session_data.get("uk_company_choice"):
                # No country, but we stashed a uk/non uk company choice
                uk_company = uk_company_choice == "uk_company"
                non_uk_company = not uk_company

        form_data = {
            "errors": kwargs.get("errors"),
            "current_page_name": "Invite 3rd party",
            "submission_type_key": "invite",
            "all_organisations": True,
            "case_id": self.case_id,
            "submission_id": self.submission_id,
            "case": self.case,
            "submission": self.submission,
            "inviting_organisation": request.user.organisation,
            "contact": contact,
            "uk_company": uk_company,
            "non_uk_company": non_uk_company,
            "countries": countries,
        }
        return render(request, self.template_name, form_data)

    def post(self, request, case_id, submission_id=None, *args, **kwargs):
        data = {
            "name": request.POST.get("name"),
            "email": request.POST.get("email"),
            "uk_company_choice": request.POST.get("uk_company_choice"),
        }
        request.session["invite_form_data"] = data
        request.session.modified = True
        errors = {}
        if not data.get("uk_company_choice"):
            # Only makes sense to deliver this one error at this point
            errors["uk_company_choice"] = "You must select an option"
            return self.get(request, case_id, submission_id=None, errors=errors)

        validations = third_party_validators_base.copy()
        # Pick out posted data based on uk company choice and set appropriate validations
        if data.get("uk_company_choice") == "uk_company":
            data["organisation_name"] = request.POST.get("organisation_name_uk")
            data["organisation_address"] = request.POST.get("organisation_address_uk")
            data["companies_house_id"] = request.POST.get("companies_house_id_uk")
            data["country_code"] = "GB"
            validations.extend(third_party_validators_uk.copy())
        else:
            data["organisation_name"] = request.POST.get("organisation_name_non_uk")
            data["organisation_address"] = request.POST.get("organisation_address_non_uk")
            data["companies_house_id"] = request.POST.get("companies_house_id_non_uk")
            data["country_code"] = request.POST.get("country_code")
            validations.extend(third_party_validators_non_uk.copy())
        errors = validate(data, validations)

        # Cannot invite a company member as a third party
        if data.get("organisation_name") == request.user.organisation.get("name"):
            msg = "Invalid company name: A third party cannot be from your organisation"
            errors["organisation_name"] = msg

        if errors:
            # Back to form for another go
            return self.get(request, case_id, submission_id=None, errors=errors)

        # Call API to create/update third party invite
        response = self._client.third_party_invite(
            case_id=case_id,
            organisation_id=request.user.organisation["id"],
            submission_id=submission_id,
            invite_params=data,
        )
        if not submission_id:
            submission_id = response.get("submission", {}).get("id")
        if submission_id:
            # We successfully created a submission, back to submission task list
            return redirect(f"/case/invite/{case_id}/submission/{submission_id}")
        else:
            # No submission, back to case page
            return redirect(f"/case/invite/{case_id}/")

    def delete(self, request, case_id, submission_id, invite_id, *args, **kwargs):
        self._client.remove_third_party_invite(case_id, submission_id, invite_id)
        return redirect(f"/case/invite/{case_id}/{submission_id}/people/")


class SetPrimaryContactView(LoginRequiredMixin, GroupRequiredMixin, BasePublicView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER]

    def post(self, request, case_id, organisation_id, *args, **kwargs):
        contact_id = request.POST.get("contact_id")
        self._client.set_case_primary_contact(
            contact_id=contact_id, organisation_id=organisation_id, case_id=case_id
        )
        return redirect(
            f"/case/{case_id}/?tab=case_members&organisation_id={organisation_id}&alert=primary-contact-updated"  # noqa: E501
        )
