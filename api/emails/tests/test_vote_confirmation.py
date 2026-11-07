from datetime import timedelta

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from awards.models import AwardYear
from awards.seed import seed_year_2026
from emails.services.vote_confirmation_emails import (
    EVENT,
    send_vote_confirmation_email,
)
from people.models import OrgPerson
from voting.models import BallotInviteDelivery, BallotToken
from voting.services.eligibility import awards_for_voter
from voting.services.tokens import generate_ballot_tokens
from voting.tests.test_ballot_api import _complete_votes_payload


def _person(external_id, *, company='tourism', **kwargs):
    defaults = {
        'email': f'confirm{external_id}@incelgroup.com',
        'first_name': 'Confirm',
        'last_name': f'Voter{external_id}',
        'is_active': True,
        'role_code': 'STAFF',
        'department_code': 'TOURISM' if company == 'tourism' else 'HR',
        'company': company,
        'electorate': 'staff',
        'is_nigeria_eligible': True,
    }
    defaults.update(kwargs)
    return OrgPerson.objects.create(external_id=external_id, **defaults)


@override_settings(
    EMAIL_ENABLED=True,
    EMAIL_DEBUG=False,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    FRONTEND_BASE_URL='https://awards.example.com',
    EMAIL_SENDER_NAME='Incel Group Awards',
)
class VoteConfirmationEmailTests(APITestCase):
    def setUp(self):
        self.year = seed_year_2026()
        now = timezone.now()
        self.year.status = AwardYear.Status.VOTING
        self.year.voting_opens_at = now - timedelta(hours=1)
        self.year.voting_closes_at = now + timedelta(days=1)
        self.year.save()

        self.voter = _person(1, company='tourism')
        self.other = _person(2, company='global')
        generate_ballot_tokens(self.year)
        self.token = BallotToken.objects.get(year=self.year, person=self.voter)

    def test_send_confirmation_direct(self):
        self.token.submitted_at = timezone.now()
        self.token.save(update_fields=['submitted_at'])

        ok = send_vote_confirmation_email(self.token, award_count=5)
        self.assertTrue(ok)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertIn(self.voter.email, msg.to)
        self.assertIn('Ballot received', msg.subject)
        self.assertIn('final', msg.body.lower())
        self.assertNotIn('nominee', msg.body.lower())

        delivery = BallotInviteDelivery.objects.get(token=self.token, event=EVENT)
        self.assertEqual(delivery.status, BallotInviteDelivery.Status.SENT)

        # Idempotent — second call does not duplicate
        ok2 = send_vote_confirmation_email(self.token, award_count=5)
        self.assertTrue(ok2)
        self.assertEqual(len(mail.outbox), 1)

    def test_submit_ballot_queues_confirmation(self):
        payload = _complete_votes_payload(
            self.voter,
            self.year,
            open_person_id=self.other.id,
        )
        url = reverse('ballot-votes', kwargs={'year': 2026})
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.put(
                url,
                payload,
                format='json',
                HTTP_X_BALLOT_TOKEN=self.token.token,
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_submitted'])

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Ballot received', mail.outbox[0].subject)
        expected = len(awards_for_voter(self.voter, self.year))
        self.assertIn(str(expected), mail.outbox[0].body)

        delivery = BallotInviteDelivery.objects.get(token=self.token, event=EVENT)
        self.assertEqual(delivery.status, BallotInviteDelivery.Status.SENT)

    @override_settings(EMAIL_ENABLED=False)
    def test_disabled_email_records_skipped(self):
        self.token.submitted_at = timezone.now()
        self.token.save(update_fields=['submitted_at'])
        ok = send_vote_confirmation_email(self.token, award_count=3)
        self.assertFalse(ok)
        self.assertEqual(len(mail.outbox), 0)
        delivery = BallotInviteDelivery.objects.get(token=self.token, event=EVENT)
        self.assertEqual(delivery.status, BallotInviteDelivery.Status.SKIPPED)
