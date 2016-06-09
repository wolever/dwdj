import os

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

from django.conf import settings as s
from django.contrib.staticfiles.finders import find as find_staticfiles

register = template.Library()

def _stat(file):
    return int(os.stat(os.path.join(s.STATIC_ROOT, file)).st_mtime)

def format_attrs(attrs):
    """ Formats HTML key/value attributes::

        >>> format_attrs([("foo", "bar"), ("a", '"bar"')])
        ' foo="bar" a="&qt;bar&qt;"'
        """
    return (attrs and " " or "") + " ".join(
        '%s="%s"' %(key, escape(val)) for (key, val) in attrs
    )

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

@register.simple_tag(takes_context=True)
def static_url(context, file, absolute=False):
    url = "%s%s?%s" %(s.STATIC_URL, file, _mtime_suffix(file))
    if absolute:
        url = context["request"].build_absolute_uri(url)
    return url

@register.simple_tag
def stylesheet_link(stylesheet, media="all", rel="stylesheet", type="text/css",
                    **attrs):
    return mark_safe('<link rel="%s" href="%s%s?%d" type="%s" media="%s"%s />' %(
        rel,
        s.STATIC_URL,
        stylesheet,
        _mtime_suffix(stylesheet),
        type,
        media,
        format_attrs(attrs.items()),
    ))

@register.simple_tag
def script_link(script, type="text/javascript", **attrs):
    return mark_safe('<script type="%s" src="%s%s?%d"%s></script>' %(
        type,
        s.STATIC_URL,
        script,
        _mtime_suffix(script),
        format_attrs(attrs.items()),
    ))
