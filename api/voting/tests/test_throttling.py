"""Ballot endpoint throttle trips (token-scoped)."""

from datetime import timedelta

from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from awards.models import Award, AwardYear
from awards.seed import seed_year_2026
from people.models import OrgPerson
from voting.models import BallotToken
from voting.services.eligibility import awards_for_voter
from voting.services.tokens import generate_ballot_tokens


LOW_RATES = {
    'ballot_resolve': '2/min',
    # Ballots are immutable after submit, so vote throttle must trip on the
    # second attempt (first succeeds, second is 429 before already_submitted).
    'ballot_vote': '1/min',
    'ballot_directory': '2/min',
}

THROTTLE_TEST_DRF = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_RATES': LOW_RATES,
}


def _complete_votes_payload(person, year):
    items = []
    for award in awards_for_voter(person, year):
        if award.voting_mode == Award.VotingMode.STAFF_OPEN:
            items.append({
                'award_slug': award.slug,
                'selected_person_id': person.id,
            })
            continue
        nominee = (
            award.nominees.filter(is_confirmed=True).order_by('sort_order', 'id').first()
        )
        assert nominee is not None, f'No confirmed nominee for {award.slug}'
        items.append({'award_slug': award.slug, 'nominee_id': nominee.id})
    return {'votes': items}


@override_settings(REST_FRAMEWORK=THROTTLE_TEST_DRF)
class BallotThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.year = seed_year_2026()
        now = timezone.now()
        self.year.status = AwardYear.Status.VOTING
        self.year.voting_opens_at = now - timedelta(hours=1)
        self.year.voting_closes_at = now + timedelta(days=7)
        self.year.save()

        self.voter = OrgPerson.objects.create(
            external_id=9001,
            email='throttle@incelgroup.com',
            first_name='Throttle',
            last_name='Tester',
            is_active=True,
            role_code='STAFF',
            department_code='TOURISM',
            company='tourism',
            electorate='staff',
            is_nigeria_eligible=True,
        )
        generate_ballot_tokens(self.year)
        self.token = BallotToken.objects.get(year=self.year, person=self.voter).token

    def tearDown(self):
        cache.clear()

    def test_ballot_resolve_throttles_after_limit(self):
        url = reverse('ballot-detail', kwargs={'year': 2026})
        for _ in range(2):
            response = self.client.get(url, {'token': self.token})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(url, {'token': self.token})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_vote_submit_throttles_after_limit(self):
        url = reverse('ballot-votes', kwargs={'year': 2026})
        payload = _complete_votes_payload(self.voter, self.year)
        response = self.client.put(
            f'{url}?token={self.token}',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.put(
            f'{url}?token={self.token}',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_directory_throttles_after_limit(self):
        url = reverse('ballot-directory', kwargs={'year': 2026})
        for _ in range(2):
            response = self.client.get(url, {'token': self.token})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(url, {'token': self.token})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_different_tokens_have_separate_buckets(self):
        other = OrgPerson.objects.create(
            external_id=9002,
            email='other@incelgroup.com',
            first_name='Other',
            last_name='Voter',
            is_active=True,
            role_code='STAFF',
            department_code='HR',
            company='global',
            electorate='staff',
            is_nigeria_eligible=True,
        )
        generate_ballot_tokens(self.year)
        other_token = BallotToken.objects.get(year=self.year, person=other).token

        url = reverse('ballot-detail', kwargs={'year': 2026})
        for _ in range(2):
            self.assertEqual(
                self.client.get(url, {'token': self.token}).status_code,
                status.HTTP_200_OK,
            )
        self.assertEqual(
            self.client.get(url, {'token': self.token}).status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )
        # Other token still allowed
        self.assertEqual(
            self.client.get(url, {'token': other_token}).status_code,
            status.HTTP_200_OK,
        )
