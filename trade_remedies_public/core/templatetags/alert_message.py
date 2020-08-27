from core.templatetags import register
from core.constants import ALERT_MAP
from django.utils.safestring import mark_safe


@register.simple_tag(takes_context=True)
def alert_message(context):
    """
    Display one or more error messages
    """
    output = ""
    request = context.get("request")
    if request:
        alert = request.GET.get("alert")
        if alert:
            _message = ALERT_MAP.get(alert)
            if _message:
                output = f'<div class="govuk-box-highlight column-full">{_message}</div>'
            else:
                print(f'***  ALERT_MAP  *** tag "{alert}" not found')
    return mark_safe(output)
