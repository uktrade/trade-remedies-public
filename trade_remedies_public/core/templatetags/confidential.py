from core.templatetags import register

"""
Template tag to display an indicator for confidential or non confidential document
Usage:
    {% confidential confidential_boolean %}
"""


@register.simple_tag
def confidential(confidential):
    return "[CONF]" if confidential else "[NONCONF]"
