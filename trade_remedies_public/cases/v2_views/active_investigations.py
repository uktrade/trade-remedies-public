import sentry_sdk

from config.base_views import BaseAnonymousPublicTemplateView
from datetime import datetime

from trade_remedies_client.mixins import TradeRemediesAPIClientMixin

import logging

logger = logging.getLogger(__name__)


class ActiveInvestigationsView(BaseAnonymousPublicTemplateView, TradeRemediesAPIClientMixin):
    template_name = "v2/active_investigations/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        case_list = self.client.cases(archived_at__isnull=True, initiated_at__isnull=False)
        case_list_completed = self.client.cases(
            archived_at__isnull=False, initiated_at__isnull=False
        )

        case_ids = []
        for case in case_list:
            case_ids.append(case.get("id"))
        for case in case_list_completed:
            case_ids.append(case.get("id"))

        logger.critical(case_list)
        logger.critical(case_list_completed)
        logger.critical(case_ids)

        states = {}
        for case_id in case_ids:
            states_next_item = self.trusted_client.get_case_state(fields=["COMMODITY_NAME"], case_ids=[case_id])
            states = states | states_next_item

        #logger.critical(type(states))
        #logger.critical(states)

        for case in case_list:
            state = states.get(case.get("id"))
            if state:
                case.state = state
        for case in case_list_completed:
            state = states.get(case.get("id"))
            if state:
                case.state = state

        context["active_investigations"] = case_list
        context["completed_investigations"] = case_list_completed

        return context


class SingleCaseView(BaseAnonymousPublicTemplateView):
    template_name = "v2/active_investigations/single_case_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        case = self.client.cases.get_case_by_number(self.kwargs["case_number"])
        context["case"] = case
        context["public_file"] = case.get_public_file()

        # Convert public file issue date from string to datetime
        for file in context["public_file"]["submissions"]:
            date_string = file["issued_at"].replace("T", " ")
            file["issued_at"] = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S%z")

        return context


class SingleSubmissionView(BaseAnonymousPublicTemplateView):
    template_name = "v2/active_investigations/single_submission_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submission = self.call_client(timeout=70).submissions(
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
                "deficiency_notice_params",
            ],
            params={"non_confidential_only": True},
        )
        sentry_sdk.set_context(
            "referer",
            {
                "META_HTTP_REFERER": self.request.META.get("HTTP_REFERER"),
                "NORMAL_HTTP_REFERER": self.request.headers.get("Referer"),
            },
        )
        assert submission.issued_at
        sentry_sdk.set_context("referer", None)
        context["submission"] = submission
        return context
