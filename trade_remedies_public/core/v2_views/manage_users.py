from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.views.generic import TemplateView
from v2_api_client.shared.data.country_dialing_codes import country_dialing_codes_without_uk

from cases.v2_forms.invite import SelectPermissionsForm
from config.base_views import BasePublicView, FormInvalidMixin
from config.constants import (
    SECURITY_GROUP_ORGANISATION_OWNER,
    SECURITY_GROUP_ORGANISATION_USER,
    SECURITY_GROUP_THIRD_PARTY_USER,
)
from config.forms import EmptyForm
from core.v2_forms.manage_users import (
    ChangeCaseRoleForm,
    ChangeUserIsActiveForm,
    EditUserForm,
)


class ManageUsersView(BasePublicView, TemplateView):
    template_name = "v2/manage_users/main.html"
    groups_required = SECURITY_GROUP_ORGANISATION_OWNER

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invitations = self.client.invitations(
            organisation_id=self.request.user.contact["organisation"]["id"],
            contact_id__isnull=False,  # we need at least the name and email of the contact
            fields=[
                "contact",
                "status",
                "approved_at",
                "rejected_at",
                "accepted_at",
                "invitation_type",
                "submission",
            ],
        )

        pending_invitations = [
            invite
            for invite in invitations
            if (invite.invitation_type == 1 and not invite.accepted_at)
            or (
                invite.invitation_type == 2
                and not invite.approved_at
                and not invite.rejected_at
                and not invite.submission.archived
            )
        ]
        rejected_invitations = [
            invite
            for invite in invitations
            if invite.invitation_type == 2 and not invite.approved_at and invite.rejected_at
        ]

        context.update(
            {
                "organisation": self.client.organisations(
                    self.request.user.contact["organisation"]["id"], fields=["organisationuser_set"]
                ),
                "pending_invitations": pending_invitations,
                "rejected_invitations": rejected_invitations,
                "pending_invitations_deficient_docs_count": sum(
                    [
                        1
                        for invite in pending_invitations
                        if "deficient" in invite.status and not invite.submission.archived
                    ]
                ),
                "user": self.request.user,
                "group_owner": SECURITY_GROUP_ORGANISATION_OWNER,
                "group_third_party": SECURITY_GROUP_THIRD_PARTY_USER,
            }
        )

        return context


class BaseSingleUserView(BasePublicView):
    groups_required = SECURITY_GROUP_ORGANISATION_OWNER

    def dispatch(self, request, *args, **kwargs):
        self.organisation_user = self.client.organisation_users(self.kwargs["organisation_user_id"])
        return super().dispatch(request, *args, **kwargs)


class ViewUser(BaseSingleUserView, TemplateView):
    template_name = "v2/manage_users/view_user.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["org_user"] = self.organisation_user
        context["user"] = self.organisation_user.user
        context["organisation"] = self.client.organisations(
            self.organisation_user.user.contact.organisation,
            fields=[
                "name",
                "address",
                "post_code",
                "country_name",
            ],
        )
        # admin users cannot change their own permissions or deactivate themselves
        context["cannot_edit_permissions_and_is_active"] = (
            self.request.user.id == self.organisation_user.user.id
            and self.organisation_user.security_group == SECURITY_GROUP_ORGANISATION_OWNER
            or self.organisation_user.security_group == SECURITY_GROUP_THIRD_PARTY_USER
        )

        # users cannot edit the contact details of third party users
        context["cannot_edit_contact_details"] = (
            self.organisation_user.security_group == SECURITY_GROUP_THIRD_PARTY_USER
        )

        # users cannot assign representatives to case
        context["cannot_assign_to_case"] = (
            self.organisation_user.security_group == SECURITY_GROUP_THIRD_PARTY_USER
        )
        return context


class BaseEditUserView(BaseSingleUserView, FormInvalidMixin):
    """Admin users should not be able to edit third party users in any capacity"""

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if self.organisation_user.security_group == SECURITY_GROUP_THIRD_PARTY_USER:
            raise PermissionDenied()
        return response

    def get_success_url(self):
        return reverse("view_user", kwargs={"organisation_user_id": self.organisation_user.id})


class EditUser(BaseEditUserView):
    template_name = "v2/manage_users/edit_user.html"
    form_class = EditUserForm

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if self.organisation_user.security_group == SECURITY_GROUP_THIRD_PARTY_USER:
            raise PermissionDenied()

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.organisation_user.user

        context["country_dialing_codes_without_uk"] = country_dialing_codes_without_uk
        return context

    def form_valid(self, form):
        """Update user details and redirect to correct tab in view user page"""
        self.client.users(self.organisation_user.user.id).update(
            {
                "name": form.cleaned_data["name"],
            }
        )

        self.client.contacts(self.organisation_user.user.contact.id).update(
            {
                "name": form.cleaned_data["name"],
                "phone": form.cleaned_data["phone"],
                "country": form.cleaned_data["dialing_code"],
            }
        )

    def form_invalid(self, form):
        print("Asd")


class ChangeOrganisationUserPermissionsView(BaseEditUserView):
    template_name = "v2/invite/select_permissions.html"
    form_class = SelectPermissionsForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organisation_security_group"] = self.organisation_user.security_group
        context["group_owner"] = SECURITY_GROUP_ORGANISATION_OWNER
        context["group_regular"] = SECURITY_GROUP_ORGANISATION_USER
        return context

    def form_valid(self, form):
        self.organisation_user.update(
            {
                "security_group": form.cleaned_data["type_of_user"],
            }
        )
        # adding the user to the actual Group
        self.client.users(self.organisation_user.user.id).add_group(
            form.cleaned_data["type_of_user"]
        )


class ChangeUserActiveView(BaseEditUserView):
    template_name = "v2/manage_users/change_user_active.html"
    form_class = ChangeUserIsActiveForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.organisation_user.user
        return context

    def form_valid(self, form):
        self.client.users(self.organisation_user.user.id).update(
            {"is_active": form.cleaned_data["is_active"]}
        )


class ChangeCaseRoleView(BaseEditUserView):
    template_name = "v2/manage_users/change_case_role.html"
    form_class = ChangeCaseRoleForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_case"] = next(
            user_case
            for user_case in self.organisation_user.user.user_cases
            if user_case.id == str(self.kwargs["user_case_id"])
        )
        return context

    def form_valid(self, form):
        context = self.get_context_data(**self.kwargs)
        # update the CaseContact object if it exists (this is a workaround to the fact
        # some UserCases have no CaseContact objects)
        if case_contact := context["user_case"].case_contact:
            self.client.case_contacts(case_contact.id).update(
                {"primary": form.cleaned_data["case_role"]}
            )


class RemoveFromCaseView(BaseEditUserView):
    template_name = "v2/manage_users/remove_from_case.html"
    form_class = EmptyForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_case"] = next(
            user_case
            for user_case in self.organisation_user.user.user_cases
            if user_case.id == str(self.kwargs["user_case_id"])
        )
        context["organisation_user"] = self.organisation_user
        return context

    def form_valid(self, form):
        context = self.get_context_data(**self.kwargs)

        # deleting the corresponding CaseContact object if it exists
        if case_contact := context["user_case"].case_contact:
            self.client.case_contacts(case_contact.id).delete()

        # deleting the user_case object
        self.client.user_cases(self.kwargs["user_case_id"]).delete()


class AssignToCaseView(BaseEditUserView):
    template_name = "v2/manage_users/assign_case.html"
    form_class = EmptyForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cases_already_enrolled_in = [
            each.case.id for each in self.organisation_user.user.user_cases
        ]
        org = self.client.organisations(self.organisation_user.organisation, fields=["user_cases"])
        user_cases = [
            user_case
            for user_case in org.user_cases
            if user_case.case.id not in cases_already_enrolled_in
        ]
        seen_org_case_combos = []
        no_duplicate_user_cases = []
        for user_case in user_cases:
            if (user_case.organisation.id, user_case.case.id) not in seen_org_case_combos:
                no_duplicate_user_cases.append(user_case)
                seen_org_case_combos.append((user_case.organisation.id, user_case.case.id))
        user_cases = sorted(no_duplicate_user_cases, key=lambda x: x.case.reference)
        context["user_cases"] = user_cases
        return context

    def form_valid(self, form):
        # for each case in the POST request, create a UserCase and CaseContact object if they
        # don't already exist
        for user_case in self.request.POST.getlist("which_user_case"):
            user_case = self.client.user_cases(user_case)
            user_case_dict = {
                "case": user_case.case.id,
                "user": self.organisation_user.user.id,
                "organisation": user_case.organisation.id,  # maintain the rep relationship
            }
            if not self.client.user_cases(**user_case_dict):
                self.client.user_cases(user_case_dict)

            case_contact_dict = {
                "case": user_case.case.id,
                "contact": self.organisation_user.user.contact.id,
                "organisation": user_case.organisation.id,  # maintain the rep relationship
            }

            if not self.client.case_contacts(**case_contact_dict):
                self.client.case_contacts(case_contact_dict)
