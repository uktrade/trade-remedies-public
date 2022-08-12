from collections import defaultdict

from django import forms
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin


class ValidationForm(forms.Form, TradeRemediesAPIClientMixin):
    def assign_errors_to_request(self, request):
        if not self.errors:
            return
        if "form_errors" not in request.session:
            request.session["form_errors"] = defaultdict(list)

        for field, errors in self.errors.as_data().items():
            for error in errors:
                validation_error = self.trusted_client.get_validation_error(error.message)
                if validation_error:
                    # The key can be found in the validation_errors.py file
                    if error_text := validation_error.get("error_text"):
                        if isinstance(field, list):
                            fields = field
                        else:
                            fields = [
                                field,
                            ]
                        for field in fields:
                            request.session["form_errors"][field].append(error_text)
                    if error_summary := validation_error.get("error_summary"):
                        # We don't want to show the same error_summary twice
                        if error_summary not in [
                            each[1] for each in request.session["form_errors"]["error_summaries"]
                        ]:
                            request.session["form_errors"]["error_summaries"].append(
                                (field, error_summary)
                            )
                else:
                    # The key cannot be found, treat it as a normal validation error
                    for error_message in error.messages:
                        request.session["form_errors"][field].append(error_message)


class BaseYourEmployerForm(ValidationForm):
    uk_employer = forms.ChoiceField(
        error_messages={"required": "organisation_registered_country_not_selected"},
        choices=(("no", False), ("yes", True)),
    )
