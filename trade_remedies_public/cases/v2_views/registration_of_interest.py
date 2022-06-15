from django.views.generic import TemplateView
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin


class RegistrationOfInterest1(TemplateView, TradeRemediesAPIClientMixin):
    template_name = "v2/registration_of_interest/registration_of_interest_1.html"

    def get_context_data(self, **kwargs):
        cases = self.client(self.request.user).get_all_cases("registration-of-interest")
        print("ads")
