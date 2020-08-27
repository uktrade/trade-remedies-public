from core.templatetags import register
from django.utils.safestring import mark_safe

"""
Template tag to display a breadcrumb trail
Usage:
    {% format_date datestr %}
"""


@register.simple_tag
def breadcrumbs(breadcrumbs):
    output = ['<div class="breadcrumbs" data-module="track-click">']
    output.append("<ol>")
    crumbs = breadcrumbs.split(">>")
    for crumb in crumbs:
        spl_crum = crumb.split("|")
        if len(spl_crum) > 1:
            output.append(f'<li><a href="{spl_crum[1]}">{spl_crum[0]}</a></li>')
        else:
            output.append(f"<li>{spl_crum[0]}</li>")
    output.append("</ol></div>")
    return mark_safe("".join(output))
