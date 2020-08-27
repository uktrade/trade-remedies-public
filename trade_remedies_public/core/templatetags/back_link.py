from core.templatetags import register
from django.utils.safestring import mark_safe


@register.simple_tag
def back_link(case_id, submission_id):
    """
    Template tag to display a link back to the task list
    Usage:
        {% back_link case-uuid submission-uuid %}
    """
    output = ""
    if case_id and submission_id:
        output = f"""<a href="/case/{case_id}/submission/{submission_id}/">Back to menu</a>"""
    return mark_safe(output)
