import logging
from core.templatetags import register
from django.utils.safestring import mark_safe
from trade_remedies_client.client import Client
from django.conf import settings

logger = logging.getLogger(__name__)


@register.simple_tag
def link_lookup(key):
    """
    Template tag to get a link from the links dict in systemparameters.
    """
    link = ""
    try:
        link = Client().get_system_parameters(key).get("value", "")
    except Exception as exc:
        logger.warning("Missing link %s", key)
    return mark_safe(link)
