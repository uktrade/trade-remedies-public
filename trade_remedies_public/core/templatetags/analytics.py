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
    request = context.get("request")
    if cookie_policy.get("accept_gi") == "on":
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
                request.csp_nonce if request else "",
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
