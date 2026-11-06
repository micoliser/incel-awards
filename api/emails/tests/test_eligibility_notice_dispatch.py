from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from awards.models import Award, AwardNotificationConfig, AwardYear, Nominee
from emails.services.dispatch import (
    dispatch_eligibility_notices,
    earliest_send_at,
)
from emails.services.eligibility_notice_emails import (
    build_eligibility_notice_context,
)
from people.models import OrgPerson
from voting.models import BallotInviteDelivery, BallotToken
from voting.services.tokens import generate_token_value


def _make_person(external_id, **kwargs):
    defaults = {
        'email': f'u{external_id}@incelgroup.com',
        'first_name': 'Ada',
        'last_name': f'Person{external_id}',
        'is_active': True,
        'role_code': 'STAFF',
        'department_code': 'TOURISM',
        'company': 'tourism',
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
class EligibilityNoticeDispatchTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.year = AwardYear.objects.create(
            year=2026,
            title='Employee Awards 2026',
            slug='2026',
            status=AwardYear.Status.SCHEDULED,
            voting_opens_at=now + timedelta(minutes=8),
            voting_closes_at=now + timedelta(days=7),
        )
        self.config = AwardNotificationConfig.objects.create(
            year=self.year,
            event=AwardNotificationConfig.Event.ELIGIBILITY_NOTICE,
            enabled=True,
            channel=AwardNotificationConfig.Channel.EMAIL,
            audience=AwardNotificationConfig.Audience.ALL_ELIGIBLE,
            offset_minutes_before_open=10,
            subject_template="You're eligible to vote — Incel Employee Awards {year}",
        )
        self.award = Award.objects.create(
            year=self.year,
            slug='employee-tourism',
            name='Employee of the Year (Tourism)',
            division=Award.Division.TOURISM,
            voting_mode=Award.VotingMode.WEIGHTED,
        )
        Nominee.objects.create(
            award=self.award,
            display_name='Secret Nominee',
            is_confirmed=True,
        )
        self.person = _make_person(1)
        self.token = BallotToken.objects.create(
            year=self.year,
            person=self.person,
            token=generate_token_value(),
        )

    def test_dispatch_respects_offset_too_early(self):
        self.year.voting_opens_at = timezone.now() + timedelta(hours=2)
        self.year.save(update_fields=['voting_opens_at'])
        gate = earliest_send_at(self.year, self.config)
        self.assertIsNotNone(gate)
        self.assertGreater(gate, timezone.now())

        stats = dispatch_eligibility_notices(self.year, force=False)
        self.assertEqual(stats.exited_early, 'too_early')
        self.assertEqual(stats.sent, 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_dispatch_sends_when_within_window(self):
        # opens in 8m with 10m offset → earliest was 2m ago → send now
        stats = dispatch_eligibility_notices(self.year, force=False)
        self.assertEqual(stats.exited_early, '')
        self.assertEqual(stats.sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        delivery = BallotInviteDelivery.objects.get(token=self.token)
        self.assertEqual(delivery.status, BallotInviteDelivery.Status.SENT)
        self.assertEqual(delivery.event, 'eligibility_notice')

        body = mail.outbox[0].body
        self.assertIn('Employee of the Year (Tourism)', body)
        self.assertNotIn('Secret Nominee', body)
        self.assertNotIn(self.token.token, body)
        self.assertIn('/2026', mail.outbox[0].alternatives[0][0])

    def test_context_lists_categories_not_nominees(self):
        ctx = build_eligibility_notice_context(self.token)
        self.assertEqual(ctx['award_names'], ['Employee of the Year (Tourism)'])
        self.assertNotIn('Secret Nominee', str(ctx))

    def test_idempotent(self):
        dispatch_eligibility_notices(self.year, force=True)
        stats = dispatch_eligibility_notices(self.year, force=True)
        self.assertEqual(stats.sent, 0)
        self.assertEqual(stats.skipped_already_sent, 1)
        self.assertEqual(len(mail.outbox), 1)
