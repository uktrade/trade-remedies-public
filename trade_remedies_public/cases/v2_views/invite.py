from config.base_views import BasePublicFormView, BasePublicView
from config.constants import SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER
from config.forms.base_forms import NameAndEmailForm
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView


class WhoAreYouInviting(BasePublicView, TemplateView):
    template_name = "v2/invite/start.html"

    def post(self, request, *args, **kwargs):
        if request.POST["who_are_you_inviting"] == "employee":
            new_invitation = self.client().invitations.create(
                organisation=request.user.organisation["id"],
                invalid=True
            )
            return redirect(
                reverse("invitation_name_email", kwargs={"invitation_id": new_invitation["id"]})
            )


class TeamMemberNameView(BasePublicFormView, TemplateView):
    template_name = "v2/invite/who_are_you_inviting_name_email.html"
    form_class = NameAndEmailForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invitation = self.client().invitations.retrieve(self.kwargs["invitation_id"])
        context["invitation"] = invitation
        return context

    def post(self, request, *args, **kwargs):
        invitation = self.client().invitations.update(
            kwargs["invitation_id"],
            email=request.POST["team_member_email"],
            name=request.POST["team_member_name"]
        )
        return redirect(
            reverse("invitation_select_permissions", kwargs={"invitation_id": invitation["id"]})
        )


class PermissionSelectView(BasePublicView, TemplateView):
    template_name = "v2/invite/select_permissions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group_owner"] = SECURITY_GROUP_ORGANISATION_OWNER
        context["group_regular"] = SECURITY_GROUP_ORGANISATION_USER
        return context

    def post(self, request, *args, **kwargs):
        invitation = self.client().invitations.update(
            kwargs["invitation_id"],
            organisation_security_group=request.POST["type_of_user"]
        )
        return redirect(reverse("invitation_review", kwargs={"invitation_id": invitation["id"]}))


class ReviewInvitation(BasePublicView, TemplateView):
    template_name = "v2/invite/review.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invitation = self.client().invitations.retrieve(self.kwargs["invitation_id"])
        context["invitation"] = invitation
        context["group_owner"] = SECURITY_GROUP_ORGANISATION_OWNER
        context["group_regular"] = SECURITY_GROUP_ORGANISATION_USER
        return context

    def post(self, request, *args, **kwargs):
        invitation = self.client().invitations.send(kwargs["invitation_id"])
        return redirect(reverse("invitation_sent", kwargs={"invitation_id": invitation["id"]}))


class InvitationSent(BasePublicView, TemplateView):
    template_name = "v2/invite/sent.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invitation = self.client().invitations.retrieve(self.kwargs["invitation_id"])
        context["invitation"] = invitation
        context["group_owner"] = SECURITY_GROUP_ORGANISATION_OWNER
        context["group_regular"] = SECURITY_GROUP_ORGANISATION_USER
        return context
