from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from awards.models import AwardYear
from awards.seed import seed_year_2026
from emails.services.dispatch import (
    dispatch_voting_closed,
    dispatch_voting_opened,
)
from emails.services.season import run_season_tick
from emails.services.voting_window_emails import (
    VOTING_CLOSED_EVENT,
    VOTING_OPENED_EVENT,
)
from people.dev_fixtures import build_dev_org_users
from voting.models import BallotInviteDelivery, BallotToken
from voting.services.tokens import generate_ballot_tokens


@override_settings(
    EMAIL_ENABLED=True,
    EMAIL_DEBUG=False,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    FRONTEND_BASE_URL='https://awards.example.com',
)
class VotingWindowEmailTests(TestCase):
    def setUp(self):
        self.year = seed_year_2026()
        now = timezone.now()
        self.year.status = AwardYear.Status.SCHEDULED
        self.year.voting_opens_at = now - timedelta(minutes=1)
        self.year.voting_closes_at = now + timedelta(hours=2)
        self.year.save()

        from people.services.sync import sync_org_people

        sync_org_people(build_dev_org_users())
        generate_ballot_tokens(self.year)
        self.assertGreater(BallotToken.objects.filter(year=self.year).count(), 0)

    def test_dispatch_voting_opened(self):
        stats = dispatch_voting_opened(self.year)
        self.assertGreater(stats.sent, 0)
        self.assertEqual(len(mail.outbox), stats.sent)
        self.assertTrue(all('Voting is open' in m.subject for m in mail.outbox))
        self.assertEqual(
            BallotInviteDelivery.objects.filter(
                token__year=self.year,
                event=VOTING_OPENED_EVENT,
                status=BallotInviteDelivery.Status.SENT,
            ).count(),
            stats.sent,
        )
        # Idempotent
        again = dispatch_voting_opened(self.year)
        self.assertEqual(again.sent, 0)
        self.assertEqual(again.skipped_already_sent, stats.sent)

    def test_dispatch_voting_closed(self):
        stats = dispatch_voting_closed(self.year)
        self.assertGreater(stats.sent, 0)
        self.assertTrue(all('Voting has closed' in m.subject for m in mail.outbox))
        self.assertEqual(
            BallotInviteDelivery.objects.filter(
                token__year=self.year,
                event=VOTING_CLOSED_EVENT,
                status=BallotInviteDelivery.Status.SENT,
            ).count(),
            stats.sent,
        )

    @patch('emails.services.season.sync_org_people')
    def test_season_tick_sends_opened_on_status_flip(self, mock_sync):
        from people.services.sync import SyncStats

        mock_sync.return_value = SyncStats()
        mail.outbox.clear()
        stats = run_season_tick()
        self.year.refresh_from_db()
        self.assertEqual(self.year.status, AwardYear.Status.VOTING)
        self.assertTrue(any('voting' in c for c in stats.status_changes))
        self.assertTrue(any(row.get('sent', 0) > 0 for row in stats.voting_opened))
        self.assertTrue(any('Voting is open' in m.subject for m in mail.outbox))

    @patch('emails.services.season.sync_org_people')
    def test_season_tick_sends_closed_on_status_flip(self, mock_sync):
        from people.services.sync import SyncStats

        mock_sync.return_value = SyncStats()
        self.year.status = AwardYear.Status.VOTING
        self.year.voting_closes_at = timezone.now() - timedelta(minutes=1)
        self.year.save(update_fields=['status', 'voting_closes_at'])
        mail.outbox.clear()

        stats = run_season_tick()
        self.year.refresh_from_db()
        self.assertEqual(self.year.status, AwardYear.Status.CLOSED)
        self.assertTrue(any(row.get('sent', 0) > 0 for row in stats.voting_closed))
        self.assertTrue(any('Voting has closed' in m.subject for m in mail.outbox))
