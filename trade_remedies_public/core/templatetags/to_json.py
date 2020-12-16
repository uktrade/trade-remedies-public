from core.templatetags import register
import json
from django.utils.safestring import mark_safe

"""
A template filter to display data in JSON format - useful when debugging the UI.

Usage:
    {% data|to_json %}
"""


@register.filter
def to_json(data, no_escape=None):
    if no_escape:
        return mark_safe(json.dumps(data, sort_keys=True, indent=4))
    else:
        return json.dumps(data, sort_keys=True, indent=4)
