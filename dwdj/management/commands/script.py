import sys
import logging

from dwdj.management.base import BaseCommand, CommandError

log = logging.getLogger("script")

HELP = """\
Sets up the Django environment then runs a script as if it were invoked
directly. Useful for situations where a script needs access to models,
settings, etc, but creating a management command is undesirable.

For example::

    $ ./manage.py script cleanup.py
    Cleanup complete
    $ cat cleanup.py
    from django.conf import settings as s
    from myapp.models import MyModel
    MyModel.cleanup(options=s.CLEANUP_OPTIONS)
    print "Cleanup complete"
"""

class Command(BaseCommand):
    help = HELP

    def handle(self, *args, **options):
        if not args:
            raise CommandError("Usage: script SCRIPT_NAME [SCRIPT_ARGS ...]")
        script = args[0]
        old_argv = list(sys.argv)
        try:
            sys.argv[:] = [
                "%s %s" %(sys.argv[0], script),
            ] + list(args[1:])
            script_globals = {
                "__package__": None,
                "__doc__": None,
                "__name__": "__main__",
                "__builtins__": globals()["__builtins__"],
                "__file__": script,
            }
            execfile(script, script_globals, script_globals)
        finally:
            sys.argv[:] = old_argv
