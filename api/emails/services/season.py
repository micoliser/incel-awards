"""
Season automation: sync roster → ballot tokens → emails → status ticks.

Used by Celery beat (and optionally management commands). Safe to run frequently;
notification dispatch and token generation are idempotent.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from awards.models import AwardYear
from emails.services.dispatch import (
    dispatch_eligibility_notices,
    dispatch_vote_invites,
)
from people.services.org_client import OrgUsersAPIError
from people.services.sync import SyncStats, sync_org_people
from voting.services.tokens import TokenGenStats, generate_ballot_tokens

logger = logging.getLogger(__name__)


@dataclass
class SeasonTickStats:
    sync: dict | None = None
    sync_error: str = ''
    tokens: list[dict] = field(default_factory=list)
    eligibility_notices: list[dict] = field(default_factory=list)
    invites: list[dict] = field(default_factory=list)
    status_changes: list[str] = field(default_factory=list)


def _years_for_token_gen():
    """Years that may need ballot tokens (upcoming, open, or just closed)."""
    now = timezone.now()
    return AwardYear.objects.filter(
        Q(status__in=(
            AwardYear.Status.SCHEDULED,
            AwardYear.Status.VOTING,
        ))
        | Q(
            voting_closes_at__isnull=False,
            voting_closes_at__gte=now - timedelta(days=2),
        )
    ).distinct()


def _years_for_notifications():
    return AwardYear.objects.filter(
        status__in=(
            AwardYear.Status.DRAFT,
            AwardYear.Status.SCHEDULED,
            AwardYear.Status.VOTING,
        ),
        voting_opens_at__isnull=False,
    )


def sync_roster() -> SyncStats:
    return sync_org_people()


def generate_tokens_for_active_years() -> list[tuple[int, TokenGenStats]]:
    results = []
    for year in _years_for_token_gen():
        stats = generate_ballot_tokens(year)
        results.append((year.year, stats))
        logger.info(
            'ballot tokens year=%s eligible=%s created=%s skipped=%s',
            year.year,
            stats.eligible,
            stats.created,
            stats.skipped_existing,
        )
    return results


def dispatch_eligibility_for_active_years(
    *, force: bool = False
) -> list[tuple[int, dict]]:
    results = []
    for year in _years_for_notifications():
        stats = dispatch_eligibility_notices(year, force=force)
        results.append((year.year, asdict(stats)))
        logger.info(
            'dispatch eligibility year=%s sent=%s failed=%s skipped_already=%s exited=%s',
            year.year,
            stats.sent,
            stats.failed,
            stats.skipped_already_sent,
            stats.exited_early,
        )
    return results


def dispatch_invites_for_active_years(*, force: bool = False) -> list[tuple[int, dict]]:
    results = []
    for year in _years_for_notifications():
        stats = dispatch_vote_invites(year, force=force)
        results.append((year.year, asdict(stats)))
        logger.info(
            'dispatch invites year=%s sent=%s failed=%s skipped_already=%s exited=%s',
            year.year,
            stats.sent,
            stats.failed,
            stats.skipped_already_sent,
            stats.exited_early,
        )
    return results


def advance_year_statuses() -> list[str]:
    """Flip scheduled→voting and voting→closed from voting window timestamps."""
    now = timezone.now()
    changes: list[str] = []

    for year in AwardYear.objects.filter(status=AwardYear.Status.SCHEDULED):
        opens = year.voting_opens_at
        if opens is not None and now >= opens:
            closes = year.voting_closes_at
            if closes is not None and now >= closes:
                year.status = AwardYear.Status.CLOSED
            else:
                year.status = AwardYear.Status.VOTING
            year.save(update_fields=['status'])
            changes.append(f'{year.year}:{year.status}')
            logger.info('AwardYear %s status → %s', year.year, year.status)

    for year in AwardYear.objects.filter(status=AwardYear.Status.VOTING):
        closes = year.voting_closes_at
        if closes is not None and now >= closes:
            year.status = AwardYear.Status.CLOSED
            year.save(update_fields=['status'])
            changes.append(f'{year.year}:closed')
            logger.info('AwardYear %s status → closed', year.year)

    return changes


def run_season_tick(*, force_invites: bool = False) -> SeasonTickStats:
    """
    Full automation tick:
    1. Sync org people from ORG_USERS_API_*
    2. Generate missing ballot tokens
    3. Dispatch due eligibility notices (categories only)
    4. Dispatch due vote invites (ballot links)
    5. Advance year status from open/close timestamps
    """
    out = SeasonTickStats()

    try:
        sync_stats = sync_roster()
        out.sync = asdict(sync_stats)
        logger.info(
            'org sync fetched=%s created=%s updated=%s deactivated=%s',
            sync_stats.fetched,
            sync_stats.created,
            sync_stats.updated,
            sync_stats.deactivated,
        )
    except OrgUsersAPIError as exc:
        out.sync_error = str(exc)
        logger.exception('org sync failed: %s', exc)
    except Exception as exc:  # noqa: BLE001 — tick must continue if sync fails mid-season
        out.sync_error = str(exc)
        logger.exception('org sync failed: %s', exc)

    for year_num, stats in generate_tokens_for_active_years():
        out.tokens.append({
            'year': year_num,
            'eligible': stats.eligible,
            'created': stats.created,
            'skipped_existing': stats.skipped_existing,
        })

    for year_num, stats in dispatch_eligibility_for_active_years(force=force_invites):
        out.eligibility_notices.append({'year': year_num, **stats})

    for year_num, stats in dispatch_invites_for_active_years(force=force_invites):
        out.invites.append({'year': year_num, **stats})

    out.status_changes = advance_year_statuses()
    return out
