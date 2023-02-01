from django.views.generic import TemplateView

from config.base_views import BasePublicView
from config.constants import (
    SECURITY_GROUP_ORGANISATION_OWNER,
    SECURITY_GROUP_ORGANISATION_USER,
)


class ManageYourTeamView(BasePublicView, TemplateView):
    template_name = "v2/mange_your_team/main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        """context["organisation"] = self.client.organisations(
            self.request.user.organisation["id"]
        )"""
        context["group_owner"] = SECURITY_GROUP_ORGANISATION_OWNER
        context["group_regular"] = SECURITY_GROUP_ORGANISATION_USER
        return context
