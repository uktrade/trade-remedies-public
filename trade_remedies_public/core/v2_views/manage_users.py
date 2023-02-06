from django.views.generic import TemplateView

from config.base_views import BasePublicView
from config.constants import SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_THIRD_PARTY_USER


class ManageUsersView(BasePublicView, TemplateView):
    template_name = "v2/manage_users/main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pending_invitations = self.client.invitations(
            organisation_id=self.request.user.organisation["id"],
            approved_at__isnull=True,
            rejected_at__isnull=True,
        )
        context.update(
            {
                "organisation": self.client.organisations(self.request.user.organisation["id"]),
                "pending_invitations": pending_invitations,
                "rejected_invitations": self.client.invitations(
                    organisation_id=self.request.user.organisation["id"],
                    approved_at__isnull=True,
                    rejected_at__isnull=False,
                ),
                "pending_invitations_deficient_docs_count": sum(
                    {
                        1
                        for invite in pending_invitations
                        if invite.invitation_type == 2 and invite.submission.deficiency_sent_at
                    }
                ),
                "user": self.request.user,
                "group_owner": SECURITY_GROUP_ORGANISATION_OWNER,
                "group_third_party": SECURITY_GROUP_THIRD_PARTY_USER,
            }
        )
        return context
