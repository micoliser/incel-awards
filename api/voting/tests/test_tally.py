"""
Weighted tally unit tests from PDF scenarios (domain-rules §5).

Uses E=2 eligible executives and synthetic staff vote distributions.
"""

from decimal import Decimal

from django.test import TestCase

from awards.models import Award, AwardYear, Nominee
from people.models import OrgPerson
from voting.models import Vote
from voting.services.tally import tally_award


def _person(external_id, *, company, electorate='staff', **kwargs):
    defaults = {
        'email': f'p{external_id}@incelgroup.com',
        'first_name': f'P{external_id}',
        'last_name': 'Test',
        'is_active': True,
        'role_code': 'ED' if electorate == 'executive' else 'STAFF',
        'department_code': 'TOURISM' if company == 'tourism' else 'HR',
        'company': company,
        'electorate': electorate,
        'is_nigeria_eligible': True,
    }
    defaults.update(kwargs)
    return OrgPerson.objects.create(external_id=external_id, **defaults)


def _cast(award, voter, nominee):
    return Vote.objects.create(
        award=award,
        voter=voter,
        nominee=nominee,
        electorate_at_vote=voter.electorate,
    )


class WeightedTallyPDFScenariosTests(TestCase):
    def setUp(self):
        self.year = AwardYear.objects.create(
            year=2026,
            title='Employee Awards 2026',
            slug='2026',
            status=AwardYear.Status.VOTING,
        )
        # E=2 tourism executives (eligible for tourism awards)
        self.exec1 = _person(1, company='tourism', electorate='executive')
        self.exec2 = _person(2, company='tourism', electorate='executive')

    def _make_weighted_award(self, slug, exec_w, staff_w, nominee_names):
        award = Award.objects.create(
            year=self.year,
            slug=slug,
            name=slug,
            division=Award.Division.TOURISM,
            voting_mode=Award.VotingMode.WEIGHTED,
            executive_weight=Decimal(str(exec_w)),
            staff_weight=Decimal(str(staff_w)),
            sort_order=1,
        )
        nominees = [
            Nominee.objects.create(
                award=award,
                display_name=name,
                nominee_type=Nominee.NomineeType.PERSON,
                is_confirmed=True,
                sort_order=i,
            )
            for i, name in enumerate(nominee_names)
        ]
        return award, nominees

    def _staff_voters(self, n, start_id=100):
        return [
            _person(start_id + i, company='tourism', electorate='staff')
            for i in range(n)
        ]

    def test_employee_30_70_scenario(self):
        """
        Employee of the Year (30% exec / 70% staff), E=2.
        A: both execs + 70/100 staff → 0.30 + 0.49 = 0.79
        B: 20 staff → 0.14
        C: 10 staff → 0.07
        """
        award, (a, b, c) = self._make_weighted_award(
            'employee-tourism',
            0.30,
            0.70,
            ['Mercy', 'Michael', 'Benjamin'],
        )
        staff = self._staff_voters(100)

        _cast(award, self.exec1, a)
        _cast(award, self.exec2, a)
        for voter in staff[:70]:
            _cast(award, voter, a)
        for voter in staff[70:90]:
            _cast(award, voter, b)
        for voter in staff[90:]:
            _cast(award, voter, c)

        result = tally_award(award)
        self.assertEqual(result.eligible_exec_count, 2)

        by_name = {row.display_name: row for row in result.nominees}
        self.assertEqual(by_name['Mercy'].score, Decimal('0.79'))
        self.assertEqual(by_name['Michael'].score, Decimal('0.14'))
        self.assertEqual(by_name['Benjamin'].score, Decimal('0.07'))
        self.assertEqual(result.winners[0].display_name, 'Mercy')
        self.assertFalse(result.winners[0].is_tie)

    def test_supervisor_60_40_scenario(self):
        """
        Supervisor (60/40), E=2.
        A: 1 exec + 60/100 staff → 0.30 + 0.24 = 0.54
        B: 1 exec + 40/100 staff → 0.30 + 0.16 = 0.46
        """
        award, (a, b, *_rest) = self._make_weighted_award(
            'supervisor-tourism',
            0.60,
            0.40,
            ['Marcathy', 'Ayoola', 'Uche', 'Solomon'],
        )
        staff = self._staff_voters(100)

        _cast(award, self.exec1, a)
        _cast(award, self.exec2, b)
        for voter in staff[:60]:
            _cast(award, voter, a)
        for voter in staff[60:]:
            _cast(award, voter, b)

        result = tally_award(award)
        by_name = {row.display_name: row for row in result.nominees}
        self.assertEqual(by_name['Marcathy'].score, Decimal('0.54'))
        self.assertEqual(by_name['Ayoola'].score, Decimal('0.46'))
        self.assertEqual(result.winners[0].display_name, 'Marcathy')

    def test_department_50_50_scenario(self):
        """
        Department (50/50), E=2.
        A: both execs + 50/100 staff → 0.50 + 0.25 = 0.75
        B: 50 staff → 0.25
        """
        award, (a, b, *_rest) = self._make_weighted_award(
            'department-tourism',
            0.50,
            0.50,
            ['Operations', 'Sales', 'Brands', 'IC', 'Accounts'],
        )
        # department nominee type
        for n in Nominee.objects.filter(award=award):
            n.nominee_type = Nominee.NomineeType.DEPARTMENT
            n.save(update_fields=['nominee_type'])

        staff = self._staff_voters(100)
        _cast(award, self.exec1, a)
        _cast(award, self.exec2, a)
        for voter in staff[:50]:
            _cast(award, voter, a)
        for voter in staff[50:]:
            _cast(award, voter, b)

        result = tally_award(award)
        by_name = {row.display_name: row for row in result.nominees}
        self.assertEqual(by_name['Operations'].score, Decimal('0.75'))
        self.assertEqual(by_name['Sales'].score, Decimal('0.25'))
        self.assertEqual(result.winners[0].display_name, 'Operations')

    def test_eligible_exec_count_not_hardcoded(self):
        """Adding a third tourism exec changes E and per-vote value."""
        _person(3, company='tourism', electorate='executive')
        award, (a, b) = self._make_weighted_award(
            'employee-e3',
            0.30,
            0.70,
            ['A', 'B'],
        )
        # Only one exec votes for A; staff none
        _cast(award, self.exec1, a)
        result = tally_award(award)
        self.assertEqual(result.eligible_exec_count, 3)
        # exec_vote_value = 0.30/3 = 0.10
        by_name = {row.display_name: row for row in result.nominees}
        self.assertEqual(by_name['A'].score, Decimal('0.1'))


class WeightedTallyEdgeCaseTests(TestCase):
    def setUp(self):
        self.year = AwardYear.objects.create(
            year=2026,
            title='Employee Awards 2026',
            slug='2026',
            status=AwardYear.Status.VOTING,
        )
        self.exec1 = _person(1, company='tourism', electorate='executive')
        self.exec2 = _person(2, company='tourism', electorate='executive')

    def test_zero_staff_votes_exec_only(self):
        """Staff share is 0 when no staff votes; exec-only determines score."""
        award = Award.objects.create(
            year=self.year,
            slug='employee-exec-only',
            name='Employee',
            division=Award.Division.TOURISM,
            voting_mode=Award.VotingMode.WEIGHTED,
            executive_weight=Decimal('0.30'),
            staff_weight=Decimal('0.70'),
        )
        a = Nominee.objects.create(award=award, display_name='A', is_confirmed=True)
        Nominee.objects.create(award=award, display_name='B', is_confirmed=True)

        _cast(award, self.exec1, a)
        _cast(award, self.exec2, a)

        result = tally_award(award)
        by_name = {row.display_name: row for row in result.nominees}
        # E=2 → each exec vote 0.15; both for A → 0.30; staff share 0
        self.assertEqual(by_name['A'].score, Decimal('0.30'))
        self.assertEqual(by_name['A'].staff_votes, 0)
        self.assertEqual(by_name['B'].score, Decimal('0'))
        self.assertEqual(result.winners[0].display_name, 'A')
        self.assertFalse(result.winners[0].is_tie)

    def test_weighted_tie_break_more_exec_votes(self):
        """Equal score: nominee with more exec votes wins."""
        award = Award.objects.create(
            year=self.year,
            slug='employee-tie-exec',
            name='Employee',
            division=Award.Division.TOURISM,
            voting_mode=Award.VotingMode.WEIGHTED,
            executive_weight=Decimal('0.50'),
            staff_weight=Decimal('0.50'),
        )
        a = Nominee.objects.create(award=award, display_name='A', is_confirmed=True)
        b = Nominee.objects.create(award=award, display_name='B', is_confirmed=True)
        c = Nominee.objects.create(award=award, display_name='C', is_confirmed=True)
        staff = [
            _person(100 + i, company='tourism', electorate='staff')
            for i in range(2)
        ]
        # A: 1 exec → 0.25; B: 1/2 staff → 0.25; C takes other staff vote
        # Tie-break → A wins on more exec votes
        _cast(award, self.exec1, a)
        _cast(award, staff[0], b)
        _cast(award, staff[1], c)

        result = tally_award(award)
        by_name = {row.display_name: row for row in result.nominees}
        self.assertEqual(by_name['A'].score, Decimal('0.25'))
        self.assertEqual(by_name['B'].score, Decimal('0.25'))
        self.assertEqual(len(result.winners), 1)
        self.assertEqual(result.winners[0].display_name, 'A')
        self.assertFalse(result.winners[0].is_tie)

    def test_weighted_true_tie_when_exec_and_staff_equal(self):
        """Equal score + equal exec/staff vote counts → marked as tie."""
        award = Award.objects.create(
            year=self.year,
            slug='employee-true-tie',
            name='Employee',
            division=Award.Division.TOURISM,
            voting_mode=Award.VotingMode.WEIGHTED,
            executive_weight=Decimal('0.50'),
            staff_weight=Decimal('0.50'),
        )
        a = Nominee.objects.create(award=award, display_name='A', is_confirmed=True)
        b = Nominee.objects.create(award=award, display_name='B', is_confirmed=True)
        # Each gets one exec vote → both score 0.25; exec_votes=1, staff=0
        _cast(award, self.exec1, a)
        _cast(award, self.exec2, b)

        result = tally_award(award)
        self.assertEqual(len(result.winners), 2)
        self.assertTrue(all(w.is_tie for w in result.winners))
        self.assertEqual({w.display_name for w in result.winners}, {'A', 'B'})


class SimpleTallyTests(TestCase):
    def test_shortlist_highest_count_wins(self):
        year = AwardYear.objects.create(year=2026, title='Y', slug='2026')
        award = Award.objects.create(
            year=year,
            slug='rookie',
            name='Rookie',
            division=Award.Division.SHARED,
            voting_mode=Award.VotingMode.STAFF_SHORTLIST,
        )
        a = Nominee.objects.create(award=award, display_name='A', is_confirmed=True)
        b = Nominee.objects.create(award=award, display_name='B', is_confirmed=True)
        v1 = _person(1, company='global')
        v2 = _person(2, company='tourism')
        v3 = _person(3, company='global')
        _cast(award, v1, a)
        _cast(award, v2, a)
        _cast(award, v3, b)

        result = tally_award(award)
        self.assertEqual(result.winners[0].display_name, 'A')
        self.assertEqual(result.winners[0].total_votes, 2)

    def test_shortlist_tie(self):
        year = AwardYear.objects.create(year=2026, title='Y', slug='2026')
        award = Award.objects.create(
            year=year,
            slug='rookie-tie',
            name='Rookie',
            division=Award.Division.SHARED,
            voting_mode=Award.VotingMode.STAFF_SHORTLIST,
        )
        a = Nominee.objects.create(award=award, display_name='A', is_confirmed=True)
        b = Nominee.objects.create(award=award, display_name='B', is_confirmed=True)
        v1 = _person(1, company='global')
        v2 = _person(2, company='tourism')
        _cast(award, v1, a)
        _cast(award, v2, b)

        result = tally_award(award)
        self.assertEqual(len(result.winners), 2)
        self.assertTrue(all(w.is_tie for w in result.winners))

