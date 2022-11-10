from django import forms

from config.constants import (
    SECURITY_GROUP_ORGANISATION_OWNER,
    SECURITY_GROUP_ORGANISATION_USER,
)
from config.forms import ValidationForm


class WhoAreYouInvitingForm(ValidationForm):
    who_are_you_inviting = forms.ChoiceField(
        choices=(("employee", "employee"), ("representative", "representative")),
        error_messages={"required": "who_are_you_inviting_empty"},
    )


class WhoAreYouInvitingNameEmailForm(ValidationForm):
    team_member_name = forms.CharField(
        error_messages={"required": "who_are_you_inviting_name_missing"}
    )
    team_member_email = forms.EmailField(
        error_messages={
            "required": "who_are_you_inviting_email_missing",
            "invalid": "who_are_you_inviting_email_invalid_format",
        }
    )


class SelectPermissionsForm(ValidationForm):
    type_of_user = forms.ChoiceField(
        choices=(
            (SECURITY_GROUP_ORGANISATION_USER, SECURITY_GROUP_ORGANISATION_USER),
            (SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_OWNER),
        ),
        error_messages={"required": "invite_permissions_missing"},
    )


class ChooseCaseForm(ValidationForm):
    which_user_case = forms.CharField(
        error_messages={"required": "invite_which_cases_not_selected"}
    )


class SelectCaseForm(ValidationForm):
    user_case = forms.CharField(error_messages={"required": "invite_no_case_selected"})


class SelectOrganisationForm(ValidationForm):
    organisation = forms.CharField(
        error_messages={"required": "invite_who_does_your_representative_work_for_missing"}
    )


class InviteExistingRepresentativeDetailsForm(ValidationForm):
    contact_name = forms.CharField(
        error_messages={"required": "invite_existing_representative_no_contact_name"}
    )
    contact_email = forms.EmailField(
        error_messages={
            "required": "invite_existing_representative_no_contact_email",
            "invalid": "invite_existing_representative_invalid_email",
        }
    )


class InviteNewRepresentativeDetailsForm(ValidationForm):
    organisation_name = forms.CharField(
        error_messages={"required": "invite_new_representative_no_organisation_name"}
    )
    contact_name = forms.CharField(
        error_messages={"required": "invite_new_representative_no_contact_name"}
    )
    contact_email = forms.EmailField(
        error_messages={
            "required": "invite_new_representative_no_contact_email",
            "invalid": "invite_new_representative_invalid_email",
        }
    )
