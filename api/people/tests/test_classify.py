from dataclasses import dataclass

from django.test import SimpleTestCase

from people.services.classify import (
    apply_classification,
    is_nigeria_eligible,
    resolve_company,
    resolve_electorate,
)


@dataclass
class FakePerson:
    is_active: bool = True
    department_code: str = 'IT'
    unit_name: str | None = None
    role_code: str = 'STAFF'


class NigeriaEligibilityTests(SimpleTestCase):
    def test_active_non_dubai_is_eligible(self):
        self.assertTrue(is_nigeria_eligible(FakePerson(department_code='TOURISM')))

    def test_dubai_excluded(self):
        self.assertFalse(is_nigeria_eligible(FakePerson(department_code='TOURISM_DUBAI')))

    def test_inactive_excluded(self):
        self.assertFalse(is_nigeria_eligible(FakePerson(is_active=False)))


class CompanyResolutionTests(SimpleTestCase):
    def test_tourism_department(self):
        self.assertEqual(
            resolve_company(FakePerson(department_code='TOURISM')),
            'tourism',
        )

    def test_tourism_internal_control_exception(self):
        person = FakePerson(
            department_code='INTERNAL_CONTROL',
            unit_name='Tourism Internal Control',
        )
        self.assertEqual(resolve_company(person), 'tourism')

    def test_tourism_accounts_exception(self):
        person = FakePerson(
            department_code='TRADING',
            unit_name='Tourism Accounts',
        )
        self.assertEqual(resolve_company(person), 'tourism')

    def test_internal_control_without_tourism_unit_is_global(self):
        person = FakePerson(
            department_code='INTERNAL_CONTROL',
            unit_name='Global Internal Control',
        )
        self.assertEqual(resolve_company(person), 'global')

    def test_trading_without_tourism_unit_is_global(self):
        person = FakePerson(department_code='TRADING', unit_name='Export')
        self.assertEqual(resolve_company(person), 'global')

    def test_default_global(self):
        self.assertEqual(resolve_company(FakePerson(department_code='HR')), 'global')

    def test_dubai_company_excluded(self):
        self.assertEqual(
            resolve_company(FakePerson(department_code='TOURISM_DUBAI')),
            'excluded',
        )

    def test_inactive_company_excluded(self):
        self.assertEqual(
            resolve_company(FakePerson(is_active=False, department_code='TOURISM')),
            'excluded',
        )


class ElectorateResolutionTests(SimpleTestCase):
    def test_staff(self):
        self.assertEqual(resolve_electorate(FakePerson(role_code='STAFF')), 'staff')

    def test_ed_is_executive(self):
        self.assertEqual(resolve_electorate(FakePerson(role_code='ED')), 'executive')

    def test_md_is_executive(self):
        self.assertEqual(resolve_electorate(FakePerson(role_code='MD')), 'executive')

    def test_unknown_role_ineligible(self):
        self.assertEqual(resolve_electorate(FakePerson(role_code='INTERN')), 'ineligible')

    def test_role_code_case_insensitive(self):
        self.assertEqual(resolve_electorate(FakePerson(role_code='ed')), 'executive')


class ApplyClassificationTests(SimpleTestCase):
    def test_mutates_person_fields(self):
        person = FakePerson(
            department_code='TOURISM',
            role_code='STAFF',
        )
        # Attach cache fields like OrgPerson
        person.company = ''
        person.electorate = ''
        person.is_nigeria_eligible = False

        apply_classification(person)

        self.assertTrue(person.is_nigeria_eligible)
        self.assertEqual(person.company, 'tourism')
        self.assertEqual(person.electorate, 'staff')
