from django.conf.urls import include

def include_factory(package, includefunc=include):
    """ Returns a Django-urls-``include`` function which will resolve names relative
        to ``package``::

            >>> __package__
            'mysite.urls'
            >>> include = include_factory(__package__)
            >>> include('.foo')
            ('mysite.urls.foo', ...)
            >>> include('..foo')
            ('mysite.foo', ...)

        For example::

            include = include_factory(__package__)
            urlpatterns = patterns('',
                url('^wiki/', include('.wiki.urls')),
                url('^accounts/', include('.accounts.urls')),
            )
        """
    pkg_split = package.split(".")
    def include_factory_helper(module, **kwargs):
        if isinstance(module, basestring) and module.startswith("."):
            module_rel = module.lstrip(".")
            num_above = len(module) - len(module_rel) - 1
            module_abs = pkg_split[:len(pkg_split)-num_above] + [module_rel]
            module = ".".join(module_abs)
        return includefunc(module, **kwargs)
    return include_factory_helper
