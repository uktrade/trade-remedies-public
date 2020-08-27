from core.templatetags import register
from django.utils.safestring import mark_safe

"""
Template tag to return 'a' or 'an' depending on the noun given
'an' if it starts with a vowel, otherwise 'a'
Usage:
    {% a_or_an:mystring %}
"""


@register.simple_tag(takes_context=False)
def a_or_an(str):
    return "an" if str[0:1].upper() in ["A", "E", "I", "O", "U"] else "a"
