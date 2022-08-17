from config.forms import ValidationForm
from django import forms
from django.core.validators import RegexValidator

from trade_remedies_public.config.constants import SECURITY_GROUP_ORGANISATION_OWNER, \
    SECURITY_GROUP_ORGANISATION_USER
from trade_remedies_public.config.forms.validators import email_regex_validator


class WhoAreYouInvitingForm(ValidationForm):
    who_are_you_inviting = forms.ChoiceField(
        choices=(
            ("employee", "employee"),
            ("representative", "representative")
        ),
        error_messages={"required": "who_are_you_inviting_empty"}
    )


class WhoAreYouInvitingNameEmailForm(ValidationForm):
    team_member_name = forms.CharField(
        error_messages={"required": "who_are_you_inviting_name_missing"}
    )
    team_member_email = forms.EmailField(
        error_messages={
            "required": "who_are_you_inviting_email_missing",
        },
        validators=[
            RegexValidator(
                email_regex_validator,
                "who_are_you_inviting_email_invalid_format",
            )
        ]
    )


class SelectPermissionsForm(ValidationForm):
    type_of_user = forms.ChoiceField(
        choices=(
            (SECURITY_GROUP_ORGANISATION_USER, SECURITY_GROUP_ORGANISATION_USER),
            (SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_OWNER)
        ),
        error_messages={"required": "invite_permissions_missing"}
    )


class SelectCaseForm(ValidationForm):
    cases = forms.CharField(error_messages={"required": "invite_no_case_selected"})


class SelectOrganisationForm(ValidationForm):
    organisation = forms.CharField(error_messages={"required": "invite_no_case_selected"})
