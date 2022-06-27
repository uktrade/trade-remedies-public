from config.forms import ValidationForm
from django import forms
from django.core.validators import RegexValidator


class ClientTypeForm(ValidationForm):
    org = forms.ChoiceField(
        error_messages={"required": "no_org_chosen"},
        choices=(("new-org", "new-org"), ("my-org", "my-org"), ("existing-org", "existing-org")),
    )


class PrimaryContactForm(ValidationForm):
    name = forms.CharField(error_messages={"required": "no_name_entered"})
    email = forms.CharField(
        error_messages={"required": "no_email_entered"},
        validators=[
            RegexValidator(r"\w+@\w+.com", "email_not_valid"),
        ],
    )


class YourEmployerForm(ValidationForm):
    uk_employer = forms.ChoiceField(
        error_messages={"required": "organisation_registered_country_not_selected"},
        choices=(("no", False), ("yes", True)),
    )


class UkEmployerForm(ValidationForm):
    company_search_container = forms.NullBooleanField()
    organisation_name = forms.CharField()
    companies_house_id = forms.CharField()
    organisation_post_code = forms.CharField()
    organisation_address = forms.CharField()

    def clean(self):
        if (
            self.data.get("input-autocomplete")
            and not self.cleaned_data.get("organisation_name")
            and not self.cleaned_data.get("companies_house_id")
            and not self.cleaned_data.get("organisation_post_code")
            and not self.cleaned_data.get("organisation_address")
        ):
            # The user has entered something in the autocomplete box but not selected an option
            self.add_error("company_search_container", "companies_house_not_selected")
        elif not self.data.get("input-autocomplete"):
            self.add_error("company_search_container", "companies_house_not_searched")
        else:
            return self.cleaned_data
