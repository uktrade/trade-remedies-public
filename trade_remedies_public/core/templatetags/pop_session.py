from core.templatetags import register


@register.filter
def pop_session(request, key):
    """Pops and returns a key from the request.session"""
    return request.session.pop(key, None)
