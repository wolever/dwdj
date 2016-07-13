import sys
import logging
from itertools import groupby

from django.core import management
from django.conf import settings as s
from django.db import DEFAULT_DB_ALIAS, connections

from dwdj.management.base import BaseCommand, make_option

log = logging.getLogger(__name__.rpartition(".")[2])


class Command(BaseCommand):
    help = """
        Checks whether migrations needs to be run.
    """

    option_list = [
        make_option("-i", "--interactive", action="store_true", default=False),
        make_option("--use", default="auto", choices=["auto", "django", "south"],
            help="One of 'auto' (default), 'south', or 'django'."),
        make_option("--database", action="store", dest="database", default=DEFAULT_DB_ALIAS,
            help="Nominates a database to synchronize. Defaults to the 'default' database.",
        ),
    ]

    def handle(self, *args, **options):
        sys.exit(self.run(args, options))

    def run(self, args, options):
        use = options["use"]
        if use == "auto":
            use = "south" if "south" in s.INSTALLED_APPS else "django"
        return getattr(self, "run_%s" %(use, ))(args, options)

    def run_django(self, args, options):
        from django.db.migrations.loader import MigrationLoader
        connection = connections[options['database']]
        loader = MigrationLoader(connection)
        graph = loader.graph
        targets = graph.leaf_nodes()
        plan = []
        seen = set()

        # Generate the plan
        for target in targets:
            for migration in graph.forwards_plan(target):
                if migration not in seen:
                    plan.append(graph.nodes[migration])
                    seen.add(migration)

        unapplied = []
        for migration in plan:
            if (migration.app_label, migration.name) not in loader.applied_migrations:
                unapplied.append(migration)

        quiet = options.get("quiet")
        if not unapplied:
            if not quiet:
                print "All available migrations have been applied."
            return 0

        if not quiet:
            print "FOUND UNAPPLIED MIGRATIONS"
            print "=========================="
            for migration in sorted(unapplied, key=lambda x: (x.app_label, x.name)):
                print "%s: %s" %(migration.app_label, migration.name)

        if options.get("interactive"):
            print
            resp = raw_input("Apply all of these migrations? [y/N] ").strip().lower()
            if resp in ["y", "yes"]:
                management.call_command("migrate")
                return 0
            print "NOT applying migrations."

    def run_south(self, args, options):
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
        from south.models import MigrationHistory
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
        from south.migration.base import all_migrations
        return [
            (app_migrations.app_label(), set(m.name() for m in app_migrations))
            for app_migrations in all_migrations()
        ]
