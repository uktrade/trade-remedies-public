"""Generic forms that are found frequently in the TRS."""

from config.forms import ValidationForm
from django import forms


class NameAndEmailForm(ValidationForm):
    """Asks for a name and email, e.g. contact / user information"""
    name = forms.CharField()
    email = forms.EmailField()
