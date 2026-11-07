from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from awards.models import Award, AwardNotificationConfig, AwardYear, Nominee
from awards.seed import seed_year_2026
from people.models import OrgPerson
from voting.models import BallotInviteDelivery, BallotToken, Vote, VoteAuditLog
from voting.services.reset_season import reset_season_for_testing
from voting.services.tokens import generate_ballot_tokens


def _staff(**kwargs):
    defaults = {
        'external_id': 5001,
        'email': 'reset@incelgroup.com',
        'first_name': 'Reset',
        'last_name': 'Tester',
        'is_active': True,
        'role_code': 'STAFF',
        'department_code': 'TOURISM',
        'company': 'tourism',
        'electorate': 'staff',
        'is_nigeria_eligible': True,
    }
    defaults.update(kwargs)
    return OrgPerson.objects.create(**defaults)


class ResetSeasonForTestingTests(TestCase):
    def setUp(self):
        self.year = seed_year_2026()
        now = timezone.now()
        self.year.status = AwardYear.Status.CLOSED
        self.year.voting_opens_at = now - timedelta(hours=2)
        self.year.voting_closes_at = now - timedelta(hours=1)
        self.year.results_published_at = now - timedelta(minutes=30)
        self.year.save()

        self.voter = _staff()
        generate_ballot_tokens(self.year)
        self.token = BallotToken.objects.get(year=self.year, person=self.voter)
        self.token.submitted_at = now
        self.token.save(update_fields=['submitted_at'])

        award = Award.objects.get(year=self.year, slug='employee-of-the-year-tourism')
        nominee = award.nominees.filter(is_confirmed=True).first()
        Vote.objects.create(
            award=award,
            voter=self.voter,
            nominee=nominee,
            electorate_at_vote='staff',
        )
        VoteAuditLog.objects.create(
            award=award,
            voter=self.voter,
            ballot_token=self.token,
            action=VoteAuditLog.Action.CREATED,
            electorate='staff',
            new_nominee=nominee,
        )
        BallotInviteDelivery.objects.create(
            token=self.token,
            event='vote_invite',
            sent_at=now,
            status=BallotInviteDelivery.Status.SENT,
        )
        BallotInviteDelivery.objects.create(
            token=self.token,
            event='eligibility_notice',
            sent_at=now,
            status=BallotInviteDelivery.Status.SENT,
        )

    def test_reset_clears_voting_and_email_state(self):
        awards_before = Award.objects.filter(year=self.year).count()
        nominees_before = Nominee.objects.filter(award__year=self.year).count()
        people_before = OrgPerson.objects.count()

        stats = reset_season_for_testing(
            self.year,
            opens_in_minutes=15,
            window_minutes=45,
            eligibility_offset_minutes=10,
            invite_offset_minutes=5,
            rotate_preview_token=True,
        )

        self.year.refresh_from_db()
        self.token.refresh_from_db()

        self.assertEqual(stats.votes_deleted, 1)
        self.assertEqual(stats.audit_logs_deleted, 1)
        self.assertEqual(stats.deliveries_deleted, 2)
        self.assertEqual(stats.tokens_unlocked, 1)
        self.assertEqual(stats.tokens_deleted, 0)
        self.assertTrue(stats.results_unpublished)
        self.assertTrue(stats.preview_token_rotated)

        self.assertEqual(Vote.objects.count(), 0)
        self.assertEqual(VoteAuditLog.objects.count(), 0)
        self.assertEqual(BallotInviteDelivery.objects.count(), 0)
        self.assertIsNone(self.token.submitted_at)
        self.assertEqual(self.year.status, AwardYear.Status.SCHEDULED)
        self.assertIsNone(self.year.results_published_at)
        self.assertIsNotNone(self.year.voting_opens_at)
        self.assertIsNotNone(self.year.voting_closes_at)
        self.assertGreater(self.year.voting_opens_at, timezone.now())
        self.assertEqual(
            (self.year.voting_closes_at - self.year.voting_opens_at),
            timedelta(minutes=45),
        )

        eligibility = AwardNotificationConfig.objects.get(
            year=self.year,
            event=AwardNotificationConfig.Event.ELIGIBILITY_NOTICE,
        )
        invite = AwardNotificationConfig.objects.get(
            year=self.year,
            event=AwardNotificationConfig.Event.VOTE_INVITE,
        )
        self.assertEqual(eligibility.offset_minutes_before_open, 10)
        self.assertEqual(invite.offset_minutes_before_open, 5)

        self.assertEqual(Award.objects.filter(year=self.year).count(), awards_before)
        self.assertEqual(
            Nominee.objects.filter(award__year=self.year).count(),
            nominees_before,
        )
        self.assertEqual(OrgPerson.objects.count(), people_before)

    def test_delete_tokens_option(self):
        stats = reset_season_for_testing(self.year, delete_tokens=True)
        self.assertEqual(stats.tokens_deleted, 1)
        self.assertFalse(BallotToken.objects.filter(year=self.year).exists())

    def test_command_requires_confirm(self):
        with self.assertRaises(CommandError):
            call_command('reset_season_for_testing', year=2026)

    def test_command_with_confirm(self):
        call_command(
            'reset_season_for_testing',
            year=2026,
            confirm=True,
            opens_in_minutes=20,
            eligibility_offset=10,
            invite_offset=5,
        )
        self.year.refresh_from_db()
        self.assertEqual(self.year.status, AwardYear.Status.SCHEDULED)
        self.assertEqual(Vote.objects.count(), 0)
        self.assertEqual(BallotInviteDelivery.objects.count(), 0)
