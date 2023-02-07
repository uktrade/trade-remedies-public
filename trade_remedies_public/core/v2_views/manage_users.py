from django.views.generic import TemplateView

from config.base_views import BasePublicView
from config.constants import SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_THIRD_PARTY_USER


class ManageUsersView(BasePublicView, TemplateView):
    template_name = "v2/manage_users/main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invitations = self.client.invitations(
            organisation_id=self.request.user.contact["organisation"]["id"],
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
        pending_representative_invitations = [
            invite
            for invite in invitations
            if not invite.approved_at
            and not invite.rejected_at
            and invite.invitation_type == 2
            and not invite.submission.archived
        ]
        pending_own_org_invitations = [
            invite
            for invite in invitations
            if not invite.accepted_at and invite.invitation_type == 1
        ]
        pending_invitations = pending_own_org_invitations + pending_representative_invitations
        rejected_invitations = [
            invite for invite in invitations if not invite.approved_at and invite.rejected_at
        ]
        context.update(
            {
                "organisation": self.client.organisations(
                    self.request.user.contact["organisation"]["id"], fields=["organisationuser_set"]
                ),
                "pending_invitations": pending_invitations,
                "rejected_invitations": rejected_invitations,
                "user": self.request.user,
                "group_owner": SECURITY_GROUP_ORGANISATION_OWNER,
                "group_third_party": SECURITY_GROUP_THIRD_PARTY_USER,
            }
        )
        return context
