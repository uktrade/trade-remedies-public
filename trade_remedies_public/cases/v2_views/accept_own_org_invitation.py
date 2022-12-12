from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import TemplateView
from v2_api_client.exceptions import NotFoundError
from v2_api_client.mixins import APIClientMixin

from config.base_views import FormInvalidMixin
from registration.forms.forms import PasswordForm, RegistrationStartForm, TwoFactorChoiceForm


class BaseAcceptInviteView(APIClientMixin, TemplateView):
    def dispatch(self, request, *args, **kwargs):
        try:
            invitation = self.client.invitations(self.kwargs["invitation_id"])
            if invitation["accepted_at"]:
                # The invitation has already been accepted, it is invalid
                return render(
                    request=request,
                    template_name="v2/accept_invite/invitation_already_used.html",
                    context={},
                )
            self.invitation = invitation
        except NotFoundError:
            # The invitation doesn't exist, it's DEFINITELY invalid
            return render(
                request=request,
                template_name="v2/accept_invite/invitation_not_found.html",
                context={},
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invitation"] = self.invitation
        return context


class AcceptOrganisationInvite(BaseAcceptInviteView, FormInvalidMixin):
    template_name = "v2/accept_invite/own_organisation_start.html"
    form_class = RegistrationStartForm

    def form_valid(self, form):
        contact_id = self.invitation["contact"]["id"]
        self.client.contacts(contact_id).update({"name": form.cleaned_data["name"]})
        return redirect(
            reverse(
                "accept_invite_set_password", kwargs={"invitation_id": self.kwargs["invitation_id"]}
            )
        )


class AcceptOrganisationSetPassword(BaseAcceptInviteView, FormInvalidMixin):
    template_name = "v2/registration/registration_set_password.html"
    form_class = PasswordForm

    def form_valid(self, form):
        new_user = self.invitation.create_user_from_invitation(
            password=form.cleaned_data["password"]
        )
        # adding the user to the correct groups
        self.client.users(new_user["id"]).add_group(self.invitation.organisation_security_group)
        return redirect(
            reverse(
                "accept_invite_two_factor_choice",
                kwargs={"invitation_id": self.kwargs["invitation_id"]},
            )
        )


class AcceptOrganisationTwoFactorChoice(BaseAcceptInviteView, FormInvalidMixin):
    template_name = "v2/registration/registration_2fa_choice.html"
    form_class = TwoFactorChoiceForm

    def update_two_factor_choice(
        self,
        user_id,
        two_factor_delivery_choice,
        contact_id=None,
        mobile=None,
        mobile_country_code=None,
    ):
        """Helper function to update the two-factor choice of a user instance from an invitation
        object.
        """
        if two_factor_delivery_choice == "mobile":
            # First updating the mobile number in the DB
            self.client.contacts(contact_id).update(
                {
                    "phone": mobile,
                    "country": mobile_country_code,
                }
            )

        # Then changing the chosen delivery type of two-factor authentication
        two_factor_delivery_choice = "sms" if two_factor_delivery_choice == "mobile" else "email"

        self.client.two_factor_auths(user_id).update({"delivery_type": two_factor_delivery_choice})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_email"] = self.invitation.contact.email
        return context

    def form_valid(self, form):
        contact_id = self.invitation["contact"]["id"]

        # Marking the user as active
        self.client.users(self.invitation["invited_user"]["id"]).update({"is_active": True})

        # Updating two-factor-choice of user
        self.update_two_factor_choice(
            user_id=self.invitation["invited_user"]["id"],
            two_factor_delivery_choice=form.cleaned_data["two_factor_choice"],
            contact_id=contact_id,
            mobile=form.cleaned_data["mobile"],
            mobile_country_code=form.cleaned_data["mobile_country_code"],
        )

        # if this is a caseworker invite, we want them to provide organisation details, redirect
        if self.invitation.invitation_type == 3:
            return redirect(
                reverse(
                    "accept_representative_invitation_organisation_details",
                    kwargs={"invitation_id": self.invitation.id},
                )
            )

        # Redirect to email verification page
        return redirect(
            reverse(
                "request_email_verify_code",
                kwargs={"user_pk": self.invitation["invited_user"]["id"]},
            )
            + "?account_created=yes"
        )
