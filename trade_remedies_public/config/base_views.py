from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView
from v2_api_client.mixins import APIClientMixin

from trade_remedies_public.config.constants import SECURITY_GROUP_ORGANISATION_OWNER, \
    SECURITY_GROUP_ORGANISATION_USER
from trade_remedies_public.core.base import GroupRequiredMixin


class BasePublicView(LoginRequiredMixin, GroupRequiredMixin, APIClientMixin):
    """A base view used to provide common mixins and attributes to public views.

    Forces the user to be logged in and belong to and own an organisation.
    Also mixes in the V2 API Client which can be called with self.client()
    """
    groups_required = [SECURITY_GROUP_ORGANISATION_OWNER, SECURITY_GROUP_ORGANISATION_USER]


class BasePublicFormView(BasePublicView, FormView):
    """The same as BasePublicView, but adds the FormView generic mixin and a form_invalid
    function which will assign the form errors to the request session so they can be properly
    rendered in the front-end.
    """

    def form_invalid(self, form):
        form.assign_errors_to_request(self.request)
        return super().form_invalid(form)
