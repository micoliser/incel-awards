from django.test import TestCase

from awards.models import Award, AwardYear
from people.models import OrgPerson
from voting.services.eligibility import person_may_vote_on_award


class DivisionGatingTests(TestCase):
    def setUp(self):
        self.year = AwardYear.objects.create(year=2026, title='Y', slug='2026')
        self.tourism_award = Award.objects.create(
            year=self.year,
            slug='t',
            name='T',
            division=Award.Division.TOURISM,
            voting_mode=Award.VotingMode.WEIGHTED,
        )
        self.global_award = Award.objects.create(
            year=self.year,
            slug='g',
            name='G',
            division=Award.Division.GLOBAL,
            voting_mode=Award.VotingMode.WEIGHTED,
        )
        self.shared_award = Award.objects.create(
            year=self.year,
            slug='s',
            name='S',
            division=Award.Division.SHARED,
            voting_mode=Award.VotingMode.STAFF_SHORTLIST,
        )

    def _p(self, eid, **kwargs):
        defaults = {
            'email': f'e{eid}@x.com',
            'first_name': 'A',
            'last_name': 'B',
            'is_active': True,
            'role_code': 'STAFF',
            'department_code': 'HR',
            'company': 'global',
            'electorate': 'staff',
            'is_nigeria_eligible': True,
        }
        defaults.update(kwargs)
        return OrgPerson.objects.create(external_id=eid, **defaults)

    def test_tourism_voter(self):
        p = self._p(1, company='tourism', department_code='TOURISM')
        self.assertTrue(person_may_vote_on_award(p, self.tourism_award))
        self.assertFalse(person_may_vote_on_award(p, self.global_award))
        self.assertTrue(person_may_vote_on_award(p, self.shared_award))

    def test_global_voter(self):
        p = self._p(2, company='global')
        self.assertFalse(person_may_vote_on_award(p, self.tourism_award))
        self.assertTrue(person_may_vote_on_award(p, self.global_award))
        self.assertTrue(person_may_vote_on_award(p, self.shared_award))

    def test_dubai_and_ineligible_excluded(self):
        dubai = self._p(
            3,
            company='excluded',
            is_nigeria_eligible=False,
            department_code='TOURISM_DUBAI',
        )
        intern = self._p(4, electorate='ineligible', role_code='INTERN')
        for award in (self.tourism_award, self.global_award, self.shared_award):
            self.assertFalse(person_may_vote_on_award(dubai, award))
            self.assertFalse(person_may_vote_on_award(intern, award))

    def test_executive_votes_all_divisions(self):
        tourism_ed = self._p(
            5,
            company='tourism',
            department_code='TOURISM',
            role_code='ED',
            electorate='executive',
        )
        global_md = self._p(
            6,
            company='global',
            department_code='HR',
            role_code='MD',
            electorate='executive',
        )
        for award in (self.tourism_award, self.global_award, self.shared_award):
            self.assertTrue(person_may_vote_on_award(tourism_ed, award))
            self.assertTrue(person_may_vote_on_award(global_md, award))

    def test_ungated_leadership_open_to_all_staff(self):
        leadership_tourism = Award.objects.create(
            year=self.year,
            slug='excellent-leadership-award-tourism',
            name='Leadership Tourism',
            division=Award.Division.TOURISM,
            voting_mode=Award.VotingMode.WEIGHTED,
            company_vote_gated=False,
            executive_weight='0.20',
            staff_weight='0.80',
        )
        leadership_global = Award.objects.create(
            year=self.year,
            slug='excellent-leadership-award-global',
            name='Leadership Global',
            division=Award.Division.GLOBAL,
            voting_mode=Award.VotingMode.WEIGHTED,
            company_vote_gated=False,
            executive_weight='0.20',
            staff_weight='0.80',
        )
        tourism_staff = self._p(
            7, company='tourism', department_code='TOURISM'
        )
        global_staff = self._p(8, company='global')
        self.assertTrue(person_may_vote_on_award(tourism_staff, leadership_tourism))
        self.assertTrue(person_may_vote_on_award(tourism_staff, leadership_global))
        self.assertTrue(person_may_vote_on_award(global_staff, leadership_tourism))
        self.assertTrue(person_may_vote_on_award(global_staff, leadership_global))
        # Company-gated awards still respect division for staff.
        self.assertFalse(person_may_vote_on_award(tourism_staff, self.global_award))
        self.assertFalse(person_may_vote_on_award(global_staff, self.tourism_award))

    def test_ungated_department_open_to_all_staff(self):
        dept_tourism = Award.objects.create(
            year=self.year,
            slug='department-of-the-year-tourism',
            name='Department Tourism',
            division=Award.Division.TOURISM,
            voting_mode=Award.VotingMode.WEIGHTED,
            company_vote_gated=False,
            executive_weight='0.50',
            staff_weight='0.50',
        )
        dept_global = Award.objects.create(
            year=self.year,
            slug='department-of-the-year-global',
            name='Department Global',
            division=Award.Division.GLOBAL,
            voting_mode=Award.VotingMode.WEIGHTED,
            company_vote_gated=False,
            executive_weight='0.50',
            staff_weight='0.50',
        )
        tourism_staff = self._p(
            11, company='tourism', department_code='TOURISM'
        )
        global_staff = self._p(12, company='global')
        self.assertTrue(person_may_vote_on_award(tourism_staff, dept_tourism))
        self.assertTrue(person_may_vote_on_award(tourism_staff, dept_global))
        self.assertTrue(person_may_vote_on_award(global_staff, dept_tourism))
        self.assertTrue(person_may_vote_on_award(global_staff, dept_global))

    def test_company_gated_rookie_split(self):
        rookie_tourism = Award.objects.create(
            year=self.year,
            slug='rookie-of-the-year-tourism',
            name='Rookie Tourism',
            division=Award.Division.TOURISM,
            voting_mode=Award.VotingMode.STAFF_SHORTLIST,
        )
        rookie_global = Award.objects.create(
            year=self.year,
            slug='rookie-of-the-year-global',
            name='Rookie Global',
            division=Award.Division.GLOBAL,
            voting_mode=Award.VotingMode.STAFF_SHORTLIST,
        )
        tourism_staff = self._p(
            9, company='tourism', department_code='TOURISM'
        )
        global_staff = self._p(10, company='global')
        self.assertTrue(person_may_vote_on_award(tourism_staff, rookie_tourism))
        self.assertFalse(person_may_vote_on_award(tourism_staff, rookie_global))
        self.assertTrue(person_may_vote_on_award(global_staff, rookie_global))
        self.assertFalse(person_may_vote_on_award(global_staff, rookie_tourism))
