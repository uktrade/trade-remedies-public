from django.shortcuts import redirect
from django.urls import reverse

from cases.v2_forms.accept_representative_invite import WhoIsRegisteringForm
from cases.v2_views.accept_own_org_invitation import (
    AcceptOrganisationInvite,
    AcceptOrganisationSetPassword,
    AcceptOrganisationTwoFactorChoice,
    BaseAcceptInviteView,
)
from config.base_views import FormInvalidMixin
from config.constants import SECURITY_GROUP_ORGANISATION_USER
from registration.forms.forms import NonUkEmployerForm, OrganisationFurtherDetailsForm


class WhoIsRegisteringView(BaseAcceptInviteView, FormInvalidMixin):
    template_name = "v2/accept_invite/new_user/who_is_registering.html"
    form_class = WhoIsRegisteringForm

    def form_valid(self, form):
        self.request.session["who_is_registering"] = form.cleaned_data["who_is_registering"]
        return redirect(
            reverse(
                "accept_representative_invitation_name_and_email",
                kwargs={"invitation_id": self.kwargs["invitation_id"]},
            )
        )


class RegistrationNameAndEmailView(AcceptOrganisationInvite):
    template_name = "v2/accept_invite/new_user/name_and_email.html"

    def dispatch(self, request, *args, **kwargs):
        if self.request.session["who_is_registering"] == "email_recipient":
            self.exclude_fields = ["email"]
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if self.request.session["who_is_registering"] == "organisation_recipient":
            self.request.session["new_user_name"] = form.cleaned_data["name"]
            self.request.session["new_user_email"] = form.cleaned_data["email"]
        else:
            return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "accept_representative_invitation_set_password",
            kwargs={"invitation_id": self.kwargs["invitation_id"]},
        )


class SetPassword(AcceptOrganisationSetPassword):
    def form_valid(self, form):
        if self.request.session["who_is_registering"] == "organisation_recipient":
            # We want to create the new user
            new_user = self.client.users(
                {
                    "name": self.request.session["new_user_name"],
                    "email": self.request.session["new_user_email"],
                    "password": form.cleaned_data["password"],
                }
            )
            self.request.session["new_user_id"] = new_user.id
        else:
            return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "accept_representative_invitation_two_factor_choice",
            kwargs={"invitation_id": self.kwargs["invitation_id"]},
        )


class TwoFactorChoice(AcceptOrganisationTwoFactorChoice):
    def form_valid(self, form):
        # Updating two-factor-choice of user
        if self.request.session["who_is_registering"] == "organisation_recipient":
            # we'll use the ID of the newly created user
            user_id = self.request.session["new_user_id"]
            contact_id = self.client.users(user_id).contact.id
        else:
            user_id = self.invitation.invited_user.id
            contact_id = self.invitation.contact.id
        self.update_two_factor_choice(
            user_id=user_id,
            two_factor_delivery_choice=form.cleaned_data["two_factor_choice"],
            contact_id=contact_id,
            mobile=form.cleaned_data["mobile"],
            mobile_country_code=form.cleaned_data["mobile_country_code"],
        )

        return redirect(
            reverse(
                "accept_representative_invitation_organisation_details",
                kwargs={"invitation_id": self.kwargs["invitation_id"]},
            )
        )


class OrganisationDetails(BaseAcceptInviteView, FormInvalidMixin):
    template_name = "v2/accept_invite/new_user/organisation_details.html"
    form_class = NonUkEmployerForm
    exclude_fields = ["company_name"]

    def form_valid(self, form):
        # Marking the user as active
        self.client.users(self.invitation["invited_user"]["id"]).update({"is_active": True})

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

        # Now let's add the correct groups to the user
        self.client.users(self.invitation.invited_user.id).add_group(
            SECURITY_GROUP_ORGANISATION_USER
        )

        return redirect(
            reverse(
                "accept_representative_invitation_organisation_further_details", kwargs={"invitation_id": self.invitation.id}
            )
        )



class OrganisationFurtherDetails(BaseAcceptInviteView, FormInvalidMixin):
    template_name = "v2/registration/registration_organisation_further_details.html"
    form_class = OrganisationFurtherDetailsForm

    def form_valid(self, form):
        invited_organisation = self.client.organisations(self.invitation.contact.organisation)
        # Let's update the Organisation object with the new details
        invited_organisation.update(
            {
                "organisation_website": form.cleaned_data["company_website"],
                "vat_number": form.cleaned_data.get("company_vat_number"),
                "eori_number": form.cleaned_data.get("company_eori_number"),
                "duns_number": form.cleaned_data.get("company_duns_number"),
            }
        )
        # now let's validate the person's email
        return redirect(
            reverse(
                "request_email_verify_code", kwargs={"user_pk": self.invitation.invited_user.id}
            ) + "?account_created=yes"
        )
