from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import TemplateView
from v2_api_client.mixins import APIClientMixin

from config.base_views import FormInvalidMixin
from registration.forms import PasswordForm, RegistrationStartForm, TwoFactorChoiceForm


class BaseAcceptInviteView(APIClientMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invitation"] = self.client.invitations(self.kwargs['invitation_id'])
        return context


class InvitationNotFound(TemplateView):
    template_name = "v2/accept_invite/invitation_not_found.html"


class AcceptOrganisationInvite(BaseAcceptInviteView, FormInvalidMixin):
    template_name = "v2/accept_invite/own_organisation_start.html"
    form_class = RegistrationStartForm

    def dispatch(self, request, *args, **kwargs):
        try:
            invitation = self.client.invitations(self.kwargs['invitation_id'])
            if invitation["accepted_at"]:
                # The invitation has already been accepted, it is invalid
                return render(
                    request=request,
                    template_name="v2/accept_invite/invitation_not_found.html",
                    context={},
                )
        except Exception as e:
            if getattr(e, "status_code", None) == 404:
                return render(
                    request=request,
                    template_name="v2/accept_invite/invitation_not_found.html",
                    context={},
                )
            raise e

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        invitation = self.get_context_data()["invitation"]
        contact_id = invitation["contact"]["id"]
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
        self.client.invitations(self.kwargs['invitation_id']).create_user_from_invitation(
            password=form.cleaned_data["password"]
        )
        return redirect(
            reverse(
                "accept_invite_two_factor_choice",
                kwargs={"invitation_id": self.kwargs["invitation_id"]},
            )
        )


class AcceptOrganisationTwoFactorChoice(BaseAcceptInviteView, FormInvalidMixin):
    template_name = "v2/registration/registration_2fa_choice.html"
    form_class = TwoFactorChoiceForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_email"] = context["invitation"]["contact"]["email"]
        return context

    def form_valid(self, form):
        invitation = self.get_context_data()["invitation"]
        contact_id = invitation["contact"]["id"]

        # Marking the user as active
        self.client.users(invitation['invited_user']['id']).update({"is_active": True})

        if form.cleaned_data["two_factor_choice"] == "mobile":
            # First updating the mobile number in the DB
            self.client.contacts(contact_id).update({
                "phone": form.cleaned_data["mobile"],
                "country": form.cleaned_data["mobile_country_code"],
            })

        # Then changing the chosen delivery type of two-factor authentication
        two_factor_delivery_choice = (
            "sms" if form.cleaned_data["two_factor_choice"] == "mobile" else "email"
        )

        self.client.two_factor_auths(invitation['invited_user']['id']).update({
            "delivery_type": two_factor_delivery_choice
        })

        # Now adding the user to the organisation in question
        self.client.organisations(invitation['organisation_id']).update({
            "user_id": invitation["invited_user"]["id"],
            "organisation_security_group": invitation["organisation_security_group"],
            "confirmed": False,
        })

        # Redirect to email verification page
        return redirect(
            reverse(
                "request_email_verify_code", kwargs={"user_pk": invitation["invited_user"]["id"]}
            )
            + "?account_created=yes"
        )
