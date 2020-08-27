from core.templatetags import register
from django.utils.safestring import mark_safe


@register.simple_tag
def download_count(documents, prefix=None, postfix=None, warning=None):
    """
    Template tag to display a download files count
    Usage:
        {% task_status <document list> <prefix> <postfix> %}
    """
    count = 0
    for document in documents:
        # We count the number of documents that have been downloaded, not the total numner of downloads
        if document.get("downloads", 0) > 0:
            count = count + 1

    output = ""
    prefix = prefix if prefix is not None else "Downloaded"
    postfix = postfix if postfix is not None else ""
    if count:
        output = f"""<div class="task-upload">{prefix} <span class="uploaded-count number-circle larger">{count}</span> {postfix}</div>"""
    if warning and count < len(documents):
        output += f"""<i class="icon icon-warning pull-right"><span class="visually-hidden">strong alert</span></i>"""
    return mark_safe(output)
