from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
import datetime


class RegistrationOfInterest1(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "v2/registration_of_interest/registration_of_interest_1.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cases = self.client(self.request.user).v2_get_all_cases({"open_to_roi": True})
        context["cases"] = cases
        return context

    def post(self, request, *args, **kwargs):
        case_information = request.POST["case_information"].split("*-*")
        case_reference = case_information[0]
        case_id = case_information[1]
        case_name = case_information[2]
        case_registration_deadline = case_information[3]

        if datetime.datetime.strptime(
                case_registration_deadline,
                "%Y-%m-%dT%H:%M:%S%z"
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
                }
            )
        # REDIRECT to next stage
        return redirect(reverse("landing"))
