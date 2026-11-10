from decimal import Decimal

from django.test import TestCase

from awards.models import Award, AwardNotificationConfig, AwardYear, Nominee
from awards.seed import AWARDS, YEAR, seed_year_2026


class SeedYear2026Tests(TestCase):
    def test_seed_creates_expected_awards(self):
        year = seed_year_2026()
        self.assertEqual(year.year, YEAR)
        self.assertEqual(Award.objects.filter(year=year).count(), 14)
        self.assertEqual(Award.objects.filter(year=year).count(), len(AWARDS))

        weighted = Award.objects.filter(
            year=year,
            voting_mode=Award.VotingMode.WEIGHTED,
        ).count()
        shortlist = Award.objects.filter(
            year=year,
            voting_mode=Award.VotingMode.STAFF_SHORTLIST,
        ).count()
        open_awards = Award.objects.filter(
            year=year,
            voting_mode=Award.VotingMode.STAFF_OPEN,
        ).count()
        self.assertEqual(weighted, 6)
        self.assertEqual(shortlist, 6)
        self.assertEqual(open_awards, 2)

        self.assertFalse(
            Award.objects.filter(
                year=year,
                slug__in=(
                    'supervisor-of-the-year-tourism',
                    'supervisor-of-the-year-global',
                    'excellent-leadership-award',
                    'rookie-of-the-year',
                ),
            ).exists()
        )
        for slug in (
            'excellent-leadership-award-tourism',
            'excellent-leadership-award-global',
        ):
            leadership = Award.objects.get(year=year, slug=slug)
            self.assertFalse(leadership.company_vote_gated)
            self.assertEqual(leadership.voting_mode, Award.VotingMode.WEIGHTED)
            self.assertEqual(leadership.executive_weight, Decimal('0.20'))
            self.assertEqual(leadership.staff_weight, Decimal('0.80'))
            self.assertEqual(leadership.nominees.count(), 5)

        for slug in (
            'department-of-the-year-tourism',
            'department-of-the-year-global',
        ):
            department = Award.objects.get(year=year, slug=slug)
            self.assertFalse(department.company_vote_gated)
            self.assertEqual(department.voting_mode, Award.VotingMode.WEIGHTED)
            self.assertEqual(department.executive_weight, Decimal('0.50'))
            self.assertEqual(department.staff_weight, Decimal('0.50'))
            self.assertEqual(department.nominees.count(), 5)

    def test_notification_config_defaults(self):
        year = seed_year_2026()
        configs = AwardNotificationConfig.objects.filter(year=year)
        self.assertEqual(configs.count(), 5)
        self.assertEqual(
            set(configs.values_list('event', flat=True)),
            {
                AwardNotificationConfig.Event.ELIGIBILITY_NOTICE,
                AwardNotificationConfig.Event.VOTE_INVITE,
                AwardNotificationConfig.Event.VOTING_OPENED,
                AwardNotificationConfig.Event.VOTING_CLOSING_REMINDER,
                AwardNotificationConfig.Event.VOTING_CLOSED,
            },
        )
        invite = configs.get(event=AwardNotificationConfig.Event.VOTE_INVITE)
        self.assertTrue(invite.enabled)
        self.assertEqual(invite.audience, AwardNotificationConfig.Audience.ALL_ELIGIBLE)
        self.assertEqual(invite.offset_minutes_before_open, 60)
        self.assertEqual(invite.channel, AwardNotificationConfig.Channel.EMAIL)
        reminder = configs.get(
            event=AwardNotificationConfig.Event.VOTING_CLOSING_REMINDER,
        )
        self.assertEqual(reminder.offset_minutes_before_close, 60)

    def test_idempotent_reseed(self):
        seed_year_2026()
        seed_year_2026()
        self.assertEqual(AwardYear.objects.filter(year=YEAR).count(), 1)
        self.assertEqual(Award.objects.filter(year__year=YEAR).count(), 14)

    def test_rookie_nominees_confirmed(self):
        year = seed_year_2026()
        for slug in (
            'rookie-of-the-year-tourism',
            'rookie-of-the-year-global',
        ):
            rookie = Award.objects.get(year=year, slug=slug)
            self.assertTrue(rookie.company_vote_gated)
            self.assertEqual(rookie.voting_mode, Award.VotingMode.STAFF_SHORTLIST)
            nominees = list(
                Nominee.objects.filter(award=rookie).order_by('sort_order')
            )
            self.assertEqual(len(nominees), 4)
            self.assertTrue(all(n.is_confirmed for n in nominees))
            self.assertEqual(
                [n.display_name for n in nominees],
                [
                    n['display_name']
                    for n in next(a['nominees'] for a in AWARDS if a['slug'] == slug)
                ],
            )

    def test_employees_choice_has_no_criteria(self):
        year = seed_year_2026()
        award = Award.objects.get(year=year, slug='employees-choice-of-the-year')
        self.assertEqual(award.criteria.count(), 0)
        self.assertEqual(award.nominees.count(), 0)
        self.assertEqual(award.ideal_winner, '')

    def test_about_and_ideal_winner_seeded(self):
        year = seed_year_2026()
        employee = Award.objects.get(
            year=year, slug='employee-of-the-year-tourism'
        )
        self.assertIn('lifts the team around them', employee.description)
        self.assertEqual(
            employee.ideal_winner.splitlines(),
            [
                'Consistently delivers exceptional results',
                'Is reliable and dependable',
                'Collaborates well with the team',
                'Shows integrity and a good attitude to work',
            ],
        )
        leadership = Award.objects.get(
            year=year, slug='excellent-leadership-award-tourism'
        )
        self.assertIn('rather than seniority or designation', leadership.description)
        self.assertEqual(len(leadership.ideal_winner.splitlines()), 3)
        foodie = Award.objects.get(year=year, slug='foodie-of-the-year')
        self.assertTrue(foodie.description)
        self.assertEqual(foodie.ideal_winner, '')
