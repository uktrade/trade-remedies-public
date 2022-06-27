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
            RegexValidator(r"\w+@\w+", "email_not_valid"),
        ],
    )


class YourEmployerForm(ValidationForm):
    uk_employer = forms.ChoiceField(
        error_messages={"required": "organisation_registered_country_not_selected"},
        choices=(("no", False), ("yes", True)),
    )
