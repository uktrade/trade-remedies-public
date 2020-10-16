from core.templatetags import register
from django.utils.safestring import mark_safe


@register.simple_tag
def upload_count(count, second_count=None, deficient_count=0):
    """
    Template tag to display a task status indicator
    Usage:
        {% task_status COMPLETE|INPROGRESS %}
    """
    in_progress = ""
    output = ""

    if (second_count is not None and second_count != count) or (int(deficient_count) != 0):
        in_progress = "in-progress"
    if count:
        output = f"""<div class="task-upload {in_progress}">Files uploaded <span class="uploaded-count number-circle larger">{count}</span></div>"""   # noqa: E501
    return mark_safe(output)
