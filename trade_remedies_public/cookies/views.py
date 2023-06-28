# Views to handle the cookie policy associated with registering

import json
import re
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView

from core.utils import internal_redirect, set_cookie
from registration.views import BaseRegisterView


class CookiePolicyView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, "cookies/cookie_policy.html", {})


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
            "cookies/cookies.html",
            {
                "cookie_policy": cookie_policy,
                "redirect_url": redirect_url,
            },
        )

    def post(self, request, *args, **kwargs):
        action = request.POST.get("cookies", "reject")
        accept_gi = "on" if action == "accept" else "off"
        redirect_url = request.POST.get("redirect_url") or reverse("landing")
        separator = "?" if redirect_url.find("?") == -1 else "#"
        redirect_url = f"{redirect_url}{separator}cookie-policy-updated=1"
        response = internal_redirect(redirect_url, reverse("landing"))
        policy = json.dumps({"accept_gi": accept_gi})

        if accept_gi != "on":
            # delete ga cookies by regex
            regex = r"^_g(a|i)"
            for key, value in request.COOKIES.items():
                if re.search(regex, key):
                    response.delete_cookie(key)
        set_cookie(response, "cookie_policy", policy)
        return response
