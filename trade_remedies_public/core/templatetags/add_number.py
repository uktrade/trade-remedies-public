from core.templatetags import register
from django.utils.safestring import mark_safe

"""
Template tag to set a content variable
Usage:
    {% set 'my_field' value %}
"""


@register.simple_tag(takes_context=True)
def add_number(context, var_name, value, print=False):
    try:
        old_val = int(context[var_name])
    except Exception as exc:
        old_val = 0
    try:
        value = int(value)
        context[var_name] = old_val + value
    except:
        return "Invalid"

    return context[var_name] if print else ""
