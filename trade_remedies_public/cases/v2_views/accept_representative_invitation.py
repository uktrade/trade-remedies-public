from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from cases.v2_views.accept_own_org_invitation import (
    AcceptOrganisationInvite,
    AcceptOrganisationSetPassword,
    AcceptOrganisationTwoFactorChoice,
    BaseAcceptInviteView as NormalBaseAcceptInviteView,
)
from config.base_views import FormInvalidMixin
from config.constants import SECURITY_GROUP_ORGANISATION_OWNER
from registration.forms.forms import NonUkEmployerForm, OrganisationFurtherDetailsForm


class BaseAcceptInviteView(NormalBaseAcceptInviteView):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if (
            self.invitation
            and self.invitation.submission
            and not self.invitation.submission.status.sent
        ):
            # The invitation has either been marked as sufficient or deficient by caseworker, stop
            # from proceeding
            return redirect(reverse("login"))
        return response


class RegistrationNameAndEmailView(AcceptOrganisationInvite):
    template_name = "v2/accept_invite/new_user/name_and_email.html"

    def dispatch(self, request, *args, **kwargs):
        self.exclude_fields = ["email"]
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            "accept_representative_invitation_set_password",
            kwargs={"invitation_id": self.kwargs["invitation_id"]},
        )


class SetPassword(AcceptOrganisationSetPassword):
    def get_success_url(self):
        return reverse(
            "accept_representative_invitation_two_factor_choice",
            kwargs={"invitation_id": self.kwargs["invitation_id"]},
        )


class TwoFactorChoice(AcceptOrganisationTwoFactorChoice):
    def form_valid(self, form):
        user_id = self.invitation.invited_user.id
        contact_id = self.invitation.contact.id
        self.update_two_factor_choice(
            user_id=user_id,
            two_factor_delivery_choice=form.cleaned_data["two_factor_choice"],
            contact_id=contact_id,
            mobile=form.cleaned_data["mobile"],
            mobile_country_code=form.cleaned_data["mobile_country_code"],
        )

        if not self.invitation.organisation_details_captured:
            # new organisation, capture details
            return redirect(
                reverse(
                    "accept_representative_invitation_organisation_details",
                    kwargs={"invitation_id": self.kwargs["invitation_id"]},
                )
            )
        else:
            # organisation details already exist, no need to re-request details from invitee

            # Marking the user as active
            self.client.users(self.invitation.invited_user.id).update({"is_active": True})

            if self.invitation.invitation_type == 2:
                # Now let's add the correct groups to the user, so they can log in and the
                # rest of the invitation can be processed
                self.client.users(self.invitation.invited_user.id).add_group(
                    SECURITY_GROUP_ORGANISATION_OWNER
                )

                # marking the submission as received, so it can be verified by the caseworker
                self.client.submissions(self.invitation.submission.id).update_submission_status(
                    "received"
                )
                self.invitation.update({"accepted_at": timezone.now()})
            elif self.invitation.invitation_type == 3:
                self.client.users(self.invitation.invited_user.id).add_group(
                    self.invitation.organisation_security_group
                )

                # Set the contact as not draft, as we know we have details for it
                self.client.contacts(self.invitation.contact.id).update({"draft": False})

            # First let's add the invitee as an admin user to their organisation, this was also
            # add them to the required group
            self.client.organisations(self.invitation.contact.organisation).add_user(
                user_id=self.invitation.invited_user.id,
                group_name=SECURITY_GROUP_ORGANISATION_OWNER,
                confirmed=True,
                fields=["id"],
            )

            # now let's validate the person's email
            return redirect(
                reverse(
                    "request_email_verify_code", kwargs={"user_pk": self.invitation.invited_user.id}
                )
                + "?account_created=yes"
            )


# Need to keep for when caseworker invites and the organisation was created as
# part of the invite
class OrganisationDetails(BaseAcceptInviteView, FormInvalidMixin):
    template_name = "v2/accept_invite/new_user/organisation_details.html"
    form_class = NonUkEmployerForm
    exclude_fields = ["company_name"]

    def form_valid(self, form):
        # Marking the user as active
        self.client.users(self.invitation.invited_user.id).update({"is_active": True})

        invited_organisation = self.client.organisations(self.invitation.contact.organisation)
        # Let's update the Organisation object with the new details
        invited_organisation.update(
            {
                "address": form.cleaned_data["address_snippet"],
                "post_code": form.cleaned_data.get("post_code"),
                "companies_house_id": form.cleaned_data.get("company_number"),
                "country": form.cleaned_data.get("country"),
            }
        )

        if self.invitation.invitation_type == 2:
            # Now let's add the correct groups to the user, so they can log in and the rest of the
            # invitation can be processed
            self.client.users(self.invitation.invited_user.id).add_group(
                SECURITY_GROUP_ORGANISATION_OWNER
            )
        elif self.invitation.invitation_type == 3:
            self.client.users(self.invitation.invited_user.id).add_group(
                self.invitation.organisation_security_group
            )

            # Set the organisation and contact as not draft, as we know we have details for it
            self.client.organisations(self.invitation.organisation.id).update({"draft": False})
            self.client.contacts(self.invitation.contact.id).update({"draft": False})

        return redirect(
            reverse(
                "accept_representative_invitation_organisation_further_details",
                kwargs={"invitation_id": self.invitation.id},
            )
        )


class OrganisationFurtherDetails(BaseAcceptInviteView, FormInvalidMixin):
    template_name = "v2/registration/registration_organisation_further_details.html"
    form_class = OrganisationFurtherDetailsForm

    def form_valid(self, form):
        # Let's update the Organisation object with the new details
        self.client.organisations(self.invitation.contact.organisation).update(
            {
                "organisation_website": form.cleaned_data["company_website"],
                "vat_number": form.cleaned_data.get("company_vat_number"),
                "eori_number": form.cleaned_data.get("company_eori_number"),
                "duns_number": form.cleaned_data.get("company_duns_number"),
            }
        )

        if self.invitation.invitation_type == 2:
            # marking the submission as received, so it can be verified by the caseworker
            self.client.submissions(self.invitation.submission.id).update_submission_status(
                "received"
            )
            self.invitation.update({"accepted_at": timezone.now()})

        # First let's add the invitee as an admin user to their organisation, this was also
        # add them to the required group
        self.client.organisations(self.invitation.contact.organisation).add_user(
            user_id=self.invitation.invited_user.id,
            group_name=SECURITY_GROUP_ORGANISATION_OWNER,
            confirmed=True,
            fields=["id"],
        )

        # new organisation details have now been captured
        self.invitation.update({"organisation_details_captured": True})

        # now let's validate the person's email
        return redirect(
            reverse(
                "request_email_verify_code", kwargs={"user_pk": self.invitation.invited_user.id}
            )
            + "?account_created=yes"
        )
