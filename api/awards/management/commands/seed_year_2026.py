from django.core.management.base import BaseCommand

from awards.models import Award
from awards.seed.year_2026 import AWARDS, seed_year_2026


class Command(BaseCommand):
    help = 'Idempotently seed AwardYear 2026, awards, criteria, nominees, and notification config.'

    def handle(self, *args, **options):
        year = seed_year_2026()
        award_count = Award.objects.filter(year=year).count()
        expected = len(AWARDS)
        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {year.title}: {award_count} awards '
                f'(expected {expected}).'
            )
        )
        if award_count != expected:
            self.stderr.write(
                self.style.WARNING(
                    f'Award count mismatch: got {award_count}, expected {expected}.'
                )
            )
