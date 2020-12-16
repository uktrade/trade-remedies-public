from core.templatetags import register
from django.utils.safestring import mark_safe


@register.simple_tag
def count_display(count, prefix=None, postfix=None):
    """
    Template tag to display a simple counter
    Usage:
        {% count_display <num> <prefix> <postfix> %}
    """
    output = ""
    prefix = prefix or ""
    postfix = postfix or ""
    if count:
        output = f"""<div class="task-upload">{prefix} <span class="uploaded-count number-circle larger">{count}</span> {postfix}</div>"""  # noqa: E501
    return mark_safe(output)
