from django import template
from django.templatetags.static import static
from django.conf import settings
import os


register = template.Library()


@register.simple_tag
def get_file_icon(extension):
    """Returns the icon for a given file extension. If none found, revert to the default icon."""
    expected_icon_path = f"v2/assets/images/file_icons/{extension}.png"
    if os.path.exists(os.path.join(settings.STATIC_ROOT, expected_icon_path)):
        return static(expected_icon_path)
    else:
        return static("v2/assets/images/file_icons/default.png")
