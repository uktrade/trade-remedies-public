from core.templatetags import register
from django.conf import settings

"""
Template tag to display organisation initialism
Usage:
    {% organisation_initialism %}
"""


@register.simple_tag
def organisation_initialism():
    return settings.ORGANISATION_INITIALISM
