from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from awards.models import AwardNotificationConfig, AwardYear
from awards.seed import seed_year_2026
from emails.services.season import (
    run_org_sync_tick,
    run_season_mail_tick,
    run_season_tick,
)
from people.dev_fixtures import build_dev_org_users
from people.models import OrgPerson
from people.services.sync import sync_org_people as real_sync
from voting.models import BallotToken


@override_settings(EMAIL_ENABLED=True, EMAIL_DEBUG=True)
class SeasonTickTests(TestCase):
    def setUp(self):
        self.year = seed_year_2026()
        now = timezone.now()
        self.year.status = AwardYear.Status.SCHEDULED
        self.year.voting_opens_at = now + timedelta(minutes=3)
        self.year.voting_closes_at = now + timedelta(days=1)
        self.year.save()
        config = AwardNotificationConfig.objects.get(
            year=self.year,
            event=AwardNotificationConfig.Event.VOTE_INVITE,
        )
        config.offset_minutes_before_open = 5
        config.enabled = True
        config.save()

    @patch('emails.services.season.sync_org_people')
    def test_full_tick_syncs_tokens_and_dispatches(self, mock_sync):
        mock_sync.side_effect = lambda: real_sync(build_dev_org_users())

        stats = run_season_tick()
        self.assertIsNotNone(stats.sync)
        self.assertGreaterEqual(OrgPerson.objects.filter(is_active=True).count(), 10)
        self.assertGreater(BallotToken.objects.filter(year=self.year).count(), 0)
        self.assertTrue(any(i.get('sent', 0) > 0 for i in stats.invites))

    @patch('emails.services.season.sync_org_people')
    def test_mail_tick_does_not_call_workspace_api(self, mock_sync):
        real_sync(build_dev_org_users())
        mock_sync.reset_mock()

        stats = run_season_mail_tick()
        mock_sync.assert_not_called()
        self.assertIsNone(stats.sync)
        self.assertGreater(BallotToken.objects.filter(year=self.year).count(), 0)
        self.assertTrue(any(i.get('sent', 0) > 0 for i in stats.invites))

    @patch('emails.services.season.sync_org_people')
    def test_org_sync_tick_does_not_send_invites(self, mock_sync):
        mock_sync.side_effect = lambda: real_sync(build_dev_org_users())

        stats = run_org_sync_tick()
        self.assertIsNotNone(stats.sync)
        self.assertGreater(BallotToken.objects.filter(year=self.year).count(), 0)
        self.assertFalse(hasattr(stats, 'invites'))

    @patch('emails.services.season.sync_org_people')
    def test_mail_tick_advances_status_when_open(self, mock_sync):
        real_sync(build_dev_org_users())
        mock_sync.reset_mock()
        self.year.voting_opens_at = timezone.now() - timedelta(minutes=1)
        self.year.save(update_fields=['voting_opens_at'])

        stats = run_season_mail_tick()
        mock_sync.assert_not_called()
        self.year.refresh_from_db()
        self.assertEqual(self.year.status, AwardYear.Status.VOTING)
        self.assertTrue(any('voting' in c for c in stats.status_changes))
