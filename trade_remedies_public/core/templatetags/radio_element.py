from core.templatetags import register
from django.utils.safestring import mark_safe
import json


@register.simple_tag(takes_context=True)
def radio_element(
    context,
    id,
    label,
    options,
    errors=None,
    name=None,
    value=None,
    hint=None,
    input_classes="",
    read_only=False,
):
    """
    Show a set of radio buttons
    The 'options' parameter should be a json string (as this can be handled within templates)
    usage
    {% radio_element id='yesno' label='Is it da or nyet?' options='[{"value":"yes". "label":"Da"}, {"value":"no". "label":"Nyet"} ]' %}
    """
    name = name or id
    options = json.loads(options)
    output = []
    if value is None:
        value = context.get(id, "")
    read_only = "" if not read_only else "readonly disabled"
    output.append('<div class="form-group')
    if name and errors and name in errors:
        output.append(" form-group-error ")
    output.append('">')
    output.append(f'<label class="form-label" for="{ id }">{ label }')
    if hint:
        output.append(f'<span class="form-hint">{ hint }</span>')
    output.append(f"</label>")
    if name and errors and name in errors:
        message = errors[name]
        output.append(f'<span class="error-message" id="{ name }_error">{ message }</span>')
    output.append('<div class="indent">')
    for num, option in enumerate(options, start=1):
        output.append(f'<div class="multiple-choice">')
        option_value = option.get("value")
        option_label = option.get("label")
        checked = 'checked="checked"' if option_value == value else ""
        output.append(
            f'<input class="{ input_classes }" type="radio" id="{ id }-{ option_value }" name="{ name }"\
            value="{ option_value }"\
            { checked }\
            { read_only }>'
        )
        output.append(
            f'<label for="{ id }-{ option_value }" class="form-label">{ option_label }</label>'
        )
        output.append(f"</div>")
    output.append("</div></div>")
    return mark_safe("".join(output))
