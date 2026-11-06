from unittest.mock import MagicMock, patch

from django.test import TestCase

from people.models import OrgPerson
from people.services.org_client import OrgUsersClient
from people.services.sync import sync_org_people


def _user(
    uid,
    *,
    email=None,
    first='First',
    last='Last',
    active=True,
    role='STAFF',
    dept='IT',
    unit=None,
):
    return {
        'id': uid,
        'email': email or f'user{uid}@incelgroup.com',
        'first_name': first,
        'last_name': last,
        'is_active': active,
        'role_code': role,
        'role_name': role,
        'department_code': dept,
        'department_name': dept,
        'unit_name': unit,
    }


class OrgSyncClassificationTests(TestCase):
    def test_sync_classifies_tourism_global_dubai_exec(self):
        users = [
            _user(1, first='Tour', last='Staff', dept='TOURISM', role='STAFF'),
            _user(2, first='Glob', last='Staff', dept='HR', role='STAFF'),
            _user(3, first='Dubai', last='Staff', dept='TOURISM_DUBAI', role='STAFF'),
            _user(4, first='Exec', last='Boss', dept='TOURISM', role='ED'),
            _user(
                5,
                first='IC',
                last='Tourism',
                dept='INTERNAL_CONTROL',
                unit='Tourism Internal Control',
                role='STAFF',
            ),
            _user(
                6,
                first='Acct',
                last='Tourism',
                dept='TRADING',
                unit='Tourism Accounts',
                role='MD',
            ),
            _user(7, first='Intern', last='X', dept='IT', role='INTERN'),
        ]

        stats = sync_org_people(users)
        self.assertEqual(stats.fetched, 7)
        self.assertEqual(stats.created, 7)

        tourism = OrgPerson.objects.get(external_id=1)
        self.assertTrue(tourism.is_nigeria_eligible)
        self.assertEqual(tourism.company, 'tourism')
        self.assertEqual(tourism.electorate, 'staff')

        global_staff = OrgPerson.objects.get(external_id=2)
        self.assertTrue(global_staff.is_nigeria_eligible)
        self.assertEqual(global_staff.company, 'global')
        self.assertEqual(global_staff.electorate, 'staff')

        dubai = OrgPerson.objects.get(external_id=3)
        self.assertFalse(dubai.is_nigeria_eligible)
        self.assertEqual(dubai.company, 'excluded')

        exec_person = OrgPerson.objects.get(external_id=4)
        self.assertEqual(exec_person.electorate, 'executive')
        self.assertEqual(exec_person.company, 'tourism')

        ic = OrgPerson.objects.get(external_id=5)
        self.assertEqual(ic.company, 'tourism')

        md = OrgPerson.objects.get(external_id=6)
        self.assertEqual(md.company, 'tourism')
        self.assertEqual(md.electorate, 'executive')

        intern = OrgPerson.objects.get(external_id=7)
        self.assertEqual(intern.electorate, 'ineligible')
        self.assertTrue(intern.is_nigeria_eligible)

    def test_soft_deactivate_missing_and_inactive(self):
        sync_org_people([_user(10, dept='TOURISM'), _user(11, dept='HR')])
        self.assertEqual(OrgPerson.objects.filter(is_active=True).count(), 2)

        stats = sync_org_people([
            _user(10, dept='TOURISM', active=False),
            # 11 missing from feed
        ])
        self.assertEqual(stats.deactivated, 1)

        p10 = OrgPerson.objects.get(external_id=10)
        self.assertFalse(p10.is_active)
        self.assertFalse(p10.is_nigeria_eligible)

        p11 = OrgPerson.objects.get(external_id=11)
        self.assertFalse(p11.is_active)
        self.assertFalse(p11.is_nigeria_eligible)

    def test_upsert_updates_existing(self):
        sync_org_people([_user(20, first='Old', dept='HR')])
        sync_org_people([_user(20, first='New', dept='TOURISM')])
        person = OrgPerson.objects.get(external_id=20)
        self.assertEqual(person.first_name, 'New')
        self.assertEqual(person.company, 'tourism')
        self.assertEqual(OrgPerson.objects.count(), 1)

    @patch.object(OrgUsersClient, 'fetch_all_users')
    def test_client_fetch_path(self, mock_fetch):
        mock_fetch.return_value = [_user(99, dept='TOURISM')]
        stats = sync_org_people()
        self.assertEqual(stats.created, 1)
        mock_fetch.assert_called_once()


class OrgUsersClientTests(TestCase):
    def test_paginated_results(self):
        session = MagicMock()
        page1 = MagicMock()
        page1.status_code = 200
        page1.json.return_value = {
            'results': [_user(1)],
            'next': 'http://example.test/users/?page=2',
        }
        page2 = MagicMock()
        page2.status_code = 200
        page2.json.return_value = {'results': [_user(2)], 'next': None}
        session.get.side_effect = [page1, page2]

        client = OrgUsersClient(
            base_url='http://example.test',
            token='secret',
            session=session,
        )
        users = client.fetch_all_users()
        self.assertEqual(len(users), 2)
        self.assertEqual(session.get.call_count, 2)
        first_call = session.get.call_args_list[0]
        self.assertEqual(first_call.args[0], 'http://example.test/api/v1/external/users')
        headers = first_call.kwargs['headers']
        self.assertEqual(headers['Authorization'], 'Bearer secret')
        self.assertEqual(headers['Accept'], 'application/json')
