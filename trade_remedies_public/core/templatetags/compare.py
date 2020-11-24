from core.templatetags import register

"""
Template tag to compare two values and set the result as a boolean named context variable
Usage:
    {% compare 'bool_result' thing.status 'COMPLETE' %}
"""


@register.simple_tag(takes_context=True)
def compare(context, var_name, value1, value2):
    context[var_name] = value1 == value2
    return ""
