import sys
import logging
from itertools import groupby

from django.core import management
from south.models import MigrationHistory
from south.migration.base import all_migrations
from dwdj.management.base import BaseCommand, make_option

log = logging.getLogger(__name__.rpartition(".")[2])


class Command(BaseCommand):
    help = """
        Checks whether migrations needs to be run.
    """

    option_list = [
        make_option("-i", "--interactive", action="store_true", default=False),
    ]

    def handle(self, *args, **options):
        sys.exit(self.run(args, options))

    def run(self, args, options):
        applied_dict = dict(self.get_applied_migrations())
        available = self.get_available_migrations()
        unapplied = []
        for app_name, available_migrations in available:
            unapplied_migrations = available_migrations - applied_dict.get(app_name, set())
            if unapplied_migrations:
                unapplied.append((app_name, unapplied_migrations))

        quiet = options.get("quiet")

        if not unapplied:
            if not quiet:
                print "All available migrations have been applied."
            return 0

        if not quiet:
            print "FOUND UNAPPLIED MIGRATIONS"
            print "=========================="
            for app_name, unapplied_migrations in sorted(unapplied):
                print "%s: %s" %(app_name, ", ".join(sorted(unapplied_migrations)))

        if options.get("interactive"):
            print
            resp = raw_input("Apply all of these migrations? [y/N] ").strip().lower()
            if resp in ["y", "yes"]:
                management.call_command("migrate")
                return 0
            print "NOT applying migrations."
        return 1

    def get_applied_migrations(self):
        return [
            (app_name, set(mh.migration for mh in mhistories))
            for (app_name, mhistories) in 
            groupby(
                MigrationHistory.objects
                    .filter(applied__isnull=False)
                    .order_by("app_name"),
                lambda m: m.app_name,
            )
        ]

    def get_available_migrations(self):
        return [
            (app_migrations.app_label(), set(m.name() for m in app_migrations))
            for app_migrations in all_migrations()
        ]
