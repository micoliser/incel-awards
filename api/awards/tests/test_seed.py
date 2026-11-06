from django.test import TestCase

from awards.models import Award, AwardNotificationConfig, AwardYear, Nominee
from awards.seed.year_2026 import AWARDS, YEAR, seed_year_2026


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

    def test_notification_config_defaults(self):
        year = seed_year_2026()
        config = AwardNotificationConfig.objects.get(
            year=year,
            event=AwardNotificationConfig.Event.VOTE_INVITE,
        )
        self.assertTrue(config.enabled)
        self.assertEqual(config.audience, AwardNotificationConfig.Audience.ALL_ELIGIBLE)
        self.assertEqual(config.offset_minutes_before_open, 60)
        self.assertEqual(config.channel, AwardNotificationConfig.Channel.EMAIL)

    def test_idempotent_reseed(self):
        seed_year_2026()
        seed_year_2026()
        self.assertEqual(AwardYear.objects.filter(year=YEAR).count(), 1)
        self.assertEqual(Award.objects.filter(year__year=YEAR).count(), 14)

    def test_rookie_nominees_confirmed(self):
        year = seed_year_2026()
        rookie = Award.objects.get(year=year, slug='rookie-of-the-year')
        nominees = list(Nominee.objects.filter(award=rookie).order_by('sort_order'))
        self.assertEqual(len(nominees), 4)
        self.assertTrue(all(n.is_confirmed for n in nominees))
        names = [n.display_name for n in nominees]
        self.assertEqual(
            names,
            ['Ayoola Adegoke', 'James Obande', 'Tobi', 'Peterson Paul'],
        )

    def test_employees_choice_has_no_criteria(self):
        year = seed_year_2026()
        award = Award.objects.get(year=year, slug='employees-choice-of-the-year')
        self.assertEqual(award.criteria.count(), 0)
        self.assertEqual(award.nominees.count(), 0)
