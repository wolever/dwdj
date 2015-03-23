import sys
import logging
from functools import partial
from optparse import make_option, OptionParser

from django.dispatch import Signal
from django.utils.functional import cached_property
from django.core.management.base import BaseCommand as DjBaseCommand
from django.core.management.base import (
    CommandError, OutputWrapper, handle_default_options,
)

from dwdj.strutil import dedent

CommandError

signal_pre_run = Signal(providing_args=["argv"])
signal_post_run = Signal(providing_args=["status"])

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
        * The ``self.log`` attribute will be set to a logger configured to use
          the name from ``self.get_log_name()`` (which defaults to the fully
          qualified name of the module containing the command).
        * If ``handle`` returns an integer it will be treated as a numeric exit
          status. If a ``str`` or ``unicode`` is returned it will be treated
          "normally" and 0 will be returned.
        * If ``handle`` raises an exception that exception will be logged
          (unless ``self.log_exc`` is ``False``) and the command will exit
          with a status of 1.

        Example::

            from dwdj.management.base import BaseCommand, make_option

            class MyCommand(BaseCommand):
                option_list = [
                    make_option("-f", "--foo", action="store_true"),
                ]

                def handle(self, *args, **options):
                    if options.get("foo"):
                        return 1
                    return 0
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
            Log complete exception traceback, not just exception and message.
        """)),
        make_option('--no-traceback', action='store_false', dest="traceback", help=dedent("""
            Log only exception messages, not complete tracebacks.
        """))
    ]

    option_list = []

    logging_enabled = True
    logging_handler_name = "stderr"
    logging_format = '%(levelname)s [%(name)s]: %(message)s'
    logging_format_verbose =  '%(asctime)s %(levelname)s [%(processName)s:%(threadName)s:%(name)s]: %(message)s'
    log_exc = True

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
        if logger.level > level:
            logger.setLevel(level)
        handler.setLevel(level)

    def get_log_name(self):
        return type(self).__module__

    @cached_property
    def log(self):
        return logging.getLogger(self.get_log_name())

    def logging_get_handler(self):
        logger = logging.getLogger("")
        for handler in logger.handlers:
            if handler.name == self.logging_handler_name:
                return logger, handler
        handler = logging.StreamHandler(sys.stderr)
        handler.name = self.logging_handler_name
        logger.addHandler(handler)
        return logger, handler

    def run_from_argv(self, argv):
        """
        Set up any environment changes requested (e.g., Python path
        and Django settings), then run this command. If the
        command raises a ``CommandError``, intercept it and print it sensibly
        to stderr.
        """
        signal_pre_run.send(self, argv=argv)
        parser = self.create_parser(argv[0], argv[1])
        options, args = parser.parse_args(argv[2:])
        handle_default_options(options)
        try:
            result = self.execute(*args, **options.__dict__)
        except SystemExit as e:
            signal_post_run.send(self, status=e.code)
            raise
        except BaseException:
            result = self.handle_execute_exc(options)
            if result is None:
                result = 1
        status = result or 0
        signal_post_run.send(self, status=status)
        sys.exit(status)

    def handle_execute_exc(self, options):
        if not self.log_exc:
            return 1
        if options.traceback:
            self.log.exception("Exception running command:")
        else:
            exc_info = sys.exc_info()
            self.log.error("%s: %s", exc_info[0].__name__, exc_info[1])
        return 1

    def execute(self, *args, **options):
        """
        Try to execute this command, performing model validation if
        needed (as controlled by the attribute
        ``self.requires_model_validation``, except if force-skipped).
        """

        # Switch to English, because django-admin.py creates database content
        # like permissions, and those shouldn't contain any translations.
        # But only do this if we can assume we have a working settings file,
        # because django.utils.translation requires settings.
        saved_lang = None
        self.stdout = OutputWrapper(options.get('stdout', sys.stdout))
        self.stderr = OutputWrapper(options.get('stderr', sys.stderr), self.style.ERROR)

        if self.can_import_settings:
            from django.utils import translation
            saved_lang = translation.get_language()
            translation.activate('en-us')

        try:
            if self.requires_model_validation and not options.get('skip_validation'):
                self.validate()
            result = self.handle(*args, **options)
            if isinstance(result, basestring):
                if self.output_transaction:
                    # This needs to be imported here, because it relies on
                    # settings.
                    from django.db import connections, DEFAULT_DB_ALIAS
                    connection = connections[options.get('database', DEFAULT_DB_ALIAS)]
                    if connection.ops.start_transaction_sql():
                        self.stdout.write(self.style.SQL_KEYWORD(connection.ops.start_transaction_sql()))
                self.stdout.write(result)
                if self.output_transaction:
                    self.stdout.write('\n' + self.style.SQL_KEYWORD("COMMIT;"))
                result = 0
            return result
        finally:
            if saved_lang is not None:
                translation.activate(saved_lang)
