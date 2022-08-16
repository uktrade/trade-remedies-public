from apiclient.exceptions import ClientError
from config.base_views import BasePublicFormView, BasePublicView
from config.constants import SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from trade_remedies_public.cases.v2_forms.invite import SelectPermissionsForm, \
    WhoAreYouInvitingForm, \
    WhoAreYouInvitingNameEmailForm
from trade_remedies_public.config.base_views import TaskListView


class WhoAreYouInviting(BasePublicFormView, TemplateView):
    template_name = "v2/invite/start.html"
    form_class = WhoAreYouInvitingForm

    def form_valid(self, form):
        if form.cleaned_data["who_are_you_inviting"] == "employee":
            new_invitation = self.client.post(self.client.url("invitations"), data={
                "organisation": self.request.user.organisation["id"],
                "invalid": True
            })
            return redirect(
                reverse("invitation_name_email", kwargs={"invitation_id": new_invitation["id"]})
            )
        elif form.cleaned_data["who_are_you_inviting"] == "representative":
            return redirect(reverse("invite_representative_task_list"))


class TeamMemberNameView(BasePublicFormView, TemplateView):
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


class PermissionSelectView(BasePublicFormView, TemplateView):
    template_name = "v2/invite/select_permissions.html"
    form_class = SelectPermissionsForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group_owner"] = SECURITY_GROUP_ORGANISATION_OWNER
        context["group_regular"] = SECURITY_GROUP_ORGANISATION_USER
        return context

    def form_valid(self, form):
        invitation = self.client.put(
            self.client.url(f"invitations/{self.kwargs['invitation_id']}"),
            data={
                "organisation_security_group": form.cleaned_data["type_of_user"],
            }
        )
        return redirect(reverse("invitation_review", kwargs={"invitation_id": invitation["id"]}))


class ReviewInvitation(BasePublicView, TemplateView):
    template_name = "v2/invite/review.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invitation = self.client.get(self.client.url(f"invitations/{self.kwargs['invitation_id']}"))
        context["invitation"] = invitation
        context["group_owner"] = SECURITY_GROUP_ORGANISATION_OWNER
        context["group_regular"] = SECURITY_GROUP_ORGANISATION_USER
        return context

    def post(self, request, *args, **kwargs):
        invitation = self.client.send_invitation(kwargs["invitation_id"])
        return redirect(reverse("invitation_sent", kwargs={"invitation_id": invitation["id"]}))


class InvitationSent(BasePublicView, TemplateView):
    template_name = "v2/invite/sent.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invitation = self.client.get(self.client.url(f"invitations/{self.kwargs['invitation_id']}"))
        context["invitation"] = invitation
        context["group_owner"] = SECURITY_GROUP_ORGANISATION_OWNER
        context["group_regular"] = SECURITY_GROUP_ORGANISATION_USER
        return context


class DeleteInvitation(BasePublicView, View):
    def post(self, request, invitation_id, *args, **kwargs):
        self.client.delete(self.client.url(f"invitations/{invitation_id}"))
        return redirect(reverse("team_view"))


class InviteRepresentativeTaskList(TaskListView):
    template_name = "v2/invite/task_list.html"

    def get_task_list(self):
        invitation = None
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
            }
        ]
        return steps


class InviteRepresentativeSelectCase(BasePublicView, TemplateView):
    template_name = "v2/invite/invite_representative_select_case.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organisation = self.client.get(
            self.client.url(f"organisations/{self.request.user.organisation['id']}")
        )
        context["cases"] = organisation["cases"]
        return context
