from django import forms
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin


class CustomValidationForm(forms.Form, TradeRemediesAPIClientMixin):
    def assign_errors_to_request(self, request):
        if not self.errors:
            return
        if "form_errors" not in request.session:
            request.session["form_errors"] = {}
            request.session["form_errors"]["error_summaries"] = []

        for field, errors in self.errors.as_data().items():
            for error in errors:
                validation_error = self.trusted_client.get_validation_error(error.message)
                if validation_error:
                    # The key can be found in the validation_errors.py file
                    if error_text := validation_error["error_text"]:
                        try:
                            request.session["form_errors"][field].append(error_text)
                        except KeyError:
                            request.session["form_errors"][field] = []
                            request.session["form_errors"][field].append(error_text)
                    if error_summary := validation_error["error_summary"]:
                        request.session["form_errors"]["error_summaries"].append(error_summary)
                else:
                    # The key cannot be found, treat it as a normal validation errors
                    pass
