from config.forms import BaseYourEmployerForm, ValidationForm
from django import forms
from django.core.validators import RegexValidator
from django_countries.fields import CountryField

from trade_remedies_public.config.forms.validators import email_regex_validator


class ClientTypeForm(ValidationForm):
    org = forms.ChoiceField(
        error_messages={"required": "no_org_chosen"},
        choices=(("new-org", "new-org"), ("my-org", "my-org"), ("existing-org", "existing-org")),
    )


class ExistingClientForm(ValidationForm):
    # declare empty choices variable
    choices = []

    def __init__(self, *args, **kwargs):
        existing_clients = kwargs.pop("existing_clients", None)
        super(ExistingClientForm, self).__init__(*args, **kwargs)
        # assign value to the choices variable
        self.fields["org"].choices = existing_clients

    org = forms.ChoiceField(
        error_messages={"required": "no_representative_org"},
        choices=[],  # use the choices variable
    )


class PrimaryContactForm(ValidationForm):
    name = forms.CharField(error_messages={"required": "no_contact_name_entered"})
    email = forms.CharField(
        error_messages={"required": "no_contact_email_entered"},
        validators=[
            RegexValidator(
                email_regex_validator,
                "contact_email_not_valid",
            ),
        ],
    )


class YourEmployerForm(BaseYourEmployerForm):
    pass


class UkEmployerForm(ValidationForm):
    organisation_name = forms.CharField()
    companies_house_id = forms.CharField()
    organisation_post_code = forms.CharField()
    organisation_address = forms.CharField()
    # Need a field to match element id in the form html template to add error message
    company_search_container = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean(self):
        # The user has entered something in the autocomplete box but not selected an option
        if (
            self.data.get("input-autocomplete")
            and not self.cleaned_data.get("organisation_name")
            and not self.cleaned_data.get("companies_house_id")
            and not self.cleaned_data.get("organisation_post_code")
            and not self.cleaned_data.get("organisation_address")
        ):
            self.add_error("company_search_container", "companies_house_not_selected")
        # Nothing has been entered by the user
        elif not self.data.get("input-autocomplete"):
            self.add_error("company_search_container", "companies_house_not_searched")
        else:
            return self.cleaned_data


class NonUkEmployerForm(ValidationForm):
    organisation_name = forms.CharField(error_messages={"required": "no_client_name_entered"})
    address_snippet = forms.CharField(error_messages={"required": "no_client_address_entered"})
    post_code = forms.CharField(required=False)
    company_number = forms.CharField(required=False)
    country = CountryField().formfield(error_messages={"required": "no_client_country_selected"})

    def clean(self):
        if not self.cleaned_data.get("company_number") and not self.cleaned_data.get("post_code"):
            self.add_error("company_number", "no_client_post_code_or_number_entered")
            self.add_error("post_code", "no_client_post_code_or_number_entered")
        return self.cleaned_data


class ClientFurtherDetailsForm(ValidationForm):
    company_website = forms.URLField(
        required=False, error_messages={"invalid": "incorrect_client_url"}
    )
    company_vat_number = forms.CharField(required=False)
    company_eori_number = forms.CharField(
        required=False,
        max_length=17,
        error_messages={"max_length": "incorrect_client_eori_format"},
        validators=[RegexValidator(r"[a-zA-Z]{2}[0-9]{1,15}", "incorrect_client_eori_format")],
    )
    company_duns_number = forms.CharField(
        required=False, validators=[RegexValidator(r"^[0-9]{9}$", "incorrect_client_duns_format")]
    )


class RegistrationOfInterest4Form(ValidationForm):
    authorised = forms.BooleanField(
        required=True, error_messages={"required": "not_authorised_roi"}
    )


class RegistrationOfInterest3Form(ValidationForm):
    non_confidential_file = forms.FileField()
    confidential_file = forms.FileField()
