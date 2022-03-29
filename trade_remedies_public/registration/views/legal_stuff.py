import json
import re
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from django.contrib.auth import logout
from django_countries import countries

from core.models import TransientUser
from core.utils import (
    validate,
    get,
    set_cookie,
)
from trade_remedies_client.exceptions import APIException
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
from core.validators import (
    registration_validators,
    base_registration_validators,
)
from core.utils import internal_redirect
from config.constants import SECURITY_GROUP_THIRD_PARTY_USER


class TermsAndConditionsView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, "registration/terms_and_conditions.html", {})


class AccessibilityStatementView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, "registration/accessibility_statement.html", {})
