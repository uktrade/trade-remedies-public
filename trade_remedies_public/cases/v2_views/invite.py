import logging

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse
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

logger = logging.getLogger(__name__)

"""########################################## SHARED VIEWS ######################################"""


class BaseInviteView(BasePublicView, TemplateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if invitation_id := kwargs.get("invitation_id"):
                self.invitation = self.client.invitations(invitation_id)
                if inviting_organisation := self.invitation["organisation"]:
                    if inviting_organisation["id"] != request.user.contact["organisation"]["id"]:
                        # The user should not have access to this invitation,
                        # raise a 403 permission DENIED
                        logger.info(
                            f"User {request.user.id} requested access to Invitation "
                            f"{invitation_id}. Permission denied."
                        )
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


class CancelDraftInvitation(BaseInviteView):
    """View for deleting a draft invitation"""

    template_name = "v2/invite/cancel_invite.html"

    def post(self, request, *args, **kwargs):
        if not self.invitation.accepted_at:
            self.invitation.delete()
            ...
        return redirect(reverse("invite_cancelled"))


class ReviewInvitation(BaseInviteView):
    """View for reviewing a sent invitation"""

    def get_template_names(self):
        if self.invitation.invitation_type == 1:
            # this is an own org invite
            return ["v2/invite/review_sent_invitation.html"]
        else:
            return ["v2/invite/invite_representative_review.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.invitation.invitation_type == 2:
            # this is a representative invite
            context["uploaded_loa_document_bundle"] = get_uploaded_loa_document(
                self.invitation.submission
            )
        return context

    def post(self, request, *args, **kwargs):
        if not self.invitation.accepted_at:
            self.invitation.delete()
        return redirect(reverse("invite_cancelled"))


class DeleteDraftInvitation(BaseInviteView):
    template_name = "v2/invite/delete_invite.html"

    def post(self, request, *args, **kwargs):
        if not self.invitation.accepted_at:
            # self.invitation.delete()
            ...
        return redirect(reverse("invite_deleted"))


"""########################################## OWN ORG INVITE ####################################"""


class WhoAreYouInviting(BaseInviteFormView):
    template_name = "v2/invite/start.html"
    form_class = WhoAreYouInvitingForm

    def form_valid(self, form):
        if form.cleaned_data["who_are_you_inviting"] == "employee":
            invitation_update_dictionary = {
                "organisation": self.request.user.contact["organisation"]["id"],
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
            reverse(
                "invitation_review_before_send", kwargs={"invitation_id": self.invitation["id"]}
            )
        )


class ChooseCasesView(BaseInviteFormView):
    template_name = "v2/invite/choose_cases.html"
    form_class = ChooseCaseForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_cases = self.client.organisations(
                self.request.user.contact["organisation"]["id"], fields=["user_cases"]
            )["user_cases"]
            if not user_cases:
                return redirect(
                    reverse(
                        "invitation_review_before_send",
                        kwargs={"invitation_id": self.kwargs["invitation_id"]},
                    )
                )
            else:
                seen_org_case_combos = []
                no_duplicate_user_cases = []
                for user_case in user_cases:
                    if (user_case.organisation.id, user_case.case.id) not in seen_org_case_combos:
                        no_duplicate_user_cases.append(user_case)
                        seen_org_case_combos.append((user_case.organisation.id, user_case.case.id))
                # user_cases = remove_duplicates_from_list_by_key(user_cases, "/case/id")
                user_cases = sorted(no_duplicate_user_cases, key=lambda x: x.case.reference)

            self.user_cases = user_cases
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_cases"] = self.user_cases
        context["user_cases_to_link_ids"] = [
            each["id"] for each in context["invitation"]["user_cases_to_link"]
        ]
        return context

    def form_valid(self, form):
        which_cases = self.request.POST.getlist("which_user_case")
        if "choose_case_later" in which_cases:
            # We want to clear already-linked cases if they exist
            self.invitation.update({"user_cases_to_link": "clear"})
        else:
            self.invitation.update({"user_cases_to_link": which_cases})

        return redirect(
            reverse(
                "invitation_review_before_send", kwargs={"invitation_id": self.invitation["id"]}
            )
        )


class ReviewInvitationBeforeSend(BaseInviteView):
    template_name = "v2/invite/review.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organisation = self.client.organisations(
            self.request.user.contact["organisation"]["id"], fields=["user_cases"]
        )
        context["organisation"] = organisation
        return context

    def post(self, request, *args, **kwargs):
        self.invitation.send()
        return redirect(reverse("invitation_sent", kwargs={"invitation_id": self.invitation["id"]}))


class InvitationSent(BaseInviteView):
    template_name = "v2/invite/sent.html"


"""########################################## REP INVITE ########################################"""


class InviteRepresentativeTaskList(TaskListView):
    template_name = "v2/invite/task_list.html"

    def dispatch(self, request, *args, **kwargs):
        self.deficient_loa = False
        return super().dispatch(request, *args, **kwargs)

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
                            and not get_uploaded_loa_document(
                                invitation.get("submission")
                            ).deficient
                        )
                        else "Incomplete"
                        if "submission" in invitation
                        and get_uploaded_loa_document(invitation.get("submission"))
                        and get_uploaded_loa_document(invitation.get("submission")).deficient
                        else "Not Started",
                        "status_text": "Complete"
                        if (
                            invitation
                            and "submission" in invitation
                            and get_uploaded_loa_document(invitation.get("submission"))
                            and not get_uploaded_loa_document(
                                invitation.get("submission")
                            ).deficient
                        )
                        else "Deficient document"
                        if "submission" in invitation
                        and get_uploaded_loa_document(invitation.get("submission"))
                        and get_uploaded_loa_document(invitation.get("submission")).deficient
                        else "",
                    },
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

        if (
            "submission" in invitation
            and get_uploaded_loa_document(invitation.get("submission"))
            and get_uploaded_loa_document(invitation.get("submission")).deficient
        ):
            self.deficient_loa = True

        return steps

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_deficient_loa"] = self.deficient_loa

        return context


class InviteRepresentativeSelectCase(BaseInviteFormView):
    template_name = "v2/invite/invite_representative_select_case.html"
    form_class = SelectCaseForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_cases = self.client.organisations(
                self.request.user.contact["organisation"]["id"],
                fields=["user_cases"],
            ).user_cases
            # we only want cases where this organisation is an interested party,
            # and not a representative
            only_interested_party_user_cases = [
                each
                for each in user_cases
                if request.user.contact["organisation"]["id"] == each.organisation.id
            ]
            if not only_interested_party_user_cases:
                # This organisation is not associated with any cases
                return render(
                    request,
                    template_name="v2/invite/no_cases_found.html",
                )

            # Now let's remove duplicates
            seen_org_case_combos = []
            no_duplicate_user_cases = []
            for user_case in only_interested_party_user_cases:
                if (user_case.organisation.id, user_case.case.id) not in seen_org_case_combos:
                    no_duplicate_user_cases.append(user_case)
                    seen_org_case_combos.append((user_case.organisation.id, user_case.case.id))

            # user_cases = remove_duplicates_from_list_by_key(user_cases, "/case/id")
            user_case_case_id_matchup = {
                user_case.id: user_case.case.id for user_case in user_cases
            }
            self.user_cases = no_duplicate_user_cases
            self.user_case_case_id_matchup = user_case_case_id_matchup
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_cases"] = self.user_cases
        return context

    def form_valid(self, form):
        # We've selected a valid case, lets create an invitation
        new_invitation = self.client.invitations(
            {
                "invalid": True,
                "case": self.user_case_case_id_matchup[form.cleaned_data["user_case"]],
                "invitation_type": 2,
                "organisation": self.request.user.contact["organisation"]["id"],
            }
        )
        # Linking the case to the invitation
        new_invitation.update(
            {
                "user_cases_to_link": [
                    form.cleaned_data["user_case"],
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
            self.request.user.contact["organisation"]["id"], fields=["invitations"]
        )
        # Now we need to get all the distinct organisations this organisation has sent invitations
        # to
        invitations_sent = []
        for sent_invitation in organisation["invitations"]:
            if invited_contact := sent_invitation.get("contact", None):
                # Thn checking if there is an organisation associated with the invitation
                if invited_organisation := invited_contact.get("organisation", None):
                    # If the invited contact doesn't belong to the user's organisation
                    if invited_organisation != self.request.user.contact["organisation"]["id"]:
                        if sent_invitation.submission.status.review_ok:
                            # We only want to include organisations which have been validated
                            # by the TRA in the past By having the
                            # invite 3rd party submission marked as sufficient.
                            invitations_sent.append(sent_invitation)
        organisations_seen = []
        no_dupe_orgs_sent_invitations = []
        for sent_invitation in invitations_sent:
            if sent_invitation.contact.organisation not in organisations_seen:
                no_dupe_orgs_sent_invitations.append(sent_invitation)
                organisations_seen.append(sent_invitation.contact.organisation)
        self.invitations_sent = no_dupe_orgs_sent_invitations
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
            # The user does not exist, let's create a new contact and org from scratch, unless there
            # is already an org associated with this invitee, and it has the same name and number
            # as the new one
            create_new_organisation = True
            create_new_contact = True

            contact = None
            organisation_id = None

            if existing_contact := self.invitation.contact:
                # if a contact is already associated with this invitation (i.e. the user is
                # revisiting this page), we don't want to create duplicates of the organisation and
                # contact objects, so we run some checks to see if that's really necessary.
                if existing_contact_organisation_name := self.invitation.contact.organisation_name:
                    if existing_contact_organisation_name == form.cleaned_data["organisation_name"]:
                        # it's the same organisation, reuse rather than recreate
                        create_new_organisation = False
                        organisation_id = self.invitation.contact.organisation
                    else:
                        # it's a new organisation, let's see if we want to delete the old one
                        old_organisation = self.client.organisations(
                            self.invitation.contact.organisation, fields=["draft"]
                        )
                        if old_organisation.draft:
                            old_organisation.delete()

                if (
                    existing_contact.name == form.cleaned_data["contact_name"]
                    and existing_contact.email == form.cleaned_data["contact_email"]
                ):
                    # it's the same contact, reuse rather than recreate
                    create_new_contact = False
                    contact = self.invitation.contact
                else:
                    # it's a new contact, let's see if we want to delete the old one
                    old_contact = self.client.contacts(self.invitation.contact.id, fields=["draft"])
                    if old_contact.draft:
                        old_contact.delete()

            if create_new_organisation:
                # Creating a new organisation
                organisation_id = self.client.organisations(
                    {"name": form.cleaned_data["organisation_name"], "draft": True}, fields=["id"]
                ).id

                # now we associate the new organisation with the invited contact
                if contact:
                    self.client.contacts(contact.id).update({"organisation": organisation_id})

            if create_new_contact:
                # Creating a new contact and associating them with the organisation
                contact = self.client.contacts(
                    {
                        "name": form.cleaned_data["contact_name"],
                        "email": form.cleaned_data["contact_email"],
                        "organisation": organisation_id,
                        "draft": True,
                    }
                )

        # Associating this contact with the invitation
        updated_invitation = self.invitation.update(
            {"contact": contact.id, "name": contact.name, "email": contact.email},
            fields=["submission", "contact", "name", "email"],
        )

        # Associating the submission with the inviter's organisation
        self.client.submissions(updated_invitation.submission.id).update(
            {
                # The submission needs to be associating with the inviter's organisation, the
                # invited organisation is stored in the contact object
                "organisation": self.request.user.contact["organisation"]["id"]
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

        if existing_contacts := self.client.contacts(
            name=form.cleaned_data["contact_name"],
            email=form.cleaned_data["contact_email"],
            organisation_id=organisation_id,
        ):
            # there are existing contacts with the same name, email, and organisation! let's just
            # use that one instead of creating a new one. If there are multiple, get the one that
            # was created first
            contact = sorted(existing_contacts, key=lambda x: x.created_at)[0]
        else:
            # Creating a new contact and associating them with the organisation
            contact = self.client.contacts(
                {
                    "name": form.cleaned_data["contact_name"],
                    "email": form.cleaned_data["contact_email"],
                    "organisation": organisation_id,
                }
            )

        # Associating this contact with the invitation
        self.client.invitations(self.kwargs["invitation_id"]).update(
            {"contact": contact.id, "name": contact.name, "email": contact.email},
            fields=["submission", "contact", "name", "email"],
        )

        # Associating the submission with the new organisation
        self.client.submissions(self.invitation.submission.id).update(
            {
                "organisation": self.request.user.contact["organisation"]["id"],
            },
            fields=["id"],
        )

        # Go back to the task list please!
        return redirect(
            reverse(
                "invite_representative_task_list_exists",
                kwargs={"invitation_id": self.invitation.id},
            )
        )


class InviteRepresentativeLoa(BaseInviteView):
    template_name = "v2/invite/invite_representative_loa.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invitation = context["invitation"]
        context["loa_document_bundle"] = get_loa_document_bundle()
        # Getting the uploaded LOA document if it exists
        uploaded_loa_document = get_uploaded_loa_document(invitation["submission"])
        if uploaded_loa_document:
            context["is_deficient_loa"] = uploaded_loa_document.deficient
            uploaded_loa_document = uploaded_loa_document["document"]
        context["uploaded_loa_document"] = uploaded_loa_document
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
        self.client.invitations(kwargs["invitation_id"]).send()
        return redirect(
            reverse("invite_representative_sent", kwargs={"invitation_id": self.invitation["id"]})
        )


class InviteRepresentativeSent(BaseInviteView):
    template_name = "v2/invite/invite_representative_sent.html"
