from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from awards.models import Award, AwardYear, Nominee
from awards.seed import seed_year_2026
from people.models import OrgPerson
from voting.models import BallotToken, Vote
from voting.services.eligibility import awards_for_voter
from voting.services.tokens import generate_ballot_tokens


def _person(external_id, *, company, electorate='staff', **kwargs):
    role = 'ED' if electorate == 'executive' else 'STAFF'
    defaults = {
        'email': f'{company}{external_id}@incelgroup.com',
        'first_name': company.title(),
        'last_name': f'Voter{external_id}',
        'is_active': True,
        'role_code': role,
        'department_code': 'TOURISM' if company == 'tourism' else 'HR',
        'company': company,
        'electorate': electorate,
        'is_nigeria_eligible': True,
    }
    defaults.update(kwargs)
    return OrgPerson.objects.create(external_id=external_id, **defaults)


def _complete_votes_payload(person, year, *, open_person_id=None, nominee_overrides=None):
    """Build a full ballot payload covering every award the voter may answer."""
    overrides = nominee_overrides or {}
    items = []
    for award in awards_for_voter(person, year):
        if award.voting_mode == Award.VotingMode.STAFF_OPEN:
            items.append({
                'award_slug': award.slug,
                'selected_person_id': open_person_id or person.id,
            })
            continue
        nominee_id = overrides.get(award.slug)
        if nominee_id is None:
            nominee = (
                award.nominees.filter(is_confirmed=True).order_by('sort_order', 'id').first()
            )
            assert nominee is not None, f'No confirmed nominee for {award.slug}'
            nominee_id = nominee.id
        items.append({'award_slug': award.slug, 'nominee_id': nominee_id})
    return {'votes': items}


class BallotApiTests(APITestCase):
    def setUp(self):
        self.year = seed_year_2026()
        # Open voting for write tests
        now = timezone.now()
        self.year.status = AwardYear.Status.VOTING
        self.year.voting_opens_at = now - timedelta(hours=1)
        self.year.voting_closes_at = now + timedelta(days=7)
        self.year.save()

        self.tourism = _person(1, company='tourism')
        self.global_voter = _person(2, company='global')
        self.dubai = _person(
            3,
            company='excluded',
            is_nigeria_eligible=False,
            department_code='TOURISM_DUBAI',
        )

        generate_ballot_tokens(self.year)
        self.tourism_token = BallotToken.objects.get(
            year=self.year, person=self.tourism
        ).token
        self.global_token = BallotToken.objects.get(
            year=self.year, person=self.global_voter
        ).token

    def _ballot_url(self):
        return reverse('ballot-detail', kwargs={'year': 2026})

    def _votes_url(self):
        return reverse('ballot-votes', kwargs={'year': 2026})

    def _directory_url(self):
        return reverse('ballot-directory', kwargs={'year': 2026})

    def _results_url(self):
        return reverse('year-results', kwargs={'year': 2026})

    def test_ballot_requires_token(self):
        response = self.client.get(self._ballot_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tourism_ballot_filters_awards(self):
        response = self.client.get(self._ballot_url(), {'token': self.tourism_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = {a['slug'] for a in response.data['awards']}
        self.assertIn('employee-of-the-year-tourism', slugs)
        self.assertNotIn('employee-of-the-year-global', slugs)
        self.assertIn('rookie-of-the-year', slugs)  # shared
        self.assertIn('foodie-of-the-year', slugs)
        self.assertEqual(response.data['voter']['company'], 'tourism')
        self.assertFalse(response.data['is_submitted'])
        self.assertTrue(response.data['writes_allowed'])

    def test_global_ballot_filters_awards(self):
        response = self.client.get(
            self._ballot_url(),
            HTTP_X_BALLOT_TOKEN=self.global_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = {a['slug'] for a in response.data['awards']}
        self.assertIn('employee-of-the-year-global', slugs)
        self.assertNotIn('employee-of-the-year-tourism', slugs)
        self.assertIn('rookie-of-the-year', slugs)

    def test_put_complete_ballot_and_reject_resubmit(self):
        award = Award.objects.get(year=self.year, slug='employee-of-the-year-tourism')
        nominees = list(award.nominees.filter(is_confirmed=True).order_by('id'))
        self.assertGreaterEqual(len(nominees), 2)

        payload = _complete_votes_payload(
            self.tourism,
            self.year,
            open_person_id=self.global_voter.id,
            nominee_overrides={'employee-of-the-year-tourism': nominees[0].id},
        )
        response = self.client.put(
            self._votes_url(),
            payload,
            format='json',
            HTTP_X_BALLOT_TOKEN=self.tourism_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = len(awards_for_voter(self.tourism, self.year))
        self.assertEqual(Vote.objects.filter(voter=self.tourism).count(), expected)
        self.assertTrue(response.data['is_submitted'])
        self.assertFalse(response.data['writes_allowed'])
        self.assertIsNotNone(response.data['submitted_at'])

        token = BallotToken.objects.get(token=self.tourism_token)
        self.assertIsNotNone(token.submitted_at)

        # Resubmit / overwrite rejected
        payload = _complete_votes_payload(
            self.tourism,
            self.year,
            open_person_id=self.global_voter.id,
            nominee_overrides={'employee-of-the-year-tourism': nominees[1].id},
        )
        response = self.client.put(
            f'{self._votes_url()}?token={self.tourism_token}',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['code'], 'already_submitted')
        vote = Vote.objects.get(
            voter=self.tourism,
            award__slug='employee-of-the-year-tourism',
        )
        self.assertEqual(vote.nominee_id, nominees[0].id)

    def test_incomplete_ballot_rejected(self):
        award = Award.objects.get(year=self.year, slug='employee-of-the-year-tourism')
        nominee = award.nominees.filter(is_confirmed=True).first()
        response = self.client.put(
            self._votes_url(),
            {
                'votes': [
                    {
                        'award_slug': 'employee-of-the-year-tourism',
                        'nominee_id': nominee.id,
                    }
                ]
            },
            format='json',
            HTTP_X_BALLOT_TOKEN=self.tourism_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'incomplete_ballot')
        self.assertEqual(Vote.objects.filter(voter=self.tourism).count(), 0)

    def test_tourism_cannot_vote_global_award(self):
        award = Award.objects.get(year=self.year, slug='employee-of-the-year-global')
        nominee = award.nominees.filter(is_confirmed=True).first()
        payload = _complete_votes_payload(
            self.tourism,
            self.year,
            open_person_id=self.global_voter.id,
        )
        # Inject a forbidden award into an otherwise complete ballot.
        payload['votes'].append({
            'award_slug': 'employee-of-the-year-global',
            'nominee_id': nominee.id,
        })
        response = self.client.put(
            self._votes_url(),
            payload,
            format='json',
            HTTP_X_BALLOT_TOKEN=self.tourism_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'incomplete_ballot')

    def test_open_award_selected_person(self):
        payload = _complete_votes_payload(
            self.tourism,
            self.year,
            open_person_id=self.global_voter.id,
        )
        response = self.client.put(
            self._votes_url(),
            payload,
            format='json',
            HTTP_X_BALLOT_TOKEN=self.tourism_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vote = Vote.objects.get(
            voter=self.tourism,
            award__slug='foodie-of-the-year',
        )
        self.assertEqual(vote.selected_person_id, self.global_voter.id)
        self.assertIsNone(vote.nominee_id)

    def test_rejects_unconfirmed_nominee(self):
        award = Award.objects.get(year=self.year, slug='employee-of-the-year-tourism')
        bad = Nominee.objects.create(
            award=award,
            display_name='Not Confirmed',
            is_confirmed=False,
        )
        payload = _complete_votes_payload(
            self.tourism,
            self.year,
            open_person_id=self.global_voter.id,
            nominee_overrides={'employee-of-the-year-tourism': bad.id},
        )
        response = self.client.put(
            self._votes_url(),
            payload,
            format='json',
            HTTP_X_BALLOT_TOKEN=self.tourism_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_window_closed_rejects_writes(self):
        self.year.voting_closes_at = timezone.now() - timedelta(minutes=1)
        self.year.save(update_fields=['voting_closes_at'])
        payload = _complete_votes_payload(
            self.tourism,
            self.year,
            open_person_id=self.global_voter.id,
        )
        response = self.client.put(
            self._votes_url(),
            payload,
            format='json',
            HTTP_X_BALLOT_TOKEN=self.tourism_token,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['code'], 'window_closed')

    def test_directory_search_nigeria_eligible_only(self):
        response = self.client.get(
            self._directory_url(),
            {'token': self.tourism_token, 'q': 'Voter'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {row['id'] for row in response.data['results']}
        self.assertIn(self.tourism.id, ids)
        self.assertIn(self.global_voter.id, ids)
        self.assertNotIn(self.dubai.id, ids)

    def test_results_hidden_until_published(self):
        response = self.client.get(self._results_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.year.results_published_at = timezone.now()
        self.year.save(update_fields=['results_published_at'])
        response = self.client.get(self._results_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('awards', response.data)
        self.assertTrue(response.data['awards'])
        self.assertFalse(response.data.get('preview'))

    def test_results_committee_preview_token(self):
        self.year.results_published_at = None
        self.year.ensure_results_preview_token()
        bad = self.client.get(self._results_url(), {'preview': 'wrong'})
        self.assertEqual(bad.status_code, status.HTTP_403_FORBIDDEN)

        ok = self.client.get(
            self._results_url(),
            {'preview': self.year.results_preview_token},
        )
        self.assertEqual(ok.status_code, status.HTTP_200_OK)
        self.assertTrue(ok.data.get('preview'))
        self.assertTrue(ok.data['awards'])

    def test_results_audit_requires_preview_token(self):
        url = reverse('year-results-audit', kwargs={'year': 2026})
        self.year.ensure_results_preview_token()
        self.year.results_published_at = timezone.now()
        self.year.save(update_fields=['results_published_at'])

        # Even when public results are published, audit stays locked.
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

        ok = self.client.get(url, {'preview': self.year.results_preview_token})
        self.assertEqual(ok.status_code, status.HTTP_200_OK)
        self.assertIn('summary', ok.data)
        self.assertIn('methodology', ok.data)
        self.assertIn('awards', ok.data)
        self.assertIn('weighted', ok.data['methodology'])

    def test_results_missing_year_404(self):
        url = reverse('year-results', kwargs={'year': 1999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_revoked_token_rejected(self):
        token = BallotToken.objects.get(token=self.tourism_token)
        token.revoked_at = timezone.now()
        token.save(update_fields=['revoked_at'])
        response = self.client.get(self._ballot_url(), {'token': self.tourism_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
