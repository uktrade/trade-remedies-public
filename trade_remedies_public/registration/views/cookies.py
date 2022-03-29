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


class CookiePolicyView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, "registration/cookie_policy.html", {})


class CookieSettingsView(BaseRegisterView):
    def get(self, request, *args, **kwargs):
        redirect_url = request.GET.get("url") or ""
        cookie_policy = {"accept_gi": "off"}
        try:
            cookie_policy = json.loads(request.COOKIES.get("cookie_policy"))
        except Exception as exception:
            print("Bad one", exception)
        return render(
            request,
            "registration/cookies.html",
            {
                "cookie_policy": cookie_policy,
                "redirect_url": redirect_url,
            },
        )

    def post(self, request, *args, **kwargs):
        accept_gi = request.POST.get("accept_gi")
        redirect_url = request.POST.get("redirect_url") or "/dashboard/"
        separator = "?" if redirect_url.find("?") == -1 else "#"
        redirect_url = f"{redirect_url}{separator}cookie-policy-updated=1"
        response = internal_redirect(redirect_url, "/dashboard/")
        policy = json.dumps({"accept_gi": accept_gi})

        if accept_gi != "on":
            # delete ga cookies by regex
            regex = r"^_g(a|i)"
            for key, value in request.COOKIES.items():
                if re.search(regex, key):
                    response.delete_cookie(key)
        set_cookie(response, "cookie_policy", policy)
        return response
