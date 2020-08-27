from core.templatetags import register
from django.utils.safestring import mark_safe
import datetime

"""
Template tag to display a formatted date given an iso date string
Usage:
    {% format_date datestr %}
"""


@register.simple_tag
def format_date(date, format_str="%d %b %Y %H:%M:%S"):
    if isinstance(date, str) and len(date) > 18:
        date = datetime.datetime.strptime(date[:19], "%Y-%m-%dT%H:%M:%S")
        return mark_safe(datetime.datetime.strftime(date, format_str))
    return "n/a"
