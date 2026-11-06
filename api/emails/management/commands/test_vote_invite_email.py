"""
Management command to test / preview a vote-invite email.

Usage:
  python manage.py test_vote_invite_email --year 2026 --recipient you@example.com
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from awards.models import AwardYear
from emails.config import EmailConfig
from emails.services.vote_invite_emails import (
    ballot_vote_url,
    build_vote_invite_context,
    send_vote_invite_email,
)
from voting.models import BallotToken
from voting.services.tokens import generate_ballot_tokens


class Command(BaseCommand):
    help = 'Send a test vote-invite email for a year (optionally to an override recipient).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            required=True,
            help='Award year (e.g. 2026)',
        )
        parser.add_argument(
            '--recipient',
            type=str,
            required=True,
            help='Recipient email address for the test send',
        )
        parser.add_argument(
            '--token',
            type=str,
            help='Optional specific BallotToken value; defaults to first token for the year',
        )

    def handle(self, *args, **options):
        year_num = options['year']
        recipient = options['recipient'].strip()
        token_value = (options.get('token') or '').strip() or None

        self.stdout.write(self.style.MIGRATE_HEADING('=' * 65))
        self.stdout.write(self.style.MIGRATE_HEADING('INCEL AWARDS — VOTE INVITE EMAIL TEST'))
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 65))

        self.stdout.write(f'Email Backend:  {getattr(settings, "EMAIL_BACKEND", "")}')
        self.stdout.write(
            f'SMTP Host:      {getattr(settings, "EMAIL_HOST", None)}:'
            f'{getattr(settings, "EMAIL_PORT", "")}'
        )
        self.stdout.write(f'Sender:         {EmailConfig.format_from_email()}')
        self.stdout.write(f'Email Enabled:  {EmailConfig.is_enabled()}')
        self.stdout.write(f'Debug Mode:     {EmailConfig.is_debug_mode()}')
        self.stdout.write('-' * 65)

        try:
            year = AwardYear.objects.get(year=year_num)
        except AwardYear.DoesNotExist as exc:
            raise CommandError(
                f'AwardYear {year_num} does not exist. Seed it first.'
            ) from exc

        if token_value:
            token = (
                BallotToken.objects.filter(year=year, token=token_value)
                .select_related('person', 'year')
                .first()
            )
            if token is None:
                raise CommandError(f'Token not found for year {year_num}.')
        else:
            token = (
                BallotToken.objects.filter(year=year, revoked_at__isnull=True)
                .select_related('person', 'year')
                .order_by('id')
                .first()
            )
            if token is None:
                self.stdout.write(
                    self.style.WARNING(
                        'No ballot tokens found — generating for eligible voters…'
                    )
                )
                generate_ballot_tokens(year)
                token = (
                    BallotToken.objects.filter(year=year, revoked_at__isnull=True)
                    .select_related('person', 'year')
                    .order_by('id')
                    .first()
                )
            if token is None:
                raise CommandError(
                    'No BallotToken available. Sync org people and generate tokens first.'
                )

        ctx = build_vote_invite_context(token, recipient_override=recipient)
        self.stdout.write(f'Token person:   {token.person.display_name} <{token.person.email}>')
        self.stdout.write(f'Ballot URL:     {ballot_vote_url(token)}')
        self.stdout.write(self.style.WARNING(f'Recipient override: {recipient}'))
        self.stdout.write(f'Awards on ballot: {ctx["award_count"]}')

        success = send_vote_invite_email(
            token,
            recipient_override=recipient,
            is_async=False,
        )
        if success:
            self.stdout.write(
                self.style.SUCCESS(f'Vote invite email sent to {recipient}')
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    'Vote invite email failed or was skipped '
                    '(check EMAIL_ENABLED / logs)'
                )
            )

        self.stdout.write(self.style.MIGRATE_HEADING('=' * 65))
