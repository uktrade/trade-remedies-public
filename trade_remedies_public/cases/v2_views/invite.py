from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from v2_api_client.exceptions import NotFoundError

from cases.v2_forms.invite import (
    ChooseCaseForm,
    InviteExistingRepresentativeDetailsForm,
    InviteNewRepresentativeDetailsForm,
    SelectCaseForm,
    SelectOrganisationForm,
    SelectPermissionsForm,
    WhoAreYouInvitingForm,
    WhoAreYouInvitingNameEmailForm,
)
from config.base_views import BasePublicFormView, BasePublicView, TaskListView
from config.constants import SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER
from config.utils import (
    add_form_error_to_session,
    get_loa_document_bundle,
    get_uploaded_loa_document,
)


class BaseInviteView(BasePublicView, TemplateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if invitation_id := kwargs.get("invitation_id"):
                self.invitation = self.client.invitations(invitation_id)
                if inviting_organisation := self.invitation["organisation"]:
                    if inviting_organisation["id"] != request.user.organisation["id"]:
                        # The user should not have access to this invitation,
                        # raise a 403 permission DENIED
                        raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if invitation_id := self.kwargs.get("invitation_id"):
            if hasattr(self, "invitation") and self.invitation:
                context["invitation"] = self.invitation
            else:
                context["invitation"] = self.client.invitations(invitation_id)
        context["group_owner"] = SECURITY_GROUP_ORGANISATION_OWNER
        context["group_regular"] = SECURITY_GROUP_ORGANISATION_USER
        return context


class BaseInviteFormView(BasePublicFormView, BaseInviteView):
    pass


class WhoAreYouInviting(BaseInviteFormView):
    template_name = "v2/invite/start.html"
    form_class = WhoAreYouInvitingForm

    def form_valid(self, form):
        if form.cleaned_data["who_are_you_inviting"] == "employee":
            invitation_update_dictionary = {
                "organisation": self.request.user.organisation["id"],
                "invalid": True,
                "invitation_type": 1,
            }
            if invitation_id := self.kwargs.get("invitation_id"):
                # There is already an existing invite, update it
                invitation = self.client.invitations(invitation_id).update(
                    invitation_update_dictionary
                )
                return redirect(
                    reverse("invitation_name_email", kwargs={"invitation_id": invitation["id"]})
                )
            else:
                new_invitation = self.client.invitations(invitation_update_dictionary)
                return redirect(
                    reverse("invitation_name_email", kwargs={"invitation_id": new_invitation["id"]})
                )
        elif form.cleaned_data["who_are_you_inviting"] == "representative":
            return redirect(reverse("invite_representative_task_list"))


class TeamMemberNameView(BaseInviteFormView):
    template_name = "v2/invite/who_are_you_inviting_name_email.html"
    form_class = WhoAreYouInvitingNameEmailForm

    def form_valid(self, form):
        # First we need to check if the email already exists as a user on the platform
        try:
            existing_user = self.client.users.get_user_by_email(
                email=form.cleaned_data["team_member_email"]
            )
            # If we get here, then that email is already registered, we need to check if that user
            # belongs to the current organisations, if so, we need to redirect the
            # user to the relevant page
            invitation = self.get_context_data(**self.kwargs)["invitation"]
            if invitation["organisation"]["id"] == existing_user["organisation"]["id"]:
                # The user belongs to this invitation's organisation, ABORT.
                return render(
                    request=self.request,
                    template_name="v2/invite/user_already_exists.html",
                    context={
                        "name": existing_user["name"],
                        "email": existing_user["email"],
                        "invitation": invitation,
                    },
                )

        except NotFoundError:
            # If the status is a 404, then we know the user does not exist, carry on as normal
            pass

        invitation = self.invitation.update(
            data={
                "email": form.cleaned_data["team_member_email"],
                "name": form.cleaned_data["team_member_name"],
            }
        )
        return redirect(
            reverse("invitation_select_permissions", kwargs={"invitation_id": invitation["id"]})
        )


class PermissionSelectView(BaseInviteFormView):
    template_name = "v2/invite/select_permissions.html"
    form_class = SelectPermissionsForm

    def form_valid(self, form):
        self.invitation.update(
            {
                "organisation_security_group": form.cleaned_data["type_of_user"],
            }
        )
        if form.cleaned_data["type_of_user"] == SECURITY_GROUP_ORGANISATION_USER:
            # They are a regular user, we need to select the cases they will have access to
            return redirect(
                reverse("invitation_choose_cases", kwargs={"invitation_id": self.invitation["id"]})
            )
        return redirect(
            reverse("invitation_review", kwargs={"invitation_id": self.invitation["id"]})
        )


class ChooseCasesView(BaseInviteFormView):
    template_name = "v2/invite/choose_cases.html"
    form_class = ChooseCaseForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            cases = self.client.organisations(
                self.request.user.organisation["id"], fields=["cases"]
            )["cases"]
            if not cases:
                return redirect(
                    reverse(
                        "invitation_review", kwargs={"invitation_id": self.kwargs["invitation_id"]}
                    )
                )
            else:
                cases = sorted(cases, key=lambda x: x["name"])
            self.cases = cases
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cases"] = self.cases
        context["cases_to_link_ids"] = [
            each["id"] for each in context["invitation"]["cases_to_link"]
        ]
        return context

    def form_valid(self, form):
        which_cases = self.request.POST.getlist("which_case")
        if "choose_case_later" in which_cases:
            # We want to clear already-linked cases if they exist
            self.invitation.update({"cases_to_link": "clear"})
        else:
            self.invitation.update({"cases_to_link": which_cases})

        return redirect(
            reverse("invitation_review", kwargs={"invitation_id": self.invitation["id"]})
        )


class ReviewInvitation(BaseInviteView):
    template_name = "v2/invite/review.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cases"] = self.client.organisations(
            self.request.user.organisation["id"], fields=["cases"]
        )
        return context

    def post(self, request, *args, **kwargs):
        self.invitation.send()
        return redirect(reverse("invitation_sent", kwargs={"invitation_id": self.invitation["id"]}))


class InvitationSent(BaseInviteView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cases"] = self.client.organisations(
            self.request.user.organisation["id"], fields=["cases"]
        )
        return context

    template_name = "v2/invite/sent.html"


class DeleteInvitation(BasePublicView, View):
    def post(self, request, invitation_id, *args, **kwargs):
        self.client.invitations(invitation_id).delete()
        return redirect(reverse("team_view"))


class InviteRepresentativeTaskList(TaskListView):
    template_name = "v2/invite/task_list.html"

    def get_task_list(self):
        invitation = {}
        if invitation_id := self.kwargs.get("invitation_id", None):
            invitation = self.client.invitations(invitation_id)
        steps = [
            {
                "heading": "Your cases",
                "sub_steps": [
                    {
                        "link": reverse("invite_representative_select_case"),
                        "link_text": "Select a Trade Remedies case",
                        "status": "Complete" if invitation else "Not Started",
                        "ready_to_do": False if invitation else True,
                    }
                ],
            },
            {
                "heading": "About your representative",
                "sub_steps": [
                    {
                        "link": reverse(
                            "invite_representative_organisation_details",
                            kwargs={"invitation_id": invitation["id"]},
                        )
                        if invitation
                        else "",
                        "link_text": "Organisation details",
                        "status": "Complete" if invitation.get("contact") else "Not Started",
                    }
                ],
            },
            {
                "heading": "Upload forms",
                "sub_steps": [
                    {
                        "link": reverse(
                            "invite_representative_loa", kwargs={"invitation_id": invitation["id"]}
                        )
                        if invitation
                        else "",
                        "link_text": "Letter of Authority",
                        "status": "Complete"
                        if (
                            invitation
                            and "submission" in invitation
                            and get_uploaded_loa_document(invitation.get("submission"))
                        )
                        else "Not Started",
                    }
                ],
            },
            {
                "heading": "Invite representative",
                "sub_steps": [
                    {
                        "link": reverse(
                            "invite_representative_check_and_submit",
                            kwargs={"invitation_id": invitation["id"]},
                        )
                        if invitation
                        else "",
                        "link_text": "Check and submit",
                        "status": "Not Started"
                        if (
                            invitation
                            and "submission" in invitation
                            and get_uploaded_loa_document(invitation.get("submission"))
                        )
                        else "Not Started",
                    }
                ],
            },
        ]
        return steps


class InviteRepresentativeSelectCase(BaseInviteFormView):
    template_name = "v2/invite/invite_representative_select_case.html"
    form_class = SelectCaseForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            organisation = self.client.organisations(
                self.request.user.organisation["id"],
                fields=["cases"],
                params={"no_representative_cases": "yes"},
            )
            cases = sorted(organisation["cases"], key=lambda case: case["name"])
            if not cases:
                # This organisation is not associated with any cases
                return render(
                    request,
                    template_name="v2/invite/no_cases_found.html",
                )

            # Now let's remove duplicates
            no_duplicate_cases = []
            seen_cases = []
            for case in cases:
                if case.id not in seen_cases:
                    no_duplicate_cases.append(case)
                    seen_cases.append(case.id)
            self.cases = no_duplicate_cases
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cases"] = self.cases
        return context

    def form_valid(self, form):
        # We've selected a valid case, lets create an invitation
        new_invitation = self.client.invitations(
            {
                "invalid": True,
                "case": form.cleaned_data["cases"],
                "invitation_type": 2,
                "organisation": self.request.user.organisation["id"],
            }
        )
        # Linking the case to the invitation
        new_invitation.update(
            {
                "cases_to_link": [
                    form.cleaned_data["cases"],
                ]
            }
        )
        return redirect(
            reverse(
                "invite_representative_task_list_exists",
                kwargs={"invitation_id": new_invitation["id"]},
            )
        )


class InviteRepresentativeOrganisationDetails(BaseInviteFormView):
    template_name = "v2/invite/invite_representative_organisation_details.html"
    form_class = SelectOrganisationForm

    def dispatch(self, request, *args, **kwargs):
        organisation = self.client.organisations(
            self.request.user.organisation["id"], fields=["invitations"]
        )
        # Now we need to get all the distinct organisations this organisation has sent invitations
        # to
        invitations_sent = []
        organisations_seen = []
        for sent_invitation in organisation["invitations"]:
            if invited_contact := sent_invitation.get("contact", None):
                # Thn checking if there is an organisation associated with the invitation
                if invited_organisation := invited_contact.get("organisation", None):
                    # If the invited contact doesn't belong to the user's organisation
                    if invited_organisation != self.request.user.organisation["id"]:
                        if invited_organisation not in organisations_seen:
                            validated = self.client.organisations(
                                invited_organisation, fields=["validated"]
                            )
                            if validated.validated:
                                # We only want to include organisations which have been validated
                                # by the TRA in the past
                                invitations_sent.append(sent_invitation)
                            # Still include them on the seen list, so we don't bother checking them
                            # again
                            organisations_seen.append(invited_organisation)

        self.invitations_sent = invitations_sent
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if not self.invitations_sent:
            # This organisation has not sent out any invitations previously, redirect
            return redirect(
                reverse(
                    "invite_new_representative_details",
                    kwargs={"invitation_id": self.kwargs["invitation_id"]},
                )
            )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invitations_sent"] = self.invitations_sent
        original_invitation = self.client.invitations(self.kwargs["invitation_id"])
        context["original_invitation"] = original_invitation

        return context

    def form_valid(self, form):
        if form.cleaned_data["organisation"] == "new":
            # It is a new representative, let's get some details!
            return redirect(
                reverse(
                    "invite_new_representative_details",
                    kwargs={"invitation_id": self.kwargs["invitation_id"]},
                )
            )
        else:
            return redirect(
                reverse(
                    "invite_existing_representative_details",
                    kwargs={
                        "invitation_id": self.kwargs["invitation_id"],
                        "organisation_id": form.cleaned_data["organisation"],
                    },
                )
            )


class InviteNewRepresentativeDetails(BaseInviteFormView):
    form_class = InviteNewRepresentativeDetailsForm
    template_name = "v2/invite/invite_representative_new_details.html"

    def form_valid(self, form):
        # First let's check if the email address already exists on the TRS
        try:
            user = self.client.users.get_user_by_email(form.cleaned_data["contact_email"])
            # This user already exists in the platform, let's associate the invitation with it
            # and their organisation so that when they log in, TRS with process them as a rep
            contact = user.contact
        except NotFoundError:
            # The user does not exist, let's create a new contact and org from scratch

            # Creating a new organisation
            organisation = self.client.organisations(
                {"name": form.cleaned_data["organisation_name"]}, fields=["id"]
            )
            # Creating a new contact and associating them with the organisation
            contact = self.client.contacts(
                {
                    "name": form.cleaned_data["contact_name"],
                    "email": form.cleaned_data["contact_email"],
                    "organisation": organisation["id"],
                }
            )

        # Associating this contact with the invitation
        updated_invitation = self.client.invitations(self.kwargs["invitation_id"]).update(
            {"contact": contact["id"]}, fields=["submission", "contact"]
        )

        # Associating the submission with the inviter's organisation
        self.client.submissions(updated_invitation["submission"]["id"]).update(
            {
                # The submission needs to be associating with the inviter's organisation, the
                # invited organisation is stored in the contact object
                "organisation": self.request.user.organisation["id"]
            },
            fields=["id"],
        )

        # Go back to the task list please!
        return redirect(
            reverse(
                "invite_representative_task_list_exists",
                kwargs={"invitation_id": updated_invitation["id"]},
            )
        )


class InviteExistingRepresentativeDetails(BaseInviteFormView):
    template_name = "v2/invite/invite_representative_existing_details.html"
    form_class = InviteExistingRepresentativeDetailsForm

    def form_valid(self, form):
        organisation_id = self.kwargs["organisation_id"]

        # Creating a new contact and associating them with the organisation
        new_contact = self.client.contacts(
            {
                "name": form.cleaned_data["contact_name"],
                "email": form.cleaned_data["contact_email"],
                "organisation": organisation_id,
            }
        )

        # Associating this contact with the invitation
        self.client.invitations(self.kwargs["invitation_id"]).update(
            {"contact": new_contact["id"]},
        )

        updated_invitation = self.client.invitations(self.kwargs["invitation_id"]).update(
            {"contact": new_contact["id"]}, fields=["submission", "contact"]
        )

        # Associating the submission with the new organisation
        self.client.submissions(updated_invitation["submission"]["id"]).update(
            {
                "organisation": self.request.user.organisation["id"],
            },
            fields=["id"],
        )

        # Go back to the task list please!
        return redirect(
            reverse(
                "invite_representative_task_list_exists",
                kwargs={"invitation_id": updated_invitation["id"]},
            )
        )


class InviteRepresentativeLoa(BaseInviteView):
    template_name = "v2/invite/invite_representative_loa.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invitation = context["invitation"]
        context["loa_document_bundle"] = get_loa_document_bundle()
        # Getting the uploaded LOA document if it exists
        context["uploaded_loa_document"] = get_uploaded_loa_document(invitation["submission"])
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if context.get("uploaded_loa_document", None):
            return redirect(
                reverse(
                    "invite_representative_task_list_exists",
                    kwargs={"invitation_id": self.kwargs["invitation_id"]},
                )
            )
        else:
            add_form_error_to_session("You need to upload a Letter of Authority", request)
        return redirect(request.path)


class InviteRepresentativeCheckAndSubmit(BaseInviteView):
    template_name = "v2/invite/invite_representative_check_and_submit.html"

    def post(self, request, *args, **kwargs):
        invitation = self.client.invitations(kwargs["invitation_id"]).send()
        return redirect(
            reverse("invite_representative_sent", kwargs={"invitation_id": invitation["id"]})
        )


class InviteRepresentativeSent(BaseInviteView):
    template_name = "v2/invite/invite_representative_sent.html"
