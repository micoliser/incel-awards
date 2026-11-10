from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from awards.models import Award, AwardYear, Nominee
from awards.seed import seed_year_2026


class PublicReadApiTests(APITestCase):
    def setUp(self):
        self.year = seed_year_2026()

    def test_years_list_includes_2026(self):
        url = reverse('year-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        years = [row['year'] for row in response.data]
        self.assertIn(2026, years)
        row = next(r for r in response.data if r['year'] == 2026)
        self.assertEqual(row['title'], self.year.title)
        self.assertIn('status', row)
        self.assertIn('voting_opens_at', row)
        self.assertIn('voting_closes_at', row)

    def test_year_detail_shape_and_counts(self):
        url = reverse('year-detail', kwargs={'year': 2026})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['year'], 2026)
        self.assertEqual(data['awards_count'], 14)
        self.assertGreater(data['confirmed_nominees_count'], 0)
        self.assertIn('voting_window_status', data)
        self.assertIn('description', data)
        # No tallies / tokens
        self.assertNotIn('votes', data)
        self.assertNotIn('ballot_tokens', data)
        self.assertNotIn('tallies', data)

    def test_empty_year_404(self):
        for name, kwargs in (
            ('year-detail', {'year': 1999}),
            ('year-award-list', {'year': 1999}),
            (
                'year-award-detail',
                {'year': 1999, 'slug': 'employee-of-the-year-tourism'},
            ),
        ):
            url = reverse(name, kwargs=kwargs)
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_404_NOT_FOUND,
                msg=f'{name} should 404 for missing year',
            )

    def test_awards_list_2026(self):
        url = reverse('year-award-list', kwargs={'year': 2026})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 14)
        slugs = {row['slug'] for row in response.data}
        self.assertIn('employee-of-the-year-tourism', slugs)
        self.assertIn('employees-choice-of-the-year', slugs)
        sample = response.data[0]
        for key in (
            'slug',
            'name',
            'description',
            'ideal_winner',
            'division',
            'voting_mode',
            'executive_weight',
            'staff_weight',
        ):
            self.assertIn(key, sample)
        self.assertNotIn('nominees', sample)
        self.assertNotIn('votes', sample)

    def test_awards_list_division_filter(self):
        url = reverse('year-award-list', kwargs={'year': 2026})
        response = self.client.get(url, {'division': 'tourism'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)
        self.assertTrue(all(row['division'] == 'tourism' for row in response.data))

        shared = self.client.get(url, {'division': 'shared'})
        self.assertEqual(shared.status_code, status.HTTP_200_OK)
        self.assertEqual(len(shared.data), 6)

    def test_award_detail_includes_criteria_nominees_rules(self):
        url = reverse(
            'year-award-detail',
            kwargs={'year': 2026, 'slug': 'employee-of-the-year-tourism'},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['slug'], 'employee-of-the-year-tourism')
        self.assertEqual(data['division'], 'tourism')
        self.assertEqual(data['voting_mode'], 'weighted')
        self.assertIn('lifts the team around them', data['description'])
        self.assertEqual(len(data['ideal_winner'].splitlines()), 4)
        self.assertEqual(len(data['criteria']), 5)
        self.assertEqual(len(data['nominees']), 5)
        names = [n['display_name'] for n in data['nominees']]
        self.assertTrue(all(isinstance(n, str) and n.strip() for n in names))
        rules = data['voting_rules']
        self.assertEqual(rules['division'], 'tourism')
        self.assertEqual(rules['mode'], 'weighted')
        self.assertEqual(str(rules['executive_weight']), '0.30')
        self.assertEqual(str(rules['staff_weight']), '0.70')
        self.assertNotIn('votes', data)
        self.assertNotIn('tallies', data)

    def test_unconfirmed_nominees_excluded(self):
        award = Award.objects.get(
            year=self.year,
            slug='pioneer-award-for-innovation',
        )
        Nominee.objects.create(
            award=award,
            nominee_type=Nominee.NomineeType.PERSON,
            display_name='Unconfirmed Shadow Nominee',
            is_confirmed=False,
            sort_order=99,
        )
        url = reverse(
            'year-award-detail',
            kwargs={'year': 2026, 'slug': 'pioneer-award-for-innovation'},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [n['display_name'] for n in response.data['nominees']]
        self.assertNotIn('Unconfirmed Shadow Nominee', names)
        self.assertEqual(len(names), 5)

    def test_inactive_award_hidden(self):
        award = Award.objects.get(
            year=self.year,
            slug='foodie-of-the-year',
        )
        award.is_active = False
        award.save(update_fields=['is_active'])

        list_url = reverse('year-award-list', kwargs={'year': 2026})
        list_resp = self.client.get(list_url)
        slugs = {row['slug'] for row in list_resp.data}
        self.assertNotIn('foodie-of-the-year', slugs)

        detail_url = reverse(
            'year-award-detail',
            kwargs={'year': 2026, 'slug': 'foodie-of-the-year'},
        )
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_health_still_ok(self):
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
