import sys
import os

from django.core.management import setup_environ

did_setup = False

def setup_test_environment():
    """ Setup a Django environment which can be used for testing.
        This will be called from ./__init__.py, and the environment in
        'helper_project/' will be used. """
    global did_setup
    if did_setup:
        return
    did_setup = True

    sys.path.append(os.path.join(os.path.dirname(__file__), "helper_project/"))
    import helper_project.settings
    setup_environ(helper_project.settings)
