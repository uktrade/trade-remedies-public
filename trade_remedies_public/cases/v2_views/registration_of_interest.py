import datetime

from apiclient.exceptions import ClientError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import FormView, TemplateView
from django.views.generic.base import View
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
from v2_api_client.mixins import APIClientMixin

from cases.constants import SUBMISSION_TYPE_REGISTER_INTEREST
from cases.utils import get_org_parties
from cases.v2_forms.registration_of_interest import (
    ClientFurtherDetailsForm,
    ClientTypeForm,
    ExistingClientForm,
    NonUkEmployerForm,
    PrimaryContactForm,
    RegistrationOfInterest4Form,
    UkEmployerForm,
    YourEmployerForm,
)
from config.base_views import TaskListView
from config.constants import SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER
from config.utils import (
    add_form_error_to_session,
    get_loa_document_bundle,
    get_uploaded_loa_document,
)
from core.base import GroupRequiredMixin


class RegistrationOfInterestBase(LoginRequiredMixin, GroupRequiredMixin, APIClientMixin, View):
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]

    def dispatch(self, request, *args, **kwargs):
        self.submission = {}
        if submission_id := self.kwargs.get("submission_id"):
            self.submission = self.client.submissions(submission_id)
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        form.assign_errors_to_request(self.request)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.kwargs)
        if self.submission:
            context["submission"] = self.submission
        return context

    def add_organisation_to_registration_of_interest(
        self, organisation_id: str, submission_id: str = None, contact_id: str = None
    ) -> dict:
        """
        Amends the organisation of a ROI submission object.
        Parameters
        ----------
        organisation_id : str - the UUID of the organisation object
        submission_id : str - UUID of the submission object, default to self.kwargs["submission"]
        contact_id : str - the UUID of the contact object you want to set as the primary of this
        org and this case. When representing your own org, this will be your contact object. But if
        you are representing someone else, this is the contact id of that contact

        Returns
        -------
        dict - a redirection to the tasklist loaded with the updated submission
        """
        submission_id = submission_id or self.kwargs.get("submission_id", None)
        if not submission_id:
            raise Exception("You need to provide a submission ID to amend")

        try:
            submission = self.client.submissions(
                submission_id
            ).add_organisation_to_registration_of_interest(
                organisation_id=organisation_id,
            )

            # Associate this contact with the organisation if there is no error
            self.client.contacts(contact_id).update({"organisation": organisation_id})
            # Add the contact as the invited contact to the submission
            self.client.submissions(submission_id).update({"primary_contact": contact_id})

            return redirect(
                reverse("roi_submission_exists", kwargs={"submission_id": submission["id"]})
            )
        except ClientError as exc:
            if exc.status_code == 409:
                # There is a conflict as an ROI with this case and organisation already exists
                return redirect(
                    reverse("roi_already_exists", kwargs={"submission_id": exc.message[0]["id"]})
                )
            raise exc


@method_decorator(never_cache, name="get")
class RegistrationOfInterestTaskList(RegistrationOfInterestBase, TaskListView):
    template_name = "v2/registration_of_interest/tasklist.html"

    def get_task_list(self):
        submission = getattr(self, "submission", {})

        steps = [
            {
                "heading": "Your case",
                "sub_steps": [
                    {
                        "link": reverse("roi_1"),
                        "link_text": "Select a Trade Remedies case",
                        "status": "Complete" if submission else "Not Started",
                        "ready_to_do": False if submission else True,
                    }
                ],
            },
            {
                "heading": "About you",
                "sub_steps": [
                    {
                        "link": reverse(
                            "interest_client_type", kwargs={"submission_id": submission["id"]}
                        )
                        if submission
                        else None,
                        "link_text": "Organisation details",
                        "status": "Complete"
                        if submission.get("contact") and submission["contact"].get("organisation")
                        else "Not Started",
                    }
                ],
            },
        ]

        registration_documentation_status_text = ""
        registration_documentation_status = "Not Started"
        if submission:
            # Each paired_document is a complete pair, so we multiply the count by 2 to get the
            # number of uploaded documents. Each orphaned_document is an incomplete pair.
            if documents_uploaded := (len(submission["paired_documents"]) * 2) + len(
                submission["orphaned_documents"]
            ):
                registration_documentation_status_text = f"Documents uploaded: {documents_uploaded}"
            else:
                registration_documentation_status_text = (
                    "Not Started" if submission.organisation else "Cannot Start Yet"
                )

            if submission["paired_documents"] and not submission["orphaned_documents"]:
                registration_documentation_status = "Complete"
            elif orphaned_documents := submission["orphaned_documents"]:
                registration_documentation_status = "Incomplete"
            else:
                registration_documentation_status = "Not Started"
        documentation_sub_steps = [
            {
                "link": reverse(
                    "roi_3_registration_documentation", kwargs={"submission_id": submission["id"]}
                )
                if submission
                else None,
                "link_text": "Registration documentation",
                "status": registration_documentation_status,
                "status_text": registration_documentation_status_text,
            }
        ]

        if (
            submission
            and submission.organisation
            and submission.organisation.id != self.request.user.contact["organisation"]["id"]
        ):
            # THe user is representing someone else, we should show the letter of authority
            documentation_sub_steps.append(
                {
                    "link": reverse("roi_3_loa", kwargs={"submission_id": submission["id"]}),
                    "link_text": "Letter of Authority",
                    "status": "Complete"
                    if get_uploaded_loa_document(self.submission)
                    else "Not Started",
                }
            )

        steps.append({"heading": "Documentation", "sub_steps": documentation_sub_steps})

        steps.append(
            {
                "heading": "Register interest",
                "sub_steps": [
                    {
                        "link": reverse("roi_4", kwargs={"submission_id": submission["id"]})
                        if submission
                        else None,
                        "link_text": "Check and submit",
                        "status": "Complete"
                        if submission.get("status", {}).get("locking") is True
                        else "Not Started",
                    }
                ],
            }
        )
        return steps

    def get(self, request, *args, **kwargs):
        if request.GET.get("confirm_access", False) or (
            self.submission and self.submission["status"]["locking"]
        ):
            # The submission exists, show the user the overview page
            return render(
                request,
                "v2/registration_of_interest/registration_of_interest_review.html",
                context={"submission": self.submission},
            )
        # If not, show the normal tasklist
        return super().get(request, *args, **kwargs)


class RegistrationOfInterest1(RegistrationOfInterestBase, TemplateView):
    template_name = "v2/registration_of_interest/registration_of_interest_1.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cases = self.client.cases.open_to_roi()
        if not cases:
            add_form_error_to_session(
                "There are no active cases to join", request=self.request, field="table-header"
            )
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
        new_submission = self.client.submissions(
            {
                "case": case_id,
                "type": SUBMISSION_TYPE_REGISTER_INTEREST,
                "documents": [],
                "created_by": self.request.user.id,
            },
            fields=["id"],
        )

        # REDIRECT to next stage
        return redirect(
            reverse("roi_submission_exists", kwargs={"submission_id": new_submission["id"]})
        )


class InterestClientTypeStep2(RegistrationOfInterestBase, FormView):
    template_name = "v2/registration_of_interest/who_is_registering.html"
    form_class = ClientTypeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.request.GET)
        # a list of dictionaries
        existing_clients_list = get_org_parties(
            TradeRemediesAPIClientMixin.client(self, self.request.user), self.request.user
        )
        # removing duplicates
        existing_clients_list = [
            each
            for each in existing_clients_list
            if each["id"] != self.request.user.organisation.get("id")
        ]
        context["existing_clients"] = True if existing_clients_list else False
        return context

    def form_valid(self, form):
        submission_id = self.kwargs["submission_id"]
        self.request.session["roi_org_chosen"] = form.cleaned_data.get("org", None)
        if form.cleaned_data.get("org") == "new-org":
            # third-party invite
            return redirect(
                reverse("interest_primary_contact", kwargs={"submission_id": submission_id})
            )
        elif form.cleaned_data.get("org") == "my-org":
            # If it's your own org, you act as both the contact and the organisation, it's not a
            # third party invite
            return self.add_organisation_to_registration_of_interest(
                organisation_id=self.request.user.contact["organisation"]["id"],
                submission_id=submission_id,
                contact_id=self.request.user.contact["id"],
            )

        elif form.cleaned_data.get("org") == "existing-org":
            # third-party invite
            return redirect(
                reverse("interest_existing_client", kwargs={"submission_id": submission_id})
            )


class InterestPrimaryContactStep2(RegistrationOfInterestBase, FormView):
    template_name = "v2/registration_of_interest/primary_client_contact.html"
    form_class = PrimaryContactForm

    def form_valid(self, form):
        submission_id = self.kwargs["submission_id"]
        new_contact = self.client.contacts(
            {"name": form.cleaned_data.get("name"), "email": form.cleaned_data.get("email")},
            fields=["id"],
        )
        contact_id = new_contact["id"]
        # organisation_id only exists if registering ROI for existing client
        organisation_id = self.kwargs.get("organisation_id", None)
        if organisation_id:
            # Associate that organisation with the ROI
            return self.add_organisation_to_registration_of_interest(
                organisation_id=organisation_id, submission_id=submission_id, contact_id=contact_id
            )
        else:
            return redirect(
                reverse(
                    "interest_ch", kwargs={"submission_id": submission_id, "contact_id": contact_id}
                )
            )


class InterestUkRegisteredYesNoStep2(RegistrationOfInterestBase, FormView):
    template_name = "v2/registration_of_interest/is_client_uk_company.html"
    form_class = YourEmployerForm

    def form_valid(self, form):
        context = self.get_context_data()
        contact_id = context["contact_id"]
        submission_id = self.kwargs["submission_id"]
        if form.cleaned_data.get("uk_employer") == "yes":
            return redirect(
                reverse(
                    "interest_ch_yes",
                    kwargs={"submission_id": submission_id, "contact_id": contact_id},
                )
            )
        elif form.cleaned_data.get("uk_employer") == "no":
            return redirect(
                reverse(
                    "interest_ch_no",
                    kwargs={"submission_id": submission_id, "contact_id": contact_id},
                )
            )


class InterestNonUkRegisteredStep2(RegistrationOfInterestBase, FormView):
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


class InterestIsUkRegisteredStep2(RegistrationOfInterestBase, FormView):
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


class InterestUkSubmitStep2(RegistrationOfInterestBase, FormView):
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
        get_dictionary = self.request.GET.dict()
        # Creating the new organisation
        organisation = self.client.organisations({**get_dictionary, **form.cleaned_data})
        # Associating the ROI with the organisation and redirecting to tasklist
        return self.add_organisation_to_registration_of_interest(
            organisation_id=organisation["id"], submission_id=submission_id, contact_id=contact_id
        )


class InterestExistingClientStep2(RegistrationOfInterestBase, FormView):
    template_name = "v2/registration_of_interest/who_you_representing_existing.html"
    form_class = ExistingClientForm

    def get_existing_clients(self):
        org_parties = get_org_parties(
            TradeRemediesAPIClientMixin.client(self, self.request.user), self.request.user
        )
        # extract and return tuples of id and name in a list (from a
        # list of dictionaries)
        # removing duplicates
        return [
            (each["id"], each["name"])
            for each in org_parties
            if each["id"] != self.request.user.contact["organisation"].get("id")
        ]

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
        return redirect(
            reverse(
                "interest_existing_client_primary_contact",
                kwargs={
                    "submission_id": self.kwargs["submission_id"],
                    "organisation_id": form.cleaned_data.get("org"),
                },
            )
        )


@method_decorator(never_cache, name="get")
class RegistrationOfInterestRegistrationDocumentation(RegistrationOfInterestBase, TemplateView):
    template_name = (
        "v2/registration_of_interest/registration_of_interest_3_registration_documentation.html"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Let's loop over the paired documents first, Then we have a look at the orphaned documents
        # (those without a corresponding public/private pair
        uploaded_documents = (
            self.submission["paired_documents"] + self.submission["orphaned_documents"]
        )

        long_time_ago = timezone.now() - datetime.timedelta(days=1000)
        sorted_uploaded_documents = sorted(
            uploaded_documents,
            key=lambda x: (
                datetime.datetime.strptime(
                    x["non_confidential"]["created_at"], "%Y-%m-%dT%H:%M:%S%z"
                )
                if x.get("non_confidential", {}).get("created_at", None)
                else long_time_ago,
                datetime.datetime.strptime(x["confidential"]["created_at"], "%Y-%m-%dT%H:%M:%S%z")
                if x.get("confidential", {}).get("created_at", None)
                else long_time_ago,
            ),
        )
        context["uploaded_documents"] = sorted_uploaded_documents

        return context

    def post(self, request, *args, **kwargs):
        if not self.submission["orphaned_documents"] and self.submission["paired_documents"]:
            return redirect(
                reverse("roi_submission_exists", kwargs={"submission_id": self.submission["id"]})
            )

        elif orphaned_documents := self.submission["orphaned_documents"]:
            for orphan in orphaned_documents:
                missing = "confidential" if orphan["non_confidential"] else "non-confidential"
                add_form_error_to_session(
                    f"You need to upload a {missing} version of your registration documentation",
                    request,
                )

        elif not self.submission["paired_documents"]:
            add_form_error_to_session(
                "You need to upload a confidential and non-confidential"
                " version of your registration documentation",
                request,
            )
        return redirect(request.path)


class RegistrationOfInterestLOA(RegistrationOfInterestBase, TemplateView):
    template_name = "v2/registration_of_interest/registration_of_interest_3_loa.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["loa_document_bundle"] = get_loa_document_bundle()
        if self.submission:
            # Getting the uploaded LOA document if it exists
            context["loa_document"] = get_uploaded_loa_document(self.submission)
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if context.get("loa_document", None):
            return redirect(
                reverse("roi_submission_exists", kwargs={"submission_id": self.submission["id"]})
            )
        else:
            add_form_error_to_session(
                "You need to upload a Letter of Authority to represent your client", request
            )
        return redirect(request.path)


class RegistrationOfInterest4(RegistrationOfInterestBase, FormView):
    template_name = "v2/registration_of_interest/registration_of_interest_4.html"
    form_class = RegistrationOfInterest4Form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.submission:
            # Getting the uploaded LOA document if it exists
            loa_document = next(
                filter(
                    lambda document: document["type"]["key"] == "loa",
                    self.submission["submission_documents"],
                ),
                None,
            )
            if loa_document:
                context["loa_document"] = loa_document["document"]
        return context

    def form_valid(self, form):
        # First we need to update the relevant OrganisationCaseRole object to AWAITING_APPROVAL
        organisation_case_role = self.client.organisation_case_roles(
            params={
                "case_id": self.submission.case.id,
                "organisation_id": self.submission.organisation.id,
            }
        )[0]
        self.client.organisation_case_roles(organisation_case_role.id).update(
            {"role_key": "awaiting_approval"}
        )

        # Now we update the status of the submission to received
        self.client.submissions(self.kwargs["submission_id"]).update_submission_status("received")
        return redirect(
            reverse("roi_complete", kwargs={"submission_id": self.kwargs["submission_id"]})
        )


class RegistrationOfInterestComplete(RegistrationOfInterestBase, TemplateView):
    template_name = "v2/registration_of_interest/registration_of_interest_complete.html"


class RegistrationOfInterestAlreadyExists(RegistrationOfInterestBase, TemplateView):
    template_name = "v2/registration_of_interest/registration_of_interest_already_exists.html"


class DeleteRegistrationOfInterest(RegistrationOfInterestBase, TemplateView):
    template_name = "v2/registration_of_interest/registration_of_interest_delete.html"

    def post(self, request, *args, **kwargs):
        submission_id = kwargs["submission_id"]
        self.client.submissions(submission_id).delete()
        return redirect(reverse("dashboard"))
