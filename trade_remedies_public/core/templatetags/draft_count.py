from core.templatetags import register
from django.utils.safestring import mark_safe


@register.simple_tag
def draft_count(submission):
    """
    Template tag to display a task status indicator
    Usage:
        {% task_status COMPLETE|INPROGRESS %}
    """
    output = ""
    count = submission.get("version")
    if count:
        if not submission.get("status").get("sufficient"):
            count = count - 1
        output = f"""<div class="task-upload pull-right">
            Drafts submitted
            <span class="uploaded-count number-circle larger">{count}</span></div>"""
    return mark_safe(output)
