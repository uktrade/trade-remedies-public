from functools import wraps

from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse
from requests import HTTPError
from trade_remedies_client.exceptions import APIException


def v2_error_handling(redirection_url_resolver=None):
    """Decorator that adds custom APIException V2 error handling to a view method.
    CustomValidationException errors thrown on the API side will be passed back to the public site,
    and errors summary/text will be added to the request.session for rendering in the front-end"""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view_func(request, *args, **kwargs):
            try:
                response = view_func(request, *args, **kwargs)
                return response
            except (APIException, HTTPError) as exc:
                if hasattr(exc, "response"):
                    request.request.session["form_errors"] = exc.response.json()
                    request.request.session.is_modified = True
                    if redirection_url_resolver:
                        try:
                            redirection_url = reverse(redirection_url_resolver)
                            return redirect(redirection_url)
                        except NoReverseMatch:
                            pass
                else:
                    # We're dealing with an unhandled error, let it (unfortunately) propagate and
                    # sentry will pick it up
                    raise exc

                return redirect(request.request.path)

        return _wrapped_view_func

    return decorator
