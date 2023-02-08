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
            invite for invite in invitations if not invite.approved_at and invite.rejected_at
        ]

        context.update(
            {
                "organisation": self.client.organisations(
                    self.request.user.contact["organisation"]["id"], fields=["organisationuser_set"]
                ),
                "pending_invitations": pending_invitations,
                "rejected_invitations": rejected_invitations,
                "pending_invitations_deficient_docs_count": sum(
                    {
                        1
                        for invite in pending_invitations
                        if invite.invitation_type == 2 and invite.submission.status.version
                    }
                ),
                "user": self.request.user,
                "group_owner": SECURITY_GROUP_ORGANISATION_OWNER,
                "group_third_party": SECURITY_GROUP_THIRD_PARTY_USER,
            }
        )

        return context


class ViewUser(BasePublicView, TemplateView):
    template_name = "v2/manage_users/view_user.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_user = self.client.organisation_users(self.kwargs["organisation_user_id"])

        context["org_user"] = org_user
        context["user"] = org_user.user
        context["organisation"] = self.client.organisations(
            org_user.user.contact.organisation,
            fields=[
                "name",
                "address",
                "post_code",
                "country_name",
            ],
        )
        return context
