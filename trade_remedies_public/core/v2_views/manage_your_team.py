from django.views.generic import TemplateView

from trade_remedies_public.config.base_views import BasePublicView


class ManageYourTeamView(BasePublicView, TemplateView):
    template_name = "v2/mange_your_team/main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organisation"] = self.client().organisations.retrieve(
            self.request.user.organisation["id"]
        )
        return context
