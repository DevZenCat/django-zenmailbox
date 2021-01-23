from django import template
from django.utils.html import strip_tags

register = template.Library()


@register.filter
def html_to_plaintext(value):
    return strip_tags(value.replace("<br>", "\n"))
