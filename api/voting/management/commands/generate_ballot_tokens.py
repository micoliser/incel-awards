from django.core.management.base import BaseCommand, CommandError

from awards.models import AwardYear
from voting.services.tokens import generate_ballot_tokens


class Command(BaseCommand):
    help = 'Generate BallotToken rows for Nigeria-eligible staff/executives for a year.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            required=True,
            help='Award year (e.g. 2026)',
        )

    def handle(self, *args, **options):
        year_num = options['year']
        try:
            year = AwardYear.objects.get(year=year_num)
        except AwardYear.DoesNotExist as exc:
            raise CommandError(f'AwardYear {year_num} does not exist. Seed it first.') from exc

        stats = generate_ballot_tokens(year)
        self.stdout.write(
            self.style.SUCCESS(
                f'Tokens for {year_num}: eligible={stats.eligible} '
                f'created={stats.created} skipped_existing={stats.skipped_existing}'
            )
        )
