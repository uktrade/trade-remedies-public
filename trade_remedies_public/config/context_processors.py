"""
user_context context processor providing a global user context to
templates which contains the current user's token and basic info.
If the request contains relevant case,  submission or organisation ids
those will be preloaded and ready for the request processing.
"""
import json
from django.urls import reverse
from trade_remedies_client.client import Client
from config.version import __version__


def motd_context(request):
    return {"public_notice": Client().get_system_parameters("PUBLIC_NOTICE").get("value")}


def user_context(request):
    token = request.session.get("token")
    context = {
        "authenticated": bool(token and request.user.is_authenticated),
        "user": request.user,
        "token": token,
        "current_organisation": None,
        "session": request.session,
        "within_2fa": request.path == reverse("two_factor"),
        "within_verify": request.path == reverse("email_verify"),
    }
    request_kwargs = request.resolver_match.kwargs if request.resolver_match else {}
    resolved_organisation_id = request_kwargs.get("organisation_id") or request.session.get(
        "organisation_id"
    )
    resolved_submission_id = request_kwargs.get("submission_id")
    resolved_case_id = request_kwargs.get("case_id")
    client = None
    if resolved_case_id and resolved_submission_id:
        client = Client(request.user.token)
        context["submission"] = client.get_submission_public(
            resolved_case_id, resolved_submission_id
        )
        # context['current_organisation'] = context['submission']['organisation']
    if resolved_organisation_id and not context["current_organisation"]:
        client = Client(request.user.token) if not client else client
        context["current_organisation"] = client.get_organisation(resolved_organisation_id)
    return context


def version_context(request):
    return {"version": {"api": request.session.get("version", ""), "ui": __version__}}


def cookie_management(request):
    cookie_policy_set = True
    try:
        cookie_updated = request.GET.get("cookie-policy-updated")
        cookie_policy = json.loads(request.COOKIES.get("cookie_policy"))
    except Exception as exception:
        cookie_updated = None
        cookie_policy = {"accept_gi": "on"}
        cookie_policy_set = False
    return {
        "cookie_policy": cookie_policy,
        "cookie_policy_updated": cookie_updated,
        "cookie_policy_set": cookie_policy_set,
    }


def v2_error_handling(request):
    """Pops the errors from the request.session for front-end rendering."""
    if form_errors := request.session.pop("form_errors", None):
        return {"form_errors": form_errors}
    return {}
