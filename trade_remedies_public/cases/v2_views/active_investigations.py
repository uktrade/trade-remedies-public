from config.base_views import BaseAnonymousPublicTemplateView


class ActiveInvestigationsView(BaseAnonymousPublicTemplateView):
    template_name = "v2/active_investigations/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_investigations"] = self.client.cases(params={"active_investigations": True})
        context["completed"] = self.client.cases(params={"completed_investigations": True})
        return context


class SingleCaseView(BaseAnonymousPublicTemplateView):
    template_name = "v2/active_investigations/single_case_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        case = self.client.cases(self.kwargs["case_id"])
        context["case"] = case
        context["public_file"] = case.get_public_file()
        return context
