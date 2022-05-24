from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from config.forms import CustomValidationForm
from django_countries.fields import CountryField


class RegistrationStartForm(CustomValidationForm):
    name = forms.CharField(error_messages={"required": "no_name_entered"}, required=True)
    email = forms.CharField(
        error_messages={"required": "no_email_entered"},
        validators=[
            RegexValidator(r"\w+@\w+", "email_not_valid"),
        ],
        required=True
    )
    terms_and_conditions_accept = forms.BooleanField(
        required=True,
        error_messages={"required": "terms_and_conditions_not_accepted"}
    )


class PasswordForm(CustomValidationForm):
    password = forms.CharField(
        error_messages={"required": "no_password_entered"},
        validators=[
            RegexValidator(
                r"^(?=[^A-Z\n]*[A-Z])(?=[^a-z\n]*[a-z])(?=[^0-9\n]*[0-9])(?=[^#?!@$%^&*\n-]*[#?!@$%^&*-]).{8,}$",
                "password_fails_requirements"),
        ]
    )


class TwoFactorChoiceForm(CustomValidationForm):
    two_factor_choice = forms.ChoiceField(
        choices=(("mobile", "mobile"), ("email", "email")),
        required=True,
        error_messages={"required": "no_two_factor_selected"},
    )
    mobile_country_code = CountryField().formfield()
    mobile = forms.CharField(
        max_length=13,
        validators=[
            RegexValidator(r"[^0-9]", "invalid_mobile_number", inverse_match=True),
        ],
        error_messages={"max_length": "invalid_mobile_number"}
    )

    def clean(self):
        if self.cleaned_data["two_factor_choice"] == "mobile":
            if not self.cleaned_data.get("mobile_country_code"):
                raise ValidationError(message="no_country_selected")
            if not self.cleaned_data.get("mobile"):
                raise ValidationError(message="no_mobile_entered")
        return self.cleaned_data

class YourEmployerForm(CustomValidationForm):
    uk_employer = forms.BooleanField(
        required=True,
        error_messages={"required": "organisation_registered_country_not_selected"}
    )

class UkEmployerForm(CustomValidationForm):
    company_data = forms.JSONField(
        required=True,
        error_messages={"required": "organisation_registered_country_not_selected"}
    )
