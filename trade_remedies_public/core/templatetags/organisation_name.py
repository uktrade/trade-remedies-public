from core.templatetags import register
from django.conf import settings

"""
Template tag to display organisation name
    {% organisation_name %}
"""


@register.simple_tag
def organisation_name():
    return settings.ORGANISATION_NAME
