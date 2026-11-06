"""VoteAuditLog rows written on create; resubmits are rejected."""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from awards.models import Award, AwardYear, Nominee
from people.models import OrgPerson
from voting.models import BallotToken, VoteAuditLog
from voting.services.tokens import generate_ballot_tokens
from voting.services.votes import VoteValidationError, upsert_votes


def _person(external_id, **kwargs):
    defaults = {
        'email': f'p{external_id}@incelgroup.com',
        'first_name': f'P{external_id}',
        'last_name': 'Test',
        'is_active': True,
        'role_code': 'STAFF',
        'department_code': 'TOURISM',
        'company': 'tourism',
        'electorate': 'staff',
        'is_nigeria_eligible': True,
    }
    defaults.update(kwargs)
    return OrgPerson.objects.create(external_id=external_id, **defaults)


class VoteAuditLogTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.year = AwardYear.objects.create(
            year=2026,
            title='Y',
            slug='2026',
            status=AwardYear.Status.VOTING,
            voting_opens_at=now - timedelta(hours=1),
            voting_closes_at=now + timedelta(days=1),
        )
        self.award = Award.objects.create(
            year=self.year,
            slug='employee-tourism',
            name='Employee',
            division=Award.Division.TOURISM,
            voting_mode=Award.VotingMode.WEIGHTED,
        )
        self.n1 = Nominee.objects.create(
            award=self.award, display_name='Mercy', is_confirmed=True
        )
        self.n2 = Nominee.objects.create(
            award=self.award, display_name='Michael', is_confirmed=True
        )
        self.voter = _person(1)
        generate_ballot_tokens(self.year)
        self.token = BallotToken.objects.get(year=self.year, person=self.voter)

    def test_create_writes_audit_log(self):
        upsert_votes(
            year=self.year,
            voter=self.voter,
            ballot_token=self.token,
            items=[{'award_slug': self.award.slug, 'nominee_id': self.n1.id}],
        )
        logs = list(VoteAuditLog.objects.filter(award=self.award, voter=self.voter))
        self.assertEqual(len(logs), 1)
        log = logs[0]
        self.assertEqual(log.action, VoteAuditLog.Action.CREATED)
        self.assertIsNone(log.previous_nominee_id)
        self.assertEqual(log.new_nominee_id, self.n1.id)
        self.assertEqual(log.electorate, 'staff')
        self.assertEqual(log.ballot_token_id, self.token.id)
        self.token.refresh_from_db()
        self.assertIsNotNone(self.token.submitted_at)

    def test_resubmit_rejected_without_updated_audit(self):
        upsert_votes(
            year=self.year,
            voter=self.voter,
            ballot_token=self.token,
            items=[{'award_slug': self.award.slug, 'nominee_id': self.n1.id}],
        )
        with self.assertRaises(VoteValidationError) as ctx:
            upsert_votes(
                year=self.year,
                voter=self.voter,
                ballot_token=self.token,
                items=[{'award_slug': self.award.slug, 'nominee_id': self.n2.id}],
            )
        self.assertEqual(ctx.exception.code, 'already_submitted')
        logs = list(
            VoteAuditLog.objects.filter(award=self.award, voter=self.voter).order_by(
                'created_at'
            )
        )
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, VoteAuditLog.Action.CREATED)
        self.assertEqual(logs[0].new_nominee_id, self.n1.id)
