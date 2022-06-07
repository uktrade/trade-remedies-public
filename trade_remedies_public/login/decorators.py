from functools import wraps

from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse
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
            except APIException as exc:
                if hasattr(exc, "detail"):
                    request.request.session["form_errors"] = exc.detail
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

                # We're setting an empty HTML anchor as 302 redirects preserve anchors between
                # requests, and if the user has clicked on the anchor link in the error summaries
                # box, we don't want the browser to continuously focus on that troublesome input
                return redirect(f"{request.request.path}#")

        return _wrapped_view_func

    return decorator
