from core.templatetags import register
from django.utils.safestring import mark_safe
from html import escape
import re


@register.simple_tag(takes_context=True)
def download_link(context, document, all_downloadable=None):
    """
    Template tag to display a document link with icon
    Usage:
        {% download_link <document> <all_downloadable> %}
    """
    safe = document.get("safe")
    downloadable = document.get("downloadable")

    extension_icons = {
        "docx": "doc",
        "doc": "doc",
        "odt": "doc",
        "txt": "doc",
        "pdf": "pdf",
        "png": "img",
        "jpg": "img",
        "jpeg": "img",
        "jfif": "img",
        "gif": "img",
        "bmp": "img",
        "xls": "xls",
        "xlsx": "xls",
        "ods": "xls",
        "zip": "zip",
    }

    filename = document.get("name")
    regex = r"\.([^\.]{3,4})$"
    match = re.search(regex, filename)
    extension = match and match.group(1).lower()
    doc_class = extension_icons.get(extension) or ""

    output = (
        f"""<i class="icon-file {doc_class}"></i><span class="filename">{escape(filename)}</span>"""
    )
    #  Show docs as links if they are creted by this user or issued or not confidential
    if safe and downloadable:
        case = context.get("case") or {}
        reference = case.get("reference")
        submission_id = context.get("submission_id")
        output = f"""<a href="/public/case/{reference}/submission/{submission_id}/document/{document.get('id')}/" class="link" target="_blank">{output}</a>"""
    output = f"""<div class="download-link">{output}</div>"""
    return mark_safe(output)
