from django.views.generic import TemplateView

from config.base_views import BasePublicView
from config.constants import SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_THIRD_PARTY_USER


class ManageUsersView(BasePublicView, TemplateView):
    template_name = "v2/manage_users/main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organisation"] = self.client.organisations(self.request.user.organisation["id"])
        context["pending_invitations"] = self.client.invitations(
            organisation_id=self.request.user.organisation["id"],
            approved_at__isnull=True,
            rejected_at__isnull=True,
        )
        context["rejected_invitations"] = self.client.invitations(
            organisation_id=self.request.user.organisation["id"],
            approved_at__isnull=True,
            rejected_at__isnull=False,
        )
        context["user"] = self.request.user
        context["group_owner"] = SECURITY_GROUP_ORGANISATION_OWNER
        context["group_third_party"] = SECURITY_GROUP_THIRD_PARTY_USER
        return context
