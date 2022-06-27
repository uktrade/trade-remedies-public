from functools import wraps

from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse
from requests import HTTPError
from trade_remedies_client.exceptions import APIException


def catch_form_errors(redirection_url_resolver=None):  # noqa: C901
    """Catch form errors on submission and redirect to specified page where they can be displayed.

    Checks if errors are raised when calling the API whilst submitting, store those form errors in
    the request and session, and redirect the user to a specified URL where those errors can be
    rendered in a nice way. Uses the add_form_errors context processor to add those form errors
    to the HTML context dictionary for rendering.

    :param str redirection_url_resolver: The name of the URL to redirect the user to if there are
    errors with the form. NOT the actual URL, but just the name="" attribute of the URL defined in
    urls.py
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view_func(request, *args, **kwargs):
            try:
                response = view_func(request, *args, **kwargs)
                return response
            except (APIException, HTTPError) as exc:
                if hasattr(exc, "response"):
                    request.request.session["form_errors"] = exc.response.json()
                elif hasattr(exc, "detail"):
                    request.request.session["form_errors"] = exc.detail
                else:
                    # We're dealing with an unhandled error, let it (unfortunately) propagate and
                    # sentry will pick it up
                    raise exc
                request.request.session.is_modified = True
                if redirection_url_resolver:
                    try:
                        redirection_url = reverse(redirection_url_resolver)
                        return redirect(redirection_url)
                    except NoReverseMatch:
                        pass
                return redirect(request.request.path)

        return _wrapped_view_func

    return decorator
