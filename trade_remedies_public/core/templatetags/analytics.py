import os
import base64

from core.templatetags import register
from django.utils.safestring import mark_safe
from django.conf import settings


@register.simple_tag(takes_context=True)
def analytics(context, body=False):
    """
    Template tag to render Google Analytics tag
    Usage:
        {% analytics %}
    """
    if settings.DEBUG:
        return ""

    output = []
    cookie_policy = context.get("cookie_policy") or {}
    if cookie_policy.get("accept_gi") == "on":
        # solution from:
        # https://github.com/mozilla/django-csp/blob/e209183b0956bfe2cef562bece18a6a526479c80/csp/middleware.py
        nonce = None
        request = context.get("request")
        if request:
            nonce = getattr(request, "_csp_nonce", None)
            if not nonce:
                nonce = base64.b64encode(os.urandom(16)).decode("ascii")
                setattr(request, "_csp_nonce", nonce)
        if body:
            output = [
                "<!-- Google Tag Manager (noscript) -->",
                '<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=',
                settings.GOOGLE_ANALYTICS_TAG_MANAGER_ID,
                '" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>',  # noqa: E501
                "<!-- End Google Tag Manager (noscript) -->",
            ]
        else:
            output = [
                "<!-- Google Tag Manager -->",
                "<script nonce='",
                nonce or "",
                "'>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':",
                "new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],",
                "j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=",
                "'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);",  # noqa: E501
                "})(window,document,'script','dataLayer','",
                settings.GOOGLE_ANALYTICS_TAG_MANAGER_ID,
                "');</script>",
                "<!-- End Google Tag Manager -->",
            ]
    return mark_safe("".join(output))
