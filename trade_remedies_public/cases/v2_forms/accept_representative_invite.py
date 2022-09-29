from django import forms

from config.forms import ValidationForm


class WhoIsRegisteringForm(ValidationForm):
    who_is_registering = forms.ChoiceField(
        choices=(
            ("email_recipient", "email_recipient"),
            ("organisation_recipient", "organisation_recipient"),
        )
    )
