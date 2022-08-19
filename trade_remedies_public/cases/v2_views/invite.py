from apiclient.exceptions import ClientError
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from config.base_views import BasePublicFormView, BasePublicView
from config.constants import SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER
from trade_remedies_public.cases.v2_forms.invite import InviteExistingRepresentativeDetailsForm, \
    InviteNewRepresentativeDetailsForm, \
    SelectCaseForm, SelectOrganisationForm, \
    SelectPermissionsForm, \
    WhoAreYouInvitingForm, \
    WhoAreYouInvitingNameEmailForm
from trade_remedies_public.config.base_views import TaskListView
from trade_remedies_public.config.utils import add_form_error_to_session, get_loa_document_bundle, \
    get_uploaded_loa_document


class BaseInviteView(BasePublicView, TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if invitation_id := self.kwargs.get("invitation_id"):
            context["invitation"] = self.client.get(
                self.client.url(f"invitations/{invitation_id}")
            )
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
            new_invitation = self.client.post(self.client.url("invitations"), data={
                "organisation": self.request.user.organisation["id"],
                "invalid": True,
                "invitation_type": 1
            })
            return redirect(
                reverse("invitation_name_email", kwargs={"invitation_id": new_invitation["id"]})
            )
        elif form.cleaned_data["who_are_you_inviting"] == "representative":
            return redirect(reverse("invite_representative_task_list"))


class TeamMemberNameView(BaseInviteFormView):
    template_name = "v2/invite/who_are_you_inviting_name_email.html"
    form_class = WhoAreYouInvitingNameEmailForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invitation = self.client.get(self.client.url(f"invitations/{self.kwargs['invitation_id']}"))
        context["invitation"] = invitation
        return context

    def form_valid(self, form):
        # First we need to check if the email already exists as a user on the platform
        try:
            existing_user = self.client.get_user_by_email(
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
                        "invitation": invitation
                    }
                )

        except ClientError as e:
            if e.status_code != 404:
                # An unknown error has been raised by the API
                raise e

        invitation = self.client.put(
            self.client.url(f"invitations/{self.kwargs['invitation_id']}"),
            data={
                "email": form.cleaned_data["team_member_email"],
                "name": form.cleaned_data["team_member_name"]
            }
        )
        return redirect(
            reverse("invitation_select_permissions", kwargs={"invitation_id": invitation["id"]})
        )


class PermissionSelectView(BaseInviteFormView):
    template_name = "v2/invite/select_permissions.html"
    form_class = SelectPermissionsForm

    def form_valid(self, form):
        invitation = self.client.put(
            self.client.url(f"invitations/{self.kwargs['invitation_id']}"),
            data={
                "organisation_security_group": form.cleaned_data["type_of_user"],
            }
        )
        return redirect(reverse("invitation_review", kwargs={"invitation_id": invitation["id"]}))


class ReviewInvitation(BaseInviteView):
    template_name = "v2/invite/review.html"

    def post(self, request, *args, **kwargs):
        invitation = self.client.send_invitation(kwargs["invitation_id"])
        return redirect(reverse("invitation_sent", kwargs={"invitation_id": invitation["id"]}))


class InvitationSent(BaseInviteView):
    template_name = "v2/invite/sent.html"


class DeleteInvitation(BasePublicView, View):
    def post(self, request, invitation_id, *args, **kwargs):
        self.client.delete(self.client.url(f"invitations/{invitation_id}"))
        return redirect(reverse("team_view"))


class InviteRepresentativeTaskList(TaskListView):
    template_name = "v2/invite/task_list.html"

    def get_task_list(self):
        invitation = {}
        if invitation_id := self.kwargs.get("invitation_id", None):
            invitation = self.client.get(self.client.url(f"invitations/{invitation_id}"))
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
                        "link": reverse("invite_representative_organisation_details", kwargs={
                            "invitation_id": invitation["id"]
                        }) if invitation else "",
                        "link_text": "Organisation details",
                        "status": "Complete" if invitation.get("contact") else "Not Started",
                    }
                ],
            },
            {
                "heading": "Upload forms",
                "sub_steps": [
                    {
                        "link": reverse("invite_representative_loa", kwargs={
                            "invitation_id": invitation["id"]
                        }) if invitation else "",
                        "link_text": "Letter of Authority",
                        "status": "Complete" if (
                                invitation and
                                "submission" in invitation and
                                get_uploaded_loa_document(invitation.get("submission"))
                        ) else "Not Started",
                    }
                ],
            },
            {
                "heading": "Invite representative",
                "sub_steps": [
                    {
                        "link": reverse("invite_representative_check_and_submit", kwargs={
                            "invitation_id": invitation["id"]
                        }) if invitation else "",
                        "link_text": "Check and submit",
                        "status": "Not Started" if (
                                invitation and
                                "submission" in invitation and
                                get_uploaded_loa_document(invitation.get("submission"))
                        ) else "Not Started",
                    }
                ],
            }
        ]
        return steps


class InviteRepresentativeSelectCase(BaseInviteFormView):
    template_name = "v2/invite/invite_representative_select_case.html"
    form_class = SelectCaseForm

    def dispatch(self, request, *args, **kwargs):
        organisation = self.client.get(
            self.client.url(f"organisations/{self.request.user.organisation['id']}")
        )
        cases = sorted(organisation["cases"], key=lambda case: case["name"])
        if not cases:
            # This organisation is not associated with any cases
            return render(
                request,
                template_name="v2/invite/no_cases_found.html",
            )

        self.cases = cases
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cases"] = self.cases
        return context

    def form_valid(self, form):
        # We've selected a valid case, lets create an invitation
        new_invitation = self.client.post(self.client.url("invitations"), data={
            "invalid": True,
            "case": form.cleaned_data["cases"],
            "invitation_type": 2,
            "organisation": self.request.user.organisation["id"]
        })
        return redirect(
            reverse(
                "invite_representative_task_list_exists",
                kwargs={"invitation_id": new_invitation["id"]}
            )
        )


class InviteRepresentativeOrganisationDetails(BaseInviteFormView):
    template_name = "v2/invite/invite_representative_organisation_details.html"
    form_class = SelectOrganisationForm

    def dispatch(self, request, *args, **kwargs):
        organisation = self.client.get(
            self.client.url(f"organisations/{self.request.user.organisation['id']}")
        )
        # Now we need to get all the distinct organisations this organisation has sent invitations
        # to
        invitations_sent = []
        for sent_invitation in organisation["invitations"]:
            if invited_contact := sent_invitation.get("contact", None):
                # If the invited contact doesn't belong to the user's organisation
                if invited_contact.get("organisation") != self.request.user.organisation["id"]:
                    invitations_sent.append(sent_invitation)

        self.invitations_sent = invitations_sent
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if not self.invitations_sent:
            # This organisation has not sent out any invitations previously, redirect
            return redirect(reverse(
                "invite_new_representative_details",
                kwargs={"invitation_id": self.kwargs["invitation_id"]}
            ))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invitations_sent"] = self.invitations_sent
        original_invitation = self.client.get(
            self.client.url(f"invitations/{self.kwargs['invitation_id']}")
        )
        context["original_invitation"] = original_invitation

        return context

    def form_valid(self, form):
        if form.cleaned_data["organisation"] == "new":
            # It is a new representative, let's get some details!
            return redirect(reverse(
                "invite_new_representative_details",
                kwargs={"invitation_id": self.kwargs["invitation_id"]}
            ))
        else:
            return redirect(reverse("invite_existing_representative_details", kwargs={
                "invitation_id": self.kwargs["invitation_id"],
                "organisation_id": form.cleaned_data["organisation"]
            }))


class InviteNewRepresentativeDetails(BaseInviteFormView):
    form_class = InviteNewRepresentativeDetailsForm
    template_name = "v2/invite/invite_representative_new_details.html"

    def form_valid(self, form):
        # Creating a new organisation
        new_organisation = self.client.post(self.client.url("organisations"), data={
            "name": form.cleaned_data["organisation_name"]
        })

        # Creating a new contact and associating them with the organisation
        new_contact = self.client.post(self.client.url("contacts"), data={
            "name": form.cleaned_data["contact_name"],
            "email": form.cleaned_data["contact_email"],
            "organisation": new_organisation["id"],
        })

        # Associating this contact with the invitation
        updated_invitation = self.client.put(
            self.client.url(f"invitations/{self.kwargs['invitation_id']}"),
            data={
                "contact": new_contact["id"]
            }
        )

        # Associating the submission with the new organisation
        updated_submission = self.client.put(
            self.client.url(f"submissions/{updated_invitation['submission']['id']}"),
            data={
                # The submission needs to be associating with the inviter's organisation, the
                # invited's organisation is stored in the contact object
                "organisation": self.request.user.organisation['id']
            }
        )

        # Go back to the task list please!
        return redirect(reverse(
            "invite_representative_task_list_exists",
            kwargs={"invitation_id": updated_invitation["id"]}
        ))


class InviteExistingRepresentativeDetails(BaseInviteFormView):
    template_name = "v2/invite/invite_representative_existing_details.html"
    form_class = InviteExistingRepresentativeDetailsForm

    def form_valid(self, form):
        organisation_id = self.kwargs["organisation_id"]

        # Creating a new contact and associating them with the organisation
        new_contact = self.client.post(self.client.url("contacts"), data={
            "name": form.cleaned_data["contact_name"],
            "email": form.cleaned_data["contact_email"],
            "organisation": organisation_id,
        })

        # Associating this contact with the invitation
        updated_invitation = self.client.put(
            self.client.url(f"invitations/{self.kwargs['invitation_id']}"),
            data={
                "contact": new_contact["id"]
            }
        )

        # Associating the submission with the new organisation
        updated_submission = self.client.put(
            self.client.url(f"submissions/{updated_invitation['submission']['id']}"),
            data={
                "organisation": self.request.user.organisation['id']
            }
        )

        # Go back to the task list please!
        return redirect(reverse(
            "invite_representative_task_list_exists",
            kwargs={"invitation_id": updated_invitation["id"]}
        ))


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
            return redirect(reverse(
                "invite_representative_task_list_exists",
                kwargs={"invitation_id": self.kwargs["invitation_id"]}
            ))
        else:
            add_form_error_to_session("You need to upload a Letter of Authority", request)
        return redirect(request.path)


class InviteRepresentativeCheckAndSubmit(BaseInviteView):
    template_name = "v2/invite/invite_representative_check_and_submit.html"

    def post(self, request, *args, **kwargs):
        invitation = self.client.send_invitation(kwargs["invitation_id"])
        return redirect(reverse(
            "invite_representative_sent",
            kwargs={"invitation_id": invitation["id"]}
        ))


class InviteRepresentativeSent(BaseInviteView):
    template_name = "v2/invite/invite_representative_sent.html"
