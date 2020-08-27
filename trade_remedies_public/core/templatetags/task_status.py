from core.templatetags import register
from django.utils.safestring import mark_safe


@register.simple_tag
def task_status(state, as_bool=False):
    """
    Template tag to display a task statuc indicator
    Usage:
        {% task_status COMPLETE|INPROGRESS %}
    """
    output = ""
    if as_bool:
        state = "COMPLETE" if bool(state) else ""
    if state == "COMPLETE":
        output = """<strong class="task-completed">Completed</strong>"""
    elif state == "INPROGRESS":
        output = """<strong class="task-completed progress">In progress</strong>"""
    return mark_safe(output)
