from django import template

register = template.Library()

@register.filter
def human_size(num):
    num = float(num)
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0
