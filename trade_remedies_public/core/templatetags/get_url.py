from core.templatetags import register
from django.urls import reverse


@register.simple_tag
def get_url(url_name, **kwargs):
    return reverse(url_name, kwargs=kwargs)
