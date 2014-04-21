import sys
import logging
from functools import partial
from optparse import make_option, OptionParser

from dwdj.strutil import dedent

from django.core.management.base import BaseCommand as DjBaseCommand
from django.core.management.base import CommandError

CommandError

class BaseCommand(DjBaseCommand):
    """ A less terrible base class for Djagno management commands.

        Changes:

        * Tracebacks are turned on by default
        * Verbosity is controlled by a counter instead of a number (ex,
          ``-vvv`` instead of ``-v3``) and are used to set up logging levels
          too (disable by setting ``logging_enabled = False``).
        * Will override a named logger (see ``logging_handler_name``) with the
          level and formatter settings from the command line (or add a new
          stderr logger if no matching logger is found).
        * Subclassess can set ``option_list`` directly - the base options are
          stored in ``base_option_list`` and merged with ``get_option_list``.

        Example::

            from dwdj.management.base import BaseCommand, make_option

            class MyCommand(BaseCommand):
                option_list = [
                    make_option("-f", "--foo"),
                ]

                def handle(self, *args, **options):
                    pass
    """

    base_option_list = [
        make_option('-q', '--quiet', action="store_const", const=-1, dest="verbosity"),
        make_option('-v', '--verbose', action="count", default=0, dest="verbosity"),
        make_option('--verbose-log', action="store_true", help=dedent("""
            Use a more verbose logging format.
        """)),
        make_option('--settings', help=dedent("""
            The Python path to a settings module, e.g.
            "myproject.settings.main". If this isn\'t provided, the
            DJANGO_SETTINGS_MODULE environment variable will be used.')
        """)),
        make_option('--pythonpath', help=dedent("""
            A directory to add to the Python path, e.g.
            "/home/djangoprojects/myproject".
        """)),
        make_option('--traceback', action='store_true', default=True, help=dedent("""
            Show full exception traceback
        """)),
        make_option('--no-traceback', action='store_false', dest="traceback",
                    help=dedent("""
            Hide exception traceback (implied by --quiet)
        """))
    ]

    option_list = []

    logging_enabled = True
    logging_handler_name = "stderr"
    logging_format = '%(levelname)s [%(name)s]: %(message)s'
    logging_format_verbose =  '%(asctime)s %(levelname)s [%(processName)s:%(threadName)s:%(name)s]: %(message)s'

    def get_option_list(self):
        return self.base_option_list + self.option_list

    def create_parser(self, prog_name, subcommand):
        """
        Create and return the ``OptionParser`` which will be used to
        parse the arguments to this command.

        """
        parser = OptionParser(prog=prog_name,
                              usage=self.usage(subcommand),
                              version=self.get_version(),
                              option_list=self.get_option_list())
        original_parse = parser.parse_args
        parser.parse_args = partial(self._override_parse_args, parser,
                                    original_parse)
        return parser

    def _override_parse_args(self, parser, original_parse, *argv, **kwargs):
        options, args = original_parse(*argv, **kwargs)
        self.logging_setup(options)
        if options.verbosity < 0:
            options.traceback = False
        return (options, args)

    def logging_setup(self, options):
        verbosity = options.verbosity
        level = (
            logging.CRITICAL if verbosity < 0 else
            logging.ERROR if verbosity == 0 else
            logging.WARNING if verbosity == 1 else
            logging.INFO if verbosity == 2 else
            logging.DEBUG
        )
        format = (
            self.logging_format if not options.verbose_log else
            self.logging_format_verbose
        )
        logger, handler = self.logging_get_handler()
        formatter = logging.Formatter(format)
        handler.setFormatter(formatter)
        logger.setLevel(level)
        handler.setLevel(level)

    def logging_get_handler(self):
        logger = logging.getLogger("")
        for handler in logger.handlers:
            if handler.name == self.logging_handler_name:
                return logger, handler
        handler = logging.StreamHandler(sys.stderr)
        handler.name = self.logging_handler_name
        logger.addHandler(handler)
        return logger, handler
