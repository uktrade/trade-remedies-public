import requests as requests
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.generic import TemplateView
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
import datetime

from config.settings.base import API_BASE_URL


class RegistrationOfInterest1(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "v2/registration_of_interest/registration_of_interest_1.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        response = requests.get(
            f"{API_BASE_URL}/api/v2/cases/",
            headers={
                "Authorization": f"Token {self.request.user.token}",  # /PS-IGNORE
            },
            params={"open_to_roi": True},
        )
        response.raise_for_status()
        cases = response.json()
        if not cases:
            self.request.session["form_errors"] = {}
            self.request.session["form_errors"]["error_summaries"] = [
                ["table-header", "There are no active cases to join"]
            ]
        context["cases"] = cases
        return context

    def post(self, request, *args, **kwargs):
        case_information = request.POST["case_information"].split("*-*")
        case_reference = case_information[0]
        case_id = case_information[1]
        case_name = case_information[2]
        case_registration_deadline = case_information[3]

        if datetime.datetime.strptime(
            case_registration_deadline, "%Y-%m-%dT%H:%M:%S%z"
        ) < timezone.now() and not request.POST.get("confirmed_okay_to_proceed"):
            return render(
                request,
                "v2/registration_of_interest/registration_of_interest_late_registration.html",
                context={
                    "case_registration_deadline": case_registration_deadline,
                    "case_name": case_name,
                    "case_reference": case_reference,
                    "case_id": case_id,
                    "case_information": request.POST["case_information"],
                },
            )
        # REDIRECT to next stage
        return redirect(f"/case/interest/{case_id}/")
