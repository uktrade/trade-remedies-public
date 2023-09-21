from config.base_views import BaseAnonymousPublicTemplateView
from datetime import datetime


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
        case = self.client.cases.get_case_by_number(self.kwargs["case_number"])
        context["case"] = case
        context["public_file"] = case.get_public_file()

        # Convert public file issue date from string to datetime
        for file in context["public_file"]:
            date_string = file["issued_at"].replace("T", " ")
            file["issued_at"] = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S%z")

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
                "is_tra",
                "name",
                "sent_at",
                "organisation_case_role_name",
            ],
            params={"non_confidential_only": True},
        )
        assert submission.issued_at
        context["submission"] = submission
        return context
