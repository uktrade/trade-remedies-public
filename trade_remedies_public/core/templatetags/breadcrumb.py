from core.templatetags import register
from django.utils.safestring import mark_safe

"""
Template tag to display a breadcrumb trail
Usage:
    {% format_date datestr %}
"""


@register.simple_tag
def breadcrumb(title, link):
    output = '<li class="">'
    output += f"""<a data-track-category="breadcrumbClicked" data-track-action="1" class="" aria-current="false" href="{ link }">{ title }</a>"""
    output += "</li>"
    return mark_safe(output)
