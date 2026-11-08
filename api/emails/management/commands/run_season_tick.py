from django.core.management.base import BaseCommand

from emails.services.season import run_org_sync_tick, run_season_mail_tick, run_season_tick


class Command(BaseCommand):
    help = (
        'Run season automation. Default: full pipeline (org sync + mail/status). '
        'Use --mail-only or --sync-only for the split beat jobs.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-invites',
            action='store_true',
            help='Bypass invite/eligibility/reminder timing gates (ops/tests only)',
        )
        parser.add_argument(
            '--mail-only',
            action='store_true',
            help='Tokens + due emails + status only (no workspace API)',
        )
        parser.add_argument(
            '--sync-only',
            action='store_true',
            help='Workspace org sync + mint tokens only (no emails)',
        )

    def handle(self, *args, **options):
        if options['mail_only'] and options['sync_only']:
            self.stderr.write('Choose only one of --mail-only / --sync-only.')
            return

        if options['sync_only']:
            stats = run_org_sync_tick()
            self.stdout.write(self.style.SUCCESS(f'org_sync_tick: {stats}'))
            return

        if options['mail_only']:
            stats = run_season_mail_tick(force_invites=options['force_invites'])
            self.stdout.write(self.style.SUCCESS(f'season_mail_tick: {stats}'))
            return

        stats = run_season_tick(force_invites=options['force_invites'])
        self.stdout.write(self.style.SUCCESS(f'season_tick: {stats}'))
