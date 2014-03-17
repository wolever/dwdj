from django.template import Library

register = Library()

def to_int(s, default=0):
    """
    Return input converted into an integer. If failed, then return ``default``.

    Examples::

        >>> to_int('1')
        1
        >>> to_int(1)
        1
        >>> to_int('')
        0
        >>> to_int(None)
        0
        >>> to_int(0, default='Empty')
        0
        >>> to_int(None, default='Empty')
        'Empty'
    """
    try:
        return int(s)
    except (TypeError, ValueError):
        return default

@register.simple_tag
def plural(n_str, singular, plural=None):
    """ A better pluralization template tag.

        The syntax is ``{% plural number "singular" "plural" %}``, where the
        ``plural`` is optional (the ``singular`` with an ``"s"`` suffix
        will be used if none is provided).

        By default numbers will be formatted using the ``{:,}`` formatter, so
        they will include a comma: ``1,234,567``.

        If the ``singular`` and ``plural`` strings can contain a ``{``, they
        will be treated as ``str.format`` templates::
        
            > There {% plural cats|length "is {} cat" "are {} cats" %}.
            There is 1 cat.
            > There {% plural dogs|length "is {} dog" "are {} dogs" %}.
            There are 4 dogs.

        Unlike Django's ``pluralize`` filter, ``plural`` does *not* take the
        length of lists; the ``|length`` filter can be used instead::

            > You have {% friends "friend" %}.
            You have ['Alex'] friends.
            > You have {% friends|length "friend" %}.
            You have 1 friend.

        Examples::

            > I have {% plural dog_count "dog" %}.
            I have 3 dogs.

            > You have {% plural ox_count "ox" "oxen" %}
            You have 1 ox.

            > There {% plural cats|length "is {} cat" "are {} cats" %}!
            There are 16 cats!

            > The plural will save you {% plural hours "hour" %}.
            The plural tag will save you 12,345 hours.
        """

    n = to_int(n_str, default=None)

    if plural is None:
        plural = singular + u"s"

    formatstr = singular if n == 1 else plural
    if "{" not in formatstr:
        default_format = u"{:,} " if n is not None else u"{} "
        formatstr = default_format + formatstr

    return formatstr.format(n_str)
