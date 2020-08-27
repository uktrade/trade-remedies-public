from core.templatetags import register


@register.filter
def get_item(obj, key):
    """
    Template tag to return a given key dynamically from a dictionary or an object
    """
    val = None
    if obj and type(obj) == dict:
        val = obj.get(key) or obj.get(str(key))
    elif obj and hasattr(obj, key):
        val = getattr(obj, key)
    elif obj and hasattr(obj, str(key)):
        val = getattr(obj, str(key))
    elif type(obj) == list:
        val = obj[int(key)]
    val = val or ""
    return val
