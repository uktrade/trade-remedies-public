from config.forms import ValidationForm
from django import forms
from django.core.validators import RegexValidator


class ClientTypeForm(ValidationForm):
    org = forms.CharField(error_messages={"required": "no_org_chosen"})


class PrimaryContactForm(ValidationForm):
    name = forms.CharField(error_messages={"required": "no_name_entered"})
    email = forms.CharField(
        error_messages={"required": "no_email_entered"},
        validators=[
            RegexValidator(r"\w+@\w+", "email_not_valid"),
        ],
    )