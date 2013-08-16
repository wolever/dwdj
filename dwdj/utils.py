from django.template.defaultfilters import slugify


class AutoStrMixin(object):
    """ Allows string fields ``__autostr__``, ``__autounicode__`` and
        ``__autorepr__`` to be used to implement ``__str__``, ``__unicode__``
        and ``__repr__``.  Additionally, if no ``__str__`` or ``__autostr__``
        has been implemented, ``__str__`` will return
        ``__unicode__().encode("utf-8")``.

        WARNING: This has some problems and probably shouldn't be used.
        Instead, see ``autorepr``, ``autounicode``, and autostr, below.

        ::
            >>> class Foo(AutoStrMixin):
            ...     def __init__(self, name):
            ...         self.name = name
            ...
            ...     __autounicode__ = u"name: {self.name}"
            ...     __autorepr__ = "name={self.name!r}"
            ...
            >>> foo = Foo(u"wolever")
            >>> unicode(foo)
            u'name: wolever'
            >>> str(foo)
            'name: wolever'
            >>> repr(foo)
            "<__main__.Foo name=u'wolever' at 0x...>"
        """

    def _autostr_helper(self, method, default):
        formatstr = getattr(self, "__auto%s__" %(method, ), None)
        if formatstr is None:
            return default()
        return formatstr.format(self=self)

    def __unicode__(self):
        default = lambda: unicode(repr(self))
        return self._autostr_helper("unicode", default)

    def __str__(self):
        default = lambda: unicode(self).encode("utf-8")
        return self._autostr_helper("str", default)

    def __repr__(self):
        result = self._autostr_helper("repr", lambda: None)
        if result is None:
            return super(AutoStrMixin, self).__repr__()
        return "<%s.%s %s at 0x%x>" %(self.__class__.__module__,
                                      self.__class__.__name__,
                                      result, id(self))


def _autofmthelper(name, fmt, postprocess=None):
    def fmtfunc(self):
        result = fmt.format(self=self)
        if postprocess is not None:
            result = postprocess(self, result)
        return result
    fmtfunc.__name__ = name
    return fmtfunc

def autounicode(fmt):
    """ Returns a simple ``__unicode__`` function::

        >>> class Person(object):
        ...     name = "Alex"
        ...     __unicode__ = autounicode("{self.name}")
        ...
        >>> unicode(Person())
        u'Alex'
        >>>
        """
    return _autofmthelper("__unicode__", unicode(fmt))

def autostr(fmt):
    """ Returns a simple ``__str__`` function::

        >>> class Person(object):
        ...     name = "Alex"
        ...     __str__ = autostr("{self.name}")
        ...
        >>> str(Person())
        'Alex'
        >>>
        """
    fmt = str(fmt)
    return _autofmthelper("__str__", str(fmt))

def autorepr(fmt):
    """ Returns a simple ``__repr__`` function::

        >>> class Person(object):
        ...     name = "Alex"
        ...     __repr__ = autorepr("name={self.name!r}")
        ...
        >>> repr(Person())
        "<__main__.Person name='Alex' at 0x...>"
        >>>
        """
    return _autofmthelper("__repr__", str(fmt), lambda self, result: (
        "<%s.%s %s at 0x%x>" %(
            self.__class__.__module__,
            self.__class__.__name__,
            result,
            id(self),
        )
    ))


def slug_property(field):
    @property
    def slug_property_helper(self):
        return slugify(getattr(self, field))
    return slug_property_helper

if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
