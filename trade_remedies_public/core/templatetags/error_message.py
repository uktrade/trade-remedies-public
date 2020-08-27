from core.templatetags import register
from django.utils.safestring import mark_safe


@register.simple_tag
def error_message(errors, key=None):
    """
    Display one or more error messages
    """
    output = ""
    if isinstance(errors, dict):
        if key and errors and key in errors:
            message = errors[key]
            output = f'<span id="{key}_error" class="error-message">{message}</span>'
        elif errors and not key:
            output = "<br/>".join(
                [f'<span class="error-message">{message}</span>' for key, message in errors.items()]
            )
    elif isinstance(errors, str):
        output = f'<span class="error-message">{errors}</span>'
    return mark_safe(output)
