from django import template
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_profile(user):
    try:
        return user.profile
    except ObjectDoesNotExist:
        return None
