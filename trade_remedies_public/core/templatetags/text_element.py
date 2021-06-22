from django.utils.html import escape

from core.templatetags import register
from django.utils.safestring import mark_safe


@register.simple_tag(takes_context=True)
def text_element(
    context,
    id,
    label,
    errors=None,
    data_mode=None,
    name=None,
    textarea=None,
    type=None,
    rows=3,
    value=None,
    hint=None,
    password=False,
    input_classes="",
    read_only=False,
    autocomplete=None,
    attach=None,
):
    """
    Display one or more error messages
    """
    name = name or id
    output = []
    _type = "password" if password else type if type else "text"
    if value is None:
        value = context.get(id) or ""
    read_only = "" if not read_only else "readonly disabled"

    if autocomplete:
        autocomplete = f'autocomplete="{autocomplete}" '
    else:
        autocomplete = ""

    if value is None:
        value = context.get(id, "")
    else:
        value = escape(value)

    output.append('<div class="form-group type-text ')
    if name and errors and name in errors:
        output.append("form-group-error ")
    if data_mode:
        output.append("type-typeahead ")
    output.append('"')
    if attach:
        output.append(f' data-attach="{attach}"')
    output.append(">")
    output.append(f'<label class="form-label" for="{ id }">{ label }')
    if hint:
        output.append(f'<span class="form-hint">{ hint }</span>')
    output.append("</label>")
    if name and errors and name in errors:
        message = errors[name]
        output.append(f'<span class="error-message" id="{ name }_error">{ message }</span>')
    if data_mode:  # for typeahead elements
        output.append(
            f'<input class="form-control { input_classes }" id="{ id }" type="text" data-mode="{ data_mode }" name="{ name }" value="{ value }" { read_only } { autocomplete }>'  # noqa: E501
        )
    elif textarea:
        output.append(
            f'<textarea class="form-control { input_classes }" rows="{ rows }"  id="{ id }" name="{ name }" { read_only }>{ value }</textarea>'  # noqa: E501
        )
    else:
        output.append(
            f'<input class="form-control { input_classes }" id="{ id }" type="{ _type }" name="{ name }" value="{ value }" { autocomplete } { read_only }>'  # noqa: E501
        )
    output.append("</div>")
    return mark_safe("".join(output))
