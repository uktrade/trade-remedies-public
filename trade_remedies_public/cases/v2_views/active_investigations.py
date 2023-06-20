from config.base_views import BaseAnonymousPublicTemplateView


class ActiveInvestigationsView(BaseAnonymousPublicTemplateView):
    template_name = "v2/active_investigations/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_investigations"] = self.client.cases(
            archived_at__isnull=True, initiated_at__isnull=False
        )
        context["completed_investigations"] = self.client.cases(
            archived_at__isnull=False, initiated_at__isnull=False
        )
        return context


class SingleCaseView(BaseAnonymousPublicTemplateView):
    template_name = "v2/active_investigations/single_case_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        case = self.client.cases(self.kwargs["case_id"])
        context["case"] = case
        context["public_file"] = case.get_public_file()

        return context


class SingleSubmissionView(BaseAnonymousPublicTemplateView):
    template_name = "v2/active_investigations/single_submission_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submission = self.client.submissions(
            self.kwargs["submission_id"],
            fields=[
                "case",
                "type",
                "status",
                "organisation",
                "submission_documents",
                "received_at",
                "issued_at",
                "organisation_case_role",
                "is_tra",
                "name",
            ],
        )
        assert submission.issued_at
        context["submission"] = submission
        return context
