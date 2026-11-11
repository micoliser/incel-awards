from django.core.management import call_command
from django.test import TestCase, override_settings
from io import StringIO

from awards.models import AwardYear
from people.models import OrgPerson
from voting.models import BallotToken
from voting.services.tokens import generate_ballot_tokens


def _make_person(external_id, **kwargs):
    defaults = {
        'email': f'u{external_id}@incelgroup.com',
        'first_name': 'F',
        'last_name': 'L',
        'is_active': True,
        'role_code': 'STAFF',
        'department_code': 'HR',
        'company': 'global',
        'electorate': 'staff',
        'is_nigeria_eligible': True,
    }
    defaults.update(kwargs)
    return OrgPerson.objects.create(external_id=external_id, **defaults)


class GenerateBallotTokensTests(TestCase):
    def setUp(self):
        self.year = AwardYear.objects.create(
            year=2026,
            title='Employee Awards 2026',
            slug='2026',
        )

    def test_creates_for_staff_and_exec_only(self):
        staff = _make_person(1, electorate='staff', company='tourism', department_code='TOURISM')
        exec_p = _make_person(
            2,
            electorate='executive',
            role_code='ED',
            company='global',
        )
        _make_person(
            3,
            electorate='ineligible',
            role_code='INTERN',
            is_nigeria_eligible=True,
        )
        _make_person(
            4,
            is_nigeria_eligible=False,
            company='excluded',
            department_code='TOURISM_DUBAI',
        )

        stats = generate_ballot_tokens(self.year)
        self.assertEqual(stats.eligible, 2)
        self.assertEqual(stats.created, 2)
        tokens = BallotToken.objects.filter(year=self.year)
        self.assertEqual(tokens.count(), 2)
        person_ids = set(tokens.values_list('person_id', flat=True))
        self.assertEqual(person_ids, {staff.id, exec_p.id})
        for t in tokens:
            self.assertTrue(len(t.token) >= 32)

    def test_idempotent_unique_year_person(self):
        _make_person(1)
        generate_ballot_tokens(self.year)
        stats = generate_ballot_tokens(self.year)
        self.assertEqual(stats.created, 0)
        self.assertEqual(stats.skipped_existing, 1)
        self.assertEqual(BallotToken.objects.count(), 1)

    def test_management_command(self):
        _make_person(1)
        out = StringIO()
        call_command('generate_ballot_tokens', '--year', '2026', stdout=out)
        self.assertIn('created=1', out.getvalue())
        self.assertEqual(BallotToken.objects.count(), 1)

    def test_empty_exclusion_mints_for_everyone_eligible(self):
        keep = _make_person(1, email='hr@admin.com')
        with override_settings(BALLOT_EXCLUDED_EMAILS=[]):
            stats = generate_ballot_tokens(self.year)
        self.assertEqual(stats.eligible, 1)
        self.assertEqual(stats.created, 1)
        self.assertEqual(
            BallotToken.objects.filter(year=self.year).get().person_id,
            keep.id,
        )

    @override_settings(
        BALLOT_EXCLUDED_EMAILS=['hr@admin.com', 'samueliwelumo@gmail.com']
    )
    def test_excluded_emails_do_not_get_tokens(self):
        keep = _make_person(1, email='keeper@incelgroup.com')
        _make_person(2, email='hr@admin.com')
        _make_person(3, email='SamuelIwelumo@gmail.com')  # case-insensitive
        stats = generate_ballot_tokens(self.year)
        self.assertEqual(stats.eligible, 1)
        self.assertEqual(stats.created, 1)
        tokens = BallotToken.objects.filter(year=self.year)
        self.assertEqual(tokens.count(), 1)
        self.assertEqual(tokens.get().person_id, keep.id)

    @override_settings(
        BALLOT_EXCLUDED_EMAILS=['hr@admin.com', 'samueliwelumo@gmail.com']
    )
    def test_excluded_emails_are_not_recreated_after_delete(self):
        _make_person(1, email='hr@admin.com')
        # Simulate a pre-existing token that ops deletes from admin.
        person = OrgPerson.objects.get(email='hr@admin.com')
        BallotToken.objects.create(
            year=self.year,
            person=person,
            token='stale-token-should-not-return',
        )
        BallotToken.objects.filter(year=self.year, person=person).delete()
        stats = generate_ballot_tokens(self.year)
        self.assertEqual(stats.eligible, 0)
        self.assertEqual(stats.created, 0)
        self.assertFalse(
            BallotToken.objects.filter(year=self.year, person=person).exists()
        )
