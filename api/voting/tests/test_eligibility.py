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
