from core.templatetags import register
from django.utils.safestring import mark_safe


@register.simple_tag(takes_context=True)
def password_element(context, id, label, errors=None):
    """
    Display one or more error messages
    TODO: refactor away from string concat
    """
    output = ""
    if id and errors and id in errors:
        output += output + '<div class="form-group type-text form-group-error">'
    else:
        output += '<div class="form-group type-text">'
    output += f'<label class="form-label" for="{ id }_id">{ label }</label>'
    if id and errors and id in errors:
        message = errors[id]
        if isinstance(message, list):
            for msg in message:
                output += f'<span class="error-message" id="{ id }_error">{ msg }</span>'
        else:
            output += f'<span class="error-message" id="{ id }_error">{ message }</span>'
    output += (
        f'<input class="form-control" id="{ id }_id" type="password" autocomplete="off" '
        f'name="{ id }" value="{ context.get(id,"") }">'
    )
    output += "</div>"
    return mark_safe(output)
