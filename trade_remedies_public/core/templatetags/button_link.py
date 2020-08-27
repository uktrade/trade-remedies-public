from core.templatetags import register
from django.utils.safestring import mark_safe


@register.simple_tag
def button_link(uri, label):
    """
    Template tag to display a link styled as a button back to the task list
    Usage:
        {% button_link uri label %}
    """
    output = ""
    if uri and label:
        output = f"""<a class="button" href="{uri}">{label}</a>"""
    return mark_safe(output)
