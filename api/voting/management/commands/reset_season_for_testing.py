from django.core.management.base import BaseCommand, CommandError

from awards.models import AwardYear
from voting.services.reset_season import reset_season_for_testing


class Command(BaseCommand):
    help = (
        'Wipe voting/email state for one award year so a live test can be re-run. '
        'Deletes votes, audit logs, and invite deliveries; unlocks ballots; '
        'unpublishes results; optionally schedules a fresh voting window. '
        'Does NOT delete awards, nominees, or org people. '
        'Requires --confirm.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, required=True, help='Award year (e.g. 2026)')
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Required. Acknowledge this deletes votes and invite delivery history.',
        )
        parser.add_argument(
            '--opens-in-minutes',
            type=int,
            default=None,
            help='Set voting_opens_at to now + N minutes (and status=scheduled).',
        )
        parser.add_argument(
            '--window-minutes',
            type=int,
            default=30,
            help='Voting window length after open (default 30). Used with --opens-in-minutes.',
        )
        parser.add_argument(
            '--eligibility-offset',
            type=int,
            default=None,
            help='Set eligibility_notice offset_minutes_before_open.',
        )
        parser.add_argument(
            '--invite-offset',
            type=int,
            default=None,
            help='Set vote_invite offset_minutes_before_open.',
        )
        parser.add_argument(
            '--closing-reminder-offset',
            type=int,
            default=None,
            help='Set voting_closing_reminder offset_minutes_before_close.',
        )
        parser.add_argument(
            '--delete-tokens',
            action='store_true',
            help='Delete ballot tokens (season tick will recreate). Default only unlocks them.',
        )
        parser.add_argument(
            '--rotate-preview-token',
            action='store_true',
            help='Rotate the committee results preview token.',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            raise CommandError(
                'Refusing to run without --confirm. '
                'This deletes votes and BallotInviteDelivery rows for the year.'
            )

        year_num = options['year']
        try:
            year = AwardYear.objects.get(year=year_num)
        except AwardYear.DoesNotExist as exc:
            raise CommandError(f'AwardYear {year_num} does not exist.') from exc

        try:
            stats = reset_season_for_testing(
                year,
                opens_in_minutes=options['opens_in_minutes'],
                window_minutes=options['window_minutes'],
                eligibility_offset_minutes=options['eligibility_offset'],
                invite_offset_minutes=options['invite_offset'],
                closing_reminder_offset_minutes=options['closing_reminder_offset'],
                delete_tokens=options['delete_tokens'],
                rotate_preview_token=options['rotate_preview_token'],
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                'reset_season_for_testing '
                f"year={stats.year} "
                f"votes_deleted={stats.votes_deleted} "
                f"audit_logs_deleted={stats.audit_logs_deleted} "
                f"deliveries_deleted={stats.deliveries_deleted} "
                f"tokens_unlocked={stats.tokens_unlocked} "
                f"tokens_deleted={stats.tokens_deleted} "
                f"status={stats.status} "
                f"opens={stats.voting_opens_at} "
                f"closes={stats.voting_closes_at}"
            )
        )
        self.stdout.write(
            'Awards/nominees/org people kept. '
            'Celery beat will sync, mint tokens if needed, and send emails on the new offsets.'
        )
