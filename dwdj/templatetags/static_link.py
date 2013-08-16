import os

from django import template
from django.utils.safestring import mark_safe

from django.conf import settings as s
from django.contrib.staticfiles.finders import find as find_staticfiles

register = template.Library()

def _stat(file):
    return int(os.stat(os.path.join(s.STATIC_ROOT, file)).st_mtime)

def _mtime_suffix(file):
    try:
        return _stat(file)
    except OSError as e:
        if e.errno != 2: # no such file or directory
            raise

    staticfiles = find_staticfiles(file, all=True)
    if not staticfiles:
        raise Exception("no static files found matching %r" %(file, ))
    if len(staticfiles) > 2:
        raise Exception("multiple static files found matching %r: %r"
                        %(file, staticfiles))
    return _stat(staticfiles[0])

@register.simple_tag
def static_url(file):
    return "%s%s?%s" %(s.STATIC_URL, file, _mtime_suffix(file))

@register.simple_tag
def stylesheet_link(stylesheet, media="all"):
    return mark_safe('<link rel="stylesheet" href="%s%s?%d" type="text/css" media="%s" />' %(
        s.STATIC_URL,
        stylesheet,
        _mtime_suffix(stylesheet),
        media,
    ))

@register.simple_tag
def script_link(script):
    return mark_safe('<script type="text/javascript" src="%s%s?%d"></script>' %(
        s.STATIC_URL,
        script,
        _mtime_suffix(script)
    ))
