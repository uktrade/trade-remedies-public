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
    ExistingClientForm, NonUkEmployerForm, \
    PrimaryContactForm, UkEmployerForm, YourEmployerForm
from trade_remedies_public.cases.utils import get_org_parties
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

        # Creating the registration of interest
        new_submission = self.client.post(
            self.client.url("submissions"),
            data={
                "case": case_id,
                "type": SUBMISSION_TYPE_REGISTER_INTEREST,
                "documents": [],
                "created_by": self.request.user.id
            }
        )

        # REDIRECT to next stage
        return redirect(reverse(
            "interest_case_submission_created",
            kwargs={
                "case_id": case_id,
                "submission_id": new_submission["id"]
            }
        ))


class InterestStep2BaseView(LoginRequiredMixin, GroupRequiredMixin, APIClientMixin, FormView):
    def dispatch(self, request, *args, **kwargs):
        self.edit_submission_id = request.GET.get("submission_id", None)
        return super().dispatch(request, *args, **kwargs)

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.request.GET)
        # a list of dictionaries
        existing_clients_list = get_org_parties(
            TradeRemediesAPIClientMixin.client(self, self.request.user), self.request.user
        )
        context["existing_clients"] = True if existing_clients_list else False
        return context

    def form_valid(self, form):
        submission_id = self.kwargs["submission_id"]
        if form.cleaned_data.get("org") == "new-org":
            return redirect(
                reverse("interest_primary_contact", kwargs={"submission_id": submission_id})
            )
        elif form.cleaned_data.get("org") == "my-org":
            submission = self.client.put(
                self.client.url(
                    f"submissions/{submission_id}/add_organisation_to_registration_of_interest"
                ),
                data={
                    "organisation_id": self.request.user.organisation["id"]
                }
            )
            return redirect(reverse(
                "interest_case_submission_created",
                kwargs={
                    "case_id": submission["case"]["id"],
                    "submission_id": submission_id
                }
            ))

        elif form.cleaned_data.get("org") == "existing-org":
            return redirect(
                reverse("interest_existing_client", kwargs={"submission_id": submission_id})
            )


class InterestPrimaryContactStep2(InterestStep2BaseView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "v2/registration_of_interest/primary_client_contact.html"
    form_class = PrimaryContactForm

    def form_valid(self, form):
        submission_id = self.kwargs["submission_id"]
        response = TradeRemediesAPIClientMixin.client(self, self.request.user).create_contact(
            {
                "contact_email": form.cleaned_data.get("email"),
                "contact_name": form.cleaned_data.get("name"),
            }
        )
        contact_id = response["id"]
        # organisation_id only exists if registering ROI for existing client
        organisation_id = self.kwargs.get("organisation_id", None)
        if organisation_id:
            submission = self.client.put(
                self.client.url(
                    f"submissions/{submission_id}/add_organisation_to_registration_of_interest"
                ),
                data={
                    "organisation_id": organisation_id,
                    "contact_id": contact_id,
                }
            )
            return redirect(reverse(
                "interest_case_submission_created",
                kwargs={
                    "case_id": submission["case"]["id"],
                    "submission_id": submission["id"]
                }
            ))
        else:
            return redirect(reverse(
                "interest_ch",
                kwargs={
                    "submission_id": submission_id,
                    "contact_id": contact_id
                }
            ))


class InterestUkRegisteredYesNoStep2(InterestStep2BaseView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "v2/registration_of_interest/is_client_uk_company.html"
    form_class = YourEmployerForm

    def form_valid(self, form):
        context = self.get_context_data()
        contact_id = context["contact_id"]
        submission_id = self.kwargs["submission_id"]
        if form.cleaned_data.get("uk_employer") == "yes":
            return redirect(
                reverse("interest_ch_yes", kwargs={
                    "submission_id": submission_id,
                    "contact_id": contact_id
                })
            )
        elif form.cleaned_data.get("uk_employer") == "no":
            return redirect(
                reverse("interest_ch_no", kwargs={
                    "submission_id": submission_id,
                    "contact_id": contact_id
                })
            )


class InterestNonUkRegisteredStep2(InterestStep2BaseView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "v2/registration_of_interest/your_client_details.html"
    form_class = NonUkEmployerForm

    def form_valid(self, form):
        submission_id = self.kwargs["submission_id"]
        contact_id = self.kwargs["contact_id"]
        return redirect(
            f"/case/interest/{submission_id}/{contact_id}/submit/?name="
            f"{form.cleaned_data.get('organisation_name')}&companies_house_id="
            f"{form.cleaned_data.get('company_number')}&"
            f"post_code={form.cleaned_data.get('post_code')}&non_uk_registered=true&"
            f"address={form.cleaned_data.get('address_snippet')}&"
            f"country={form.cleaned_data.get('country')}"  # noqa: E501
        )


class InterestIsUkRegisteredStep2(InterestStep2BaseView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "v2/registration_of_interest/who_you_representing.html"
    form_class = UkEmployerForm

    def form_valid(self, form):
        submission_id = self.kwargs["submission_id"]
        contact_id = self.kwargs["contact_id"]
        return redirect(
            f"/case/interest/{submission_id}/{contact_id}/submit/?name="
            f"{form.cleaned_data.get('organisation_name')}&"
            f"companies_house_id={form.cleaned_data.get('companies_house_id')}&"
            f"post_code={form.cleaned_data.get('organisation_post_code')}&"
            f"address={form.cleaned_data.get('organisation_address')}"  # noqa: E501
        )


class InterestUkSubmitStep2(InterestStep2BaseView):
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
        submission_id = self.kwargs["submission_id"]
        contact_id = self.kwargs["contact_id"]

        # Creating the new organisation
        organisation = self.client.post(
            self.client.url("organisations"),
            data={
                **self.request.GET,
                **form.cleaned_data
            }
        )

        # Associating the ROI with the organisation
        submission = self.client.put(
            self.client.url(
                f"submissions/{submission_id}/add_organisation_to_registration_of_interest"
            ),
            data={
                "organisation_id": organisation["id"],
                "contact_id": contact_id,
            }
        )

        # Return to task list
        return redirect(reverse(
            "interest_case_submission_created",
            kwargs={
                "case_id": submission["case"]["id"],
                "submission_id": submission["id"]
            }
        ))


class InterestExistingClientStep2(InterestStep2BaseView):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]
    template_name = "v2/registration_of_interest/who_you_representing_existing.html"
    form_class = ExistingClientForm

    def get_existing_clients(self):
        org_parties = get_org_parties(TradeRemediesAPIClientMixin.client(self, self.request.user),
                                      self.request.user)
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
        return redirect(reverse("interest_existing_client_primary_contact", kwargs={
            "submission_id": self.kwargs["submission_id"],
            "organisation_id": form.cleaned_data.get("org")
        }))


class RegistrationOfInterest4(TemplateView, APIClientMixin):
    template_name = "v2/registration_of_interest/registration_of_interest_4.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["submission"] = self.client.get_submission(kwargs["submission_id"])
        return context

    def post(self, request, submission_id, **kwargs):
        if request.POST.get("authorised", None) == "yes":
            submission = self.get_context_data(submission_id=submission_id)["submission"]

            # First we need to update the relevant OrganisationCaseRole object to AWAITING_APPROVAL
            organisation_case_role = self.client.get(
                self.client.url(
                    "organisation_case_roles",
                    case_id=submission["case"]["id"],
                    organisation_id=submission["organisation"]["id"]
                )
            )
            self.client.put(
                self.client.url(f"organisation_case_roles/{organisation_case_role['id']}"),
                data={
                    "role_key": "awaiting_approval"
                }
            )

            # Now we update the status of the submission to received
            self.client.update_submission_status(submission_id=submission_id, new_status="received")
        else:
            pass
        return redirect(reverse("roi_complete", kwargs={"submission_id": submission_id}))


class RegistrationOfInterestComplete(
    LoginRequiredMixin,
    APIClientMixin,
    TemplateView
):
    template_name = "v2/registration_of_interest/registration_of_interest_complete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["submission"] = self.client.get(
            self.client.url(f"submissions/{self.kwargs['submission_id']}")
        )
        return context
