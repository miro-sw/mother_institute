# institute/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def dict_key(d, key):
    """Get dictionary value by key"""
    try:
        return d.get(key)
    except (AttributeError, TypeError):
        return None

@register.filter
def mul(value, arg):
    """Multiply value by argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divide value by argument"""
    try:
        if float(arg) != 0:
            return float(value) / float(arg)
        return 0
    except (ValueError, TypeError):
        return 0