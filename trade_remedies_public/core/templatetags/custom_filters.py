from core.templatetags import register
from django.utils.safestring import mark_safe
import datetime


@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)


@register.filter
def _not(arg1):
    """Boolean or"""
    return not arg1


@register.filter
def _or(arg1, arg2):
    """Boolean or"""
    return arg1 or arg2


@register.filter
def _and(arg1, arg2):
    """Boolean and"""
    return arg1 and arg2


@register.filter
def _equals(arg1, arg2):
    """Boolean and"""
    return arg1 and arg2


@register.filter
def _plus(arg1, arg2):
    """int plus"""
    return str(int(arg1) + int(arg2))


@register.filter
def _aslist(arg1):
    """return a list, split from the string supplied"""
    return str(arg1).split(",")


@register.filter
def _get(arg1, arg2):
    """get a value from an object"""
    return (arg1 or {}).get(arg2)


def suffix(d):
    return "th" if 11 <= d <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th")


@register.filter
def format_date(date, format_str="%d %b %Y %H:%M:%S"):
    if isinstance(date, str) and len(date) > 18:
        date = datetime.datetime.strptime(date[:19], "%Y-%m-%dT%H:%M:%S")
        return mark_safe(date.strftime(format_str).replace("{th}", suffix(date.day)))
    return "n/a"
