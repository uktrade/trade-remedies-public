from core.templatetags import register
from django.utils.safestring import mark_safe


@register.simple_tag
def task_link_toggle(submission, section, title, enabled=False, link=None):
    """
    Template tag to display a link or a disabled link
    Usage:
        {% link_toggle url title enabled %}
    """
    output = ""
    case_id = submission and submission.get("case", {}).get("id")
    submission_id = submission and submission.get("id")
    if enabled:
        if link is None:
            link = (
                f"/case/{case_id}/submission/{submission_id}/{section}/"
                if case_id
                else f"/case/{section}/"
            )
        output = f"""<a class="task-name" href="{link}">{title}</a>"""
    else:
        output = f"""<span>{title}</span>"""
    return mark_safe(output)
