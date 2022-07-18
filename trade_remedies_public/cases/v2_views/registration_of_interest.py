import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import FormView, TemplateView
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
from v2_api_client.mixins import APIClientMixin

from trade_remedies_public.cases.constants import SUBMISSION_TYPE_REGISTER_INTEREST
from trade_remedies_public.cases.forms import ClientFurtherDetailsForm, ClientTypeForm, \
    NonUkEmployerForm, \
    PrimaryContactForm, UkEmployerForm, YourEmployerForm
from trade_remedies_public.config.constants import SECURITY_GROUP_ORGANISATION_OWNER, \
    SECURITY_GROUP_ORGANISATION_USER
from trade_remedies_public.core.base import GroupRequiredMixin


class RegistrationOfInterest1(LoginRequiredMixin, TemplateView, APIClientMixin):
    template_name = "v2/registration_of_interest/registration_of_interest_1.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cases = self.client.get_cases(open_to_roi=True)
        if not cases:
            self.request.session["form_errors"] = {}
            self.request.session["form_errors"]["error_summaries"] = [
                ["table-header", "There are no active cases to join"]
            ]
        context["cases"] = cases
        return context

    def post(self, request, *args, **kwargs):
        case_information = request.POST["case_information"].split("*-*")
        case_reference = case_information[0]
        case_id = case_information[1]
        case_name = case_information[2]
        case_registration_deadline = case_information[3]

        if datetime.datetime.strptime(
                case_registration_deadline, "%Y-%m-%dT%H:%M:%S%z"
        ) < timezone.now() and not request.POST.get("confirmed_okay_to_proceed"):
            return render(
                request,
                "v2/registration_of_interest/registration_of_interest_late_registration.html",
                context={
                    "case_registration_deadline": case_registration_deadline,
                    "case_name": case_name,
                    "case_reference": case_reference,
                    "case_id": case_id,
                    "case_information": request.POST["case_information"],
                },
            )

        """# Creating the registration of interest
        new_submission = self.client.create_submission(
            case=case_id,
            type=SUBMISSION_TYPE_REGISTER_INTEREST,
            organisation=request.user.contact["organisation"]["id"],
            contact=request.user.contact["id"],
            documents=[],
        )"""

        # REDIRECT to next stage
        return redirect(reverse(
            "interest_case",
            kwargs={
                "case_id": case_id
            }
        ))


class InterestStep2BaseView(LoginRequiredMixin, GroupRequiredMixin, FormView):
    def form_invalid(self, form):
        form.assign_errors_to_request(self.request)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.kwargs)
        return context


class InterestClientTypeStep2(InterestStep2BaseView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "v2/registration_of_interest/who_is_registering.html"
    form_class = ClientTypeForm

    def form_valid(self, form):
        case_id = self.get_context_data()["case_id"]
        if form.cleaned_data.get("org") == "new-org":
            return redirect(f"/case/interest/{case_id}/contact/")  # noqa: E501


class InterestPrimaryContactStep2(TradeRemediesAPIClientMixin, InterestStep2BaseView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "v2/registration_of_interest/primary_client_contact.html"
    form_class = PrimaryContactForm

    def form_valid(self, form):
        case_id = self.get_context_data()["case_id"]
        response = self.client(self.request.user).create_contact(
            {
                "contact_email": form.cleaned_data.get("email"),
                "contact_name": form.cleaned_data.get("name"),
            }
        )
        contact_id = response["id"]
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


class RegistrationOfInterest4(TemplateView, APIClientMixin):
    template_name = "v2/registration_of_interest/registration_of_interest_4.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["submission"] = self.client.get_submission(kwargs["submission_id"])
        return context

    def post(self, request, submission_id, **kwargs):
        self.client.update_submission_status(submission_id, "received")
