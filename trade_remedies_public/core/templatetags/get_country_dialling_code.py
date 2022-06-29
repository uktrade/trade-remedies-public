"""
A template filter to return the dialling code given an ISO-2 country code.

Usage:
    {% form.country_code|get_country_dialling_code %}
"""

from core.templatetags import register
from phonenumbers.phonenumberutil import country_code_for_region


@register.filter
def get_country_dialling_code(country_code):
    return country_code_for_region(country_code)
