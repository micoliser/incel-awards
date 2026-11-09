from django.core.management.base import BaseCommand, CommandError

from people.services.org_client import OrgUsersAPIError
from people.services.sync import sync_org_people


class Command(BaseCommand):
    help = 'Fetch org directory users and upsert local OrgPerson rows.'

    def handle(self, *args, **options):
        try:
            stats = sync_org_people()
        except OrgUsersAPIError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f'Sync complete: fetched={stats.fetched} kept={stats.kept} '
                f'filtered_out={stats.filtered_out} '
                f'created={stats.created} updated={stats.updated} '
                f'deactivated={stats.deactivated}'
            )
        )
