import os
import sys
import logging
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.importlib import import_module
from django.core.management import call_command
from django.core.management.commands.dumpdata import Command as DumpData

log = logging.getLogger("dump_app_data")

HELP = """\
Dumps data for each app to the directory returned by
``settings.DUMP_APP_DATA_FUNC``. If none is specified, a default function will
be used which dumps data to ``$APP/fixtures/${FIXTURE-dev}.${FORMAT-json}`` for
all apps which share a prefix with ``ROOT_URLCONF``.
"""


class Command(BaseCommand):
    help = HELP
    can_import_settings = True
    option_list = DumpData.option_list + (
        make_option('--fixture-name', dest='fixture_name', default='dev',
                    help='Fixture name to write to'),
    )
    
    @classmethod
    def app_name_to_path(cls, app_name):
        app_module = import_module(app_name)
        return os.path.join(os.path.dirname(app_module.__file__))

    @classmethod
    def DEFAULT_DUMP_APP_DATA_FUNC(cls, options, app_name):
        prefix = settings.ROOT_URLCONF.split('.')[0]
        if not app_name.startswith(prefix):
            log.debug("app %r is not prefixed with %r; ignoring",
                      app_name, prefix)
            return None
        return os.path.join(cls.app_name_to_path(app_name), "fixtures",
                            options["fixture_name"] + "." + options["format"])

    @classmethod
    def dump_app_data(cls, options, app_name, output_file):
        dumpdata_options = dict(options)
        dumpdata_options.pop("fixture_name")

        output_path = os.path.dirname(output_file)
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        orig_stdout = sys.stdout
        try:
            sys.stdout = open(output_file + ".tmp", "w")
            call_command("dumpdata", app_name.split(".")[-1],
                         **dumpdata_options)
        finally:
            sys.stdout.close()
            sys.stdout = orig_stdout

        os.rename(output_file + ".tmp", output_file)
    
        try:
            output = open(output_file, "r")
            if len(output.read(16)) < 10:
                os.remove(output_file)
                print "no data for %r; removing %r" %(app_name, output_file)
            else:
                print "dumped data for %r to %r" %(app_name, output_file)
        finally:
            output.close()

    def handle(self, *args, **options):
        path_func = getattr(settings, "DUMP_APP_DATA_FUNC",
                            self.DEFAULT_DUMP_APP_DATA_FUNC)
        for app_name in settings.INSTALLED_APPS:
            path = path_func(options, app_name)
            if not path:
                continue
            self.dump_app_data(options, app_name, path)
