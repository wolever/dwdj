import textwrap

def truncate(s, max_len=80):
    if len(s) > max_len:
        return s[:max_len - 3] + "..."
    return s

def dedent(s):
    """ Similar to ``textwrap.dedent``, but possible to use like this::

        >>> print dedent('''
        ...     Hello,
        ...     world!
        ... ''')
        Hello,
        world!
        >>>
    """
    return textwrap.dedent(s.lstrip("\n").rstrip())

def to_str(obj, encoding='utf-8', **encode_args):
    r"""
    Returns a ``str`` of ``obj``, encoding using ``encoding`` if necessary. For
    example::

        >>> some_str = "\xff"
        >>> some_unicode = u"\u1234"
        >>> some_exception = Exception(u'Error: ' + some_unicode)
        >>> to_str(some_str)
        '\xff'
        >>> to_str(some_unicode)
        '\xe1\x88\xb4'
        >>> to_str(some_exception)
        'Error: \xe1\x88\xb4'
        >>> to_str([u'\u1234', 42])
        "[u'\\u1234', 42]"

    See source code for detailed semantics.
    """
    # We coerce to unicode if '__unicode__' is available because there is no
    # way to specify encoding when calling ``str(obj)``, so, eg,
    # ``str(Exception(u'\u1234'))`` will explode.
    if isinstance(obj, unicode) or hasattr(obj, "__unicode__"):
        # Note: unicode(u'foo') is O(1) (by experimentation)
        return unicode(obj).encode(encoding, **encode_args)

    # Note: it's just as fast to do `if isinstance(obj, str): return obj` as it
    # is to simply return `str(obj)`.
    return str(obj)

def to_unicode(obj, encoding='utf-8', fallback='latin1', **decode_args):
    r"""
    Returns a ``unicode`` of ``obj``, decoding using ``encoding`` if necessary.
    If decoding fails, the ``fallback`` encoding (default ``latin1``) is used.
    
    For example::

        >>> to_unicode('\xe1\x88\xb4')
        u'\u1234'
        >>> to_unicode('\xff')
        u'\xff'
        >>> to_unicode(u'\u1234')
        u'\u1234'
        >>> to_unicode(Exception(u'\u1234'))
        u'\u1234'
        >>> to_unicode([u'\u1234', 42])
        u"[u'\\u1234', 42]"

    See source code for detailed semantics.
    """

    if isinstance(obj, unicode) or hasattr(obj, "__unicode__"):
        return unicode(obj)

    obj_str = str(obj)
    try:
        return unicode(obj_str, encoding, **decode_args)
    except UnicodeDecodeError:
        return unicode(obj_str, fallback, **decode_args)

def to_base(number, alphabet):
    if not isinstance(number, (int, long)):
        raise TypeError('number must be an integer')
    if number < 0:
        raise ValueError('number must be nonnegative')

    # Special case for zero
    if number == 0:
        return '0'

    in_base = []
    while number != 0:
        number, i = divmod(number, len(alphabet))
        in_base.append(alphabet[i])
    return "".join(reversed(in_base))

def to36(number):
    return to_base(number, '0123456789abcdefghijklmnopqrstuvwxyz')

def from36(str):
    return int(str, 36)


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
