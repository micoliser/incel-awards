from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from awards.models import AwardNotificationConfig, AwardYear
from awards.seed import seed_year_2026
from emails.services.dispatch import dispatch_voting_closing_reminders
from emails.services.season import run_season_tick
from emails.services.voting_closing_reminder_emails import EVENT
from people.dev_fixtures import build_dev_org_users
from people.services.sync import sync_org_people
from unittest.mock import patch
from voting.models import BallotInviteDelivery, BallotToken
from voting.services.tokens import generate_ballot_tokens


@override_settings(
    EMAIL_ENABLED=True,
    EMAIL_DEBUG=False,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    FRONTEND_BASE_URL='https://awards.example.com',
)
class VotingClosingReminderTests(TestCase):
    def setUp(self):
        self.year = seed_year_2026()
        now = timezone.now()
        self.year.status = AwardYear.Status.VOTING
        self.year.voting_opens_at = now - timedelta(hours=2)
        self.year.voting_closes_at = now + timedelta(minutes=30)
        self.year.save()

        config = AwardNotificationConfig.objects.get(
            year=self.year,
            event=AwardNotificationConfig.Event.VOTING_CLOSING_REMINDER,
        )
        config.enabled = True
        config.offset_minutes_before_close = 60
        config.save()

        sync_org_people(build_dev_org_users())
        generate_ballot_tokens(self.year)
        self.assertGreater(BallotToken.objects.filter(year=self.year).count(), 0)

    def test_seed_creates_closing_reminder_config(self):
        config = AwardNotificationConfig.objects.get(
            year=self.year,
            event=AwardNotificationConfig.Event.VOTING_CLOSING_REMINDER,
        )
        self.assertTrue(config.enabled)
        self.assertEqual(config.offset_minutes_before_close, 60)

    def test_dispatch_sends_to_unsubmitted_only(self):
        token = BallotToken.objects.filter(year=self.year).first()
        token.submitted_at = timezone.now()
        token.save(update_fields=['submitted_at'])
        unsubmitted = BallotToken.objects.filter(
            year=self.year, submitted_at__isnull=True
        ).count()

        stats = dispatch_voting_closing_reminders(self.year, force=False)
        self.assertEqual(stats.sent, unsubmitted)
        self.assertEqual(len(mail.outbox), unsubmitted)
        self.assertTrue(all('closes soon' in m.subject.lower() or 'Reminder' in m.subject for m in mail.outbox))
        self.assertFalse(
            BallotInviteDelivery.objects.filter(
                token=token,
                event=EVENT,
                status=BallotInviteDelivery.Status.SENT,
            ).exists()
        )

    def test_too_early_exits(self):
        self.year.voting_closes_at = timezone.now() + timedelta(hours=5)
        self.year.save(update_fields=['voting_closes_at'])
        config = AwardNotificationConfig.objects.get(
            year=self.year,
            event=AwardNotificationConfig.Event.VOTING_CLOSING_REMINDER,
        )
        config.offset_minutes_before_close = 60
        config.save()

        stats = dispatch_voting_closing_reminders(self.year)
        self.assertEqual(stats.exited_early, 'too_early')
        self.assertEqual(stats.sent, 0)

    def test_force_bypasses_timing(self):
        self.year.voting_closes_at = timezone.now() + timedelta(hours=5)
        self.year.save(update_fields=['voting_closes_at'])
        stats = dispatch_voting_closing_reminders(self.year, force=True)
        self.assertGreater(stats.sent, 0)

    @patch('emails.services.season.sync_org_people')
    def test_season_tick_dispatches_closing_reminder(self, mock_sync):
        from people.services.sync import SyncStats

        mock_sync.return_value = SyncStats()
        mail.outbox.clear()
        stats = run_season_tick()
        self.assertTrue(
            any(row.get('sent', 0) > 0 for row in stats.closing_reminders)
        )
        self.assertTrue(any('Reminder' in m.subject for m in mail.outbox))
