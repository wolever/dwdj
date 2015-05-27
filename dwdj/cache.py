class SwappableCache(object):
    """ A Django cache backend which allows the *true* backend to be swapped at
        runtime. Especially useful for tests, and moderately optimized so it
        shouldn't be a problem to use in production.

        To use ``SwappableCache``, add this to ``settings.py``::

            CACHES = {
                "default": {
                    "BACKEND": "dwdj.cache.SwappableCache",
                    "LOCATION": "redis_cache",
                },
                "redis_cache": {
                    "BACKEND": "redis_cache.cache.RedisCache",
                    "LOCATION": "localhost:,
                    "KEY_PREFIX": "cache",
                },
            }

        And then from each test::

            from django.core import cache as django_cache
            from django.conf import settings as s

            def setUp(self):
                self.old_caches = s.CACHES
                self.old_backend = django_cache.cache.get_backend()
                new_caches = dict(s.CACHES)
                new_caches.update({
                    "default": {
                        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                    },
                    "locmem": {
                        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                    },
                })
                s.CACHES = new_caches
                django_cache.cache.set_backend("locmem")
                django_cache.cache.clear()

            def tearDown(self):
                s.CACHES = self.old_caches
                django_cache.cache.backend.set_backend(self.old_backend)

        Note that both ``django.core.cache.cache`` must be fiddled with because
        it is created once at load time **and** ``settings.CACHES`` must be
        fiddled with because ``django.core.cache.get_cache`` doesn't do any
        caching, so subsequent calls to ``get_cache(...)`` will use
        ``settings.CACHES``.
    """

    def __init__(self, host, *args, **kwargs):
        self._backend = None
        self._backend_attrs = []
        self.default_backend = host

    def set_backend(self, new_backend):
        from django.core.cache import get_cache as django_get_cache
        if isinstance(new_backend, basestring):
            new_backend = django_get_cache(new_backend)
        self._backend = new_backend
        for attr in self._backend_attrs:
            try:
                delattr(self, attr)
            except AttributeError:
                pass

    def get_backend(self):
        self.set_backend(self.default_backend)
        return self._backend

    def __getattr__(self, attr):
        backend = (self._backend or self.get_backend())
        try:
            value = getattr(backend, attr)
        except AttributeError:
            return object.__getattr__(self, attr)
        self._backend_attrs.append(attr)
        setattr(self, attr, value)
        return value

    def __contains__(self, key):
        backend = (self._backend or self.get_backend())
        return key in backend
