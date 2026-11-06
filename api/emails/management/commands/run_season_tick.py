from django.core.management.base import BaseCommand

from emails.services.season import run_season_tick


class Command(BaseCommand):
    help = (
        'Run one season automation tick: sync org people, generate ballot tokens, '
        'dispatch due vote invites, advance year status.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-invites',
            action='store_true',
            help='Bypass invite timing gate (ops/tests only)',
        )

    def handle(self, *args, **options):
        stats = run_season_tick(force_invites=options['force_invites'])
        self.stdout.write(self.style.SUCCESS(f'season_tick: {stats}'))
