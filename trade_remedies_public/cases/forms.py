from config.forms import ValidationForm
from django import forms


class Step2StartForm(ValidationForm):
    org_type = forms.CharField(error_messages={"required": "no_org_type_chosen"})
