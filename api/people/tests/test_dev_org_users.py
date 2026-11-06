from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from people.dev_fixtures import build_dev_org_users


@override_settings(
    DEV_ORG_USERS_ENABLED=True,
    ORG_USERS_API_TOKEN='dev-org-token',
    ORG_USERS_API_AUTH_SCHEME='Bearer',
)
class DevOrgUsersApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_requires_token(self):
        response = self.client.get('/api/v1/external/users')
        self.assertEqual(response.status_code, 401)

    def test_returns_fifteen_users_with_bearer(self):
        response = self.client.get(
            '/api/v1/external/users',
            HTTP_AUTHORIZATION='Bearer dev-org-token',
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        self.assertEqual(len(results), 15)
        self.assertEqual(len(build_dev_org_users()), 15)
        self.assertIn('id', results[0])
        self.assertIn('email', results[0])
        self.assertIn('department_code', results[0])

    def test_trailing_slash_also_works(self):
        response = self.client.get(
            '/api/v1/external/users/',
            HTTP_AUTHORIZATION='Bearer dev-org-token',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 15)


@override_settings(DEV_ORG_USERS_ENABLED=False)
class DevOrgUsersDisabledTests(TestCase):
    def test_disabled_returns_404(self):
        client = APIClient()
        response = client.get('/api/v1/external/users')
        self.assertEqual(response.status_code, 404)
