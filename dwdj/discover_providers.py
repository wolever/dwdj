# NOTE: This function has been copied almost verbatim from
#       django/contrib/admin/__init__.py
# A flag to tell us if autodiscover is running.  autodiscover will set this to
# True while running, and False when it finishes.

LOADING = False
def discover_providers(module):
    """
    Auto-discover INSTALLED_APPS modules which provide 'module' and fail
    silently when not present. This forces an import on them to register any
    bits they may want.

    Note: a list of discovered modules is intentionally not returned -- things
    should not be "magically" detected, rather they should have to explicitly
    publish themselves (eg, see admin.py).
    """
    # Bail out if discover didn't finish loading from a previous call so that
    # we avoid running discover again when the URLConf is loaded by the
    # exception handler to resolve the handler500 view.  This prevents a module
    # with errors from re-registering models and raising a spurious
    # AlreadyRegistered exception (see #8245).
    global LOADING
    if LOADING:
        return
    LOADING = True

    import imp
    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        # For each app, we need to look for "module" inside that app's
        # package. We can't use os.path here -- recall that modules may be
        # imported different ways (think zip files) -- so we need to get
        # the app's __path__ and look for "module" on that path.

        # Step 1: find out the app's __path__.  Import errors here will (and
        # should) bubble up, but a missing __path__ (which is legal, but weird)
        # fails silently -- apps that do weird things with __path__ might
        # not work so well...
        try:
            app_path = __import__(app, {}, {}, [app.split('.')[-1]]).__path__
        except AttributeError:
            continue

        # Step 2: use imp.find_module to find the app's "module". For some
        # reason imp.find_module raises ImportError if the app can't be found
        # but doesn't actually try to import the module. So skip this app if
        # its "module" doesn't exist
        try:
            imp.find_module(module, app_path)
        except ImportError:
            continue

        # Step 3: import the app's admin file. If this has errors we want them
        # to bubble up.
        __import__("%s.%s" %(app, module))

    # autodiscover was successful, reset loading flag.
    LOADING = False
