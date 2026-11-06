from datetime import timedelta
from io import StringIO

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from awards.models import AwardNotificationConfig, AwardYear
from emails.services.dispatch import dispatch_vote_invites, earliest_send_at
from emails.services.vote_invite_emails import ballot_vote_url, send_vote_invite_email
from people.models import OrgPerson
from voting.models import BallotInviteDelivery, BallotToken
from voting.services.tokens import generate_ballot_tokens, generate_token_value


def _make_person(external_id, **kwargs):
    defaults = {
        'email': f'u{external_id}@incelgroup.com',
        'first_name': 'Ada',
        'last_name': f'Person{external_id}',
        'is_active': True,
        'role_code': 'STAFF',
        'department_code': 'HR',
        'company': 'global',
        'electorate': 'staff',
        'is_nigeria_eligible': True,
    }
    defaults.update(kwargs)
    return OrgPerson.objects.create(external_id=external_id, **defaults)


@override_settings(
    EMAIL_ENABLED=True,
    EMAIL_DEBUG=False,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    FRONTEND_BASE_URL='http://localhost:3000',
    DEFAULT_FROM_EMAIL='awards@incelgroup.com',
    EMAIL_SENDER_NAME='Incel Group Awards',
)
class VoteInviteDispatchTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.year = AwardYear.objects.create(
            year=2026,
            title='Employee Awards 2026',
            slug='2026',
            status=AwardYear.Status.SCHEDULED,
            voting_opens_at=now + timedelta(minutes=30),
            voting_closes_at=now + timedelta(days=7),
        )
        self.config = AwardNotificationConfig.objects.create(
            year=self.year,
            event=AwardNotificationConfig.Event.VOTE_INVITE,
            enabled=True,
            channel=AwardNotificationConfig.Channel.EMAIL,
            audience=AwardNotificationConfig.Audience.ALL_ELIGIBLE,
            offset_minutes_before_open=60,
            subject_template='Cast your vote — Incel Employee Awards {year}',
        )
        self.person = _make_person(1)
        self.token = BallotToken.objects.create(
            year=self.year,
            person=self.person,
            token=generate_token_value(),
        )

    def test_email_disabled_logs_and_skips_delivery(self):
        with override_settings(EMAIL_ENABLED=False):
            stats = dispatch_vote_invites(self.year, force=True)
        self.assertEqual(stats.exited_early, 'email_disabled')
        self.assertEqual(stats.sent, 0)
        self.assertEqual(BallotInviteDelivery.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_dispatch_respects_offset_too_early(self):
        # opens in 30m, offset 60m → earliest send is 30m ago? Wait:
        # opens_at = now+30, offset=60 → earliest = now+30-60 = now-30 → already past.
        # Make opens far in the future so we're before the gate.
        self.year.voting_opens_at = timezone.now() + timedelta(hours=5)
        self.year.save(update_fields=['voting_opens_at'])
        gate = earliest_send_at(self.year, self.config)
        self.assertIsNotNone(gate)
        self.assertGreater(gate, timezone.now())

        stats = dispatch_vote_invites(self.year, force=False)
        self.assertEqual(stats.exited_early, 'too_early')
        self.assertEqual(stats.sent, 0)
        self.assertEqual(BallotInviteDelivery.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_dispatch_sends_when_within_window(self):
        # opens in 30m with 60m offset → earliest was 30m ago → send now
        stats = dispatch_vote_invites(self.year, force=False)
        self.assertEqual(stats.exited_early, '')
        self.assertEqual(stats.sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        delivery = BallotInviteDelivery.objects.get(token=self.token)
        self.assertEqual(delivery.status, BallotInviteDelivery.Status.SENT)
        self.assertEqual(delivery.event, 'vote_invite')
        msg = mail.outbox[0]
        self.assertIn(self.person.email, msg.to)
        self.assertIn('/2026/vote?token=', msg.body)
        self.assertIn(self.token.token, msg.body)

    def test_force_bypasses_timing(self):
        self.year.voting_opens_at = timezone.now() + timedelta(days=10)
        self.year.save(update_fields=['voting_opens_at'])
        stats = dispatch_vote_invites(self.year, force=False)
        self.assertEqual(stats.exited_early, 'too_early')

        stats = dispatch_vote_invites(self.year, force=True)
        self.assertEqual(stats.exited_early, '')
        self.assertEqual(stats.sent, 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_idempotent_second_run_no_duplicate(self):
        dispatch_vote_invites(self.year, force=True)
        self.assertEqual(BallotInviteDelivery.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

        stats = dispatch_vote_invites(self.year, force=True)
        self.assertEqual(stats.sent, 0)
        self.assertEqual(stats.skipped_already_sent, 1)
        self.assertEqual(BallotInviteDelivery.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_disabled_config_exits(self):
        self.config.enabled = False
        self.config.save(update_fields=['enabled'])
        stats = dispatch_vote_invites(self.year, force=True)
        self.assertEqual(stats.exited_early, 'disabled')
        self.assertEqual(len(mail.outbox), 0)

    def test_management_command_force(self):
        self.year.voting_opens_at = timezone.now() + timedelta(days=3)
        self.year.save(update_fields=['voting_opens_at'])
        out = StringIO()
        call_command(
            'dispatch_vote_invites',
            '--year',
            '2026',
            '--force',
            stdout=out,
        )
        self.assertIn('sent=1', out.getvalue())
        self.assertEqual(BallotInviteDelivery.objects.count(), 1)

    def test_ballot_url_format(self):
        url = ballot_vote_url(self.token)
        self.assertEqual(
            url,
            f'http://localhost:3000/2026/vote?token={self.token.token}',
        )

    def test_email_debug_counts_as_sent_without_smtp(self):
        with override_settings(EMAIL_DEBUG=True):
            ok = send_vote_invite_email(self.token, is_async=False)
        self.assertTrue(ok)
        self.assertEqual(len(mail.outbox), 0)

    def test_all_eligible_audience_maps_to_nigeria_tokens(self):
        tourism = _make_person(
            2, company='tourism', department_code='TOURISM', email='t@incelgroup.com'
        )
        generate_ballot_tokens(self.year)
        self.assertTrue(
            BallotToken.objects.filter(year=self.year, person=tourism).exists()
        )
        # Ensure within window
        stats = dispatch_vote_invites(self.year, force=True)
        self.assertEqual(stats.audience_total, 2)
        self.assertEqual(stats.sent, 2)
