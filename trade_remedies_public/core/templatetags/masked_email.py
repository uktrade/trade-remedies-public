from core.templatetags import register
from django.utils.safestring import mark_safe


@register.simple_tag
def masked_email(email):
    """
    Mask a users email address:
        harel@harelmalka.com
        becomes
        ha****@*******.com
    Usage:
        {% masked_email email %}
    """
    try:
        user, domain = email.split("@")
        visible_user_index = 2 if len(user) > 2 else 1
        masked_user = user[0:visible_user_index] + ("*" * 5)
        toplevel = domain.split(".")[-1]
        masked_email = f"{masked_user}@**********.{toplevel}"
    except Exception as exception:
        return mark_safe(email)
    return mark_safe(masked_email)
