from config.forms import ValidationForm, BaseYourEmployerForm
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django_countries.fields import CountryField


class RegistrationStartForm(ValidationForm):
    name = forms.CharField(error_messages={"required": "no_name_entered"})
    email = forms.CharField(
        error_messages={"required": "no_email_entered"},
        validators=[
            RegexValidator(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", "email_not_valid"),
        ],
    )
    terms_and_conditions_accept = forms.BooleanField(
        error_messages={"required": "terms_and_conditions_not_accepted"}
    )


class PasswordForm(ValidationForm):
    password = forms.CharField(
        error_messages={"required": "no_password_entered"},
        validators=[
            RegexValidator(
                r"^(?=[^A-Z\n]*[A-Z])(?=[^a-z\n]*[a-z])"
                r"(?=[^0-9\n]*[0-9])(?=[^#?!@$%^&*\n-]*[#?!@$%^&*-]).{8,}$",
                "password_fails_requirements",
            ),
        ],
    )


class TwoFactorChoiceForm(ValidationForm):
    two_factor_choice = forms.ChoiceField(
        choices=(("mobile", "mobile"), ("email", "email")),
        error_messages={"required": "no_two_factor_selected"},
    )
    mobile_country_code = CountryField().formfield(required=False)
    mobile = forms.CharField(
        max_length=13,
        validators=[
            RegexValidator(r"[^0-9]", "invalid_mobile_number", inverse_match=True),
        ],
        error_messages={"max_length": "invalid_mobile_number"},
        required=False,
    )

    def clean(self):
        if self.cleaned_data.get("two_factor_choice") == "mobile":
            # We want to check that both the country code and mobile input have been provided if
            # the user wants Mobile 2FA. However, we also want to check if errors have not already
            # been raised against the values in each field, as if they have, they will not be in
            # self.cleaned_data
            if (
                not self.cleaned_data.get("mobile_country_code")
                and "mobile_country_code" not in self.errors
            ):
                self.add_error(
                    "mobile_country_code", ValidationError(message="no_country_selected")
                )
            if not self.cleaned_data.get("mobile") and "mobile" not in self.errors:
                self.add_error("mobile", ValidationError(message="no_mobile_entered"))

        return self.cleaned_data


class YourEmployerForm(BaseYourEmployerForm):
    pass


class UkEmployerForm(ValidationForm):
    company_data = forms.JSONField(error_messages={"required": "companies_house_not_searched"})

    def clean(self):
        if self.data.get("input-autocomplete") and not self.cleaned_data.get("company_data"):
            # The user has entered something in the autocomplete box but not selected an option
            self.add_error("company_data", "companies_house_not_selected")
        else:
            if self.cleaned_data.get("company_data"):
                # We only want to progress if they've selected something from
                # the companies house dropdown
                self.cleaned_data["country"] = "GB"  # Always going to be a UK company
                # We want to extract the postcode and put it in a
                # recognisable field, so we don't have to duplicate the nested dictionary for
                # a NON-UK company, as the company_data variable is fed
                # to the same create_or_update_organisation() method on the API
                self.cleaned_data["post_code"] = self.cleaned_data["company_data"]["address"][
                    "postal_code"
                ]
                # In fact, this goes for all of the fields, we want to extract them
                # so they look the same as if we came from the non-UK company page
                self.cleaned_data["address_snippet"] = self.cleaned_data["company_data"][
                    "address_snippet"
                ]
                self.cleaned_data["company_number"] = self.cleaned_data["company_data"][
                    "company_number"
                ]
                self.cleaned_data["company_name"] = self.cleaned_data["company_data"]["title"]
                return self.cleaned_data


class NonUkEmployerForm(ValidationForm):
    organisation_name = forms.CharField(error_messages={"required": "no_company_name_entered"})
    address_snippet = forms.CharField(error_messages={"required": "no_company_address_entered"})
    post_code = forms.CharField(required=False)
    company_number = forms.CharField(required=False)
    country = CountryField().formfield(error_messages={"required": "no_company_country_selected"})

    def clean(self):
        if not self.cleaned_data.get("company_number") and not self.cleaned_data.get("post_code"):
            self.add_error("company_number", "no_company_post_code_or_number_entered")
            self.add_error("post_code", "no_company_post_code_or_number_entered")
        return self.cleaned_data


class OrganisationFurtherDetailsForm(ValidationForm):
    company_website = forms.URLField(required=False, error_messages={"invalid": "incorrect_url"})
    company_vat_number = forms.CharField(required=False)
    company_eori_number = forms.CharField(
        required=False,
        max_length=17,
        error_messages={"max_length": "incorrect_eori_format"},
        validators=[RegexValidator(r"[a-zA-Z]{2}[0-9]{1,15}", "incorrect_eori_format")],
    )
    company_duns_number = forms.CharField(
        required=False, validators=[RegexValidator(r"^[0-9]{9}$", "incorrect_duns_format")]
    )
