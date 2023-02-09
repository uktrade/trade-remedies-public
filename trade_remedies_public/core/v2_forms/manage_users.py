from django import forms
from v2_api_client.shared.data.country_dialing_codes import country_dialing_codes_without_uk
from v2_api_client.shared.form_fields import RequiredYesNoRadioButton
from v2_api_client.shared.utlils import is_phone_number_valid

from config.forms import ValidationForm


class EditUserForm(ValidationForm):
    name = forms.CharField()
    email = forms.EmailField()
    dialing_code = forms.ChoiceField(
        choices=[["GB", "GB"]]
        + [[each["code"], each["name"]] for each in country_dialing_codes_without_uk]
    )
    phone = forms.CharField()

    def clean(self):
        cleaned_data = super().clean()

        if not is_phone_number_valid(cleaned_data["dialing_code"], cleaned_data["phone"]):
            self.add_error("phone", "Phone number is invalid")
        return cleaned_data


class ChangeUserIsActiveForm(ValidationForm):
    is_active = RequiredYesNoRadioButton()


class ChangeCaseRoleForm(ValidationForm):
    case_role = RequiredYesNoRadioButton()


class AssignToCaseForm(ValidationForm):
    ...
