from core.templatetags import register
from django.utils.safestring import mark_safe

"""
Template tag to set a content variable
Usage:
    {% set 'my_field' value %}
"""


@register.simple_tag(takes_context=True)
def set(context, var_name, value):
    context[var_name] = value
    if not context.get("store"):
        context["store"] = {}
    context["store"][var_name] = value
    return ""
