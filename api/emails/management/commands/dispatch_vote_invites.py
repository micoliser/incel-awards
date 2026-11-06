from django.core.management.base import BaseCommand, CommandError

from awards.models import AwardYear
from emails.services.dispatch import dispatch_vote_invites


class Command(BaseCommand):
    help = (
        'Dispatch vote-invite emails for a year based on AwardNotificationConfig. '
        'Idempotent: skips tokens with a successful BallotInviteDelivery. '
        'Cron-friendly — exits quietly when too early or disabled.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            required=True,
            help='Award year (e.g. 2026)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Bypass timing gate (voting_opens_at - offset) for ops/tests',
        )

    def handle(self, *args, **options):
        year_num = options['year']
        force = options['force']

        try:
            year = AwardYear.objects.get(year=year_num)
        except AwardYear.DoesNotExist as exc:
            raise CommandError(
                f'AwardYear {year_num} does not exist. Seed it first.'
            ) from exc

        stats = dispatch_vote_invites(year, force=force)

        if stats.exited_early:
            self.stdout.write(
                self.style.WARNING(
                    f'dispatch_vote_invites year={year_num} exited: {stats.exited_early} '
                    f'(audience={stats.audience_total}, '
                    f'skipped_email_off={stats.skipped_email_off}, '
                    f'skipped_timing={stats.skipped_timing})'
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'dispatch_vote_invites year={year_num}: '
                f'audience={stats.audience_total} sent={stats.sent} '
                f'failed={stats.failed} '
                f'skipped_already_sent={stats.skipped_already_sent} '
                f'skipped_revoked={stats.skipped_revoked}'
                + (' (forced)' if force else '')
            )
        )
