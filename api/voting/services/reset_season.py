"""
Wipe per-year voting/email state so a live test can be re-run cleanly.

Keeps awards, nominees, org people, and notification config rows.
Deletes votes, audit logs, and invite delivery records; unlocks ballots.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from awards.models import Award, AwardNotificationConfig, AwardYear
from awards.notification_defaults import ensure_default_notification_configs
from voting.models import BallotInviteDelivery, BallotToken, Vote, VoteAuditLog


@dataclass
class ResetSeasonStats:
    year: int
    votes_deleted: int = 0
    audit_logs_deleted: int = 0
    deliveries_deleted: int = 0
    tokens_unlocked: int = 0
    tokens_deleted: int = 0
    results_unpublished: bool = False
    preview_token_rotated: bool = False
    status: str = ''
    voting_opens_at: str | None = None
    voting_closes_at: str | None = None
    eligibility_offset_minutes: int | None = None
    invite_offset_minutes: int | None = None
    closing_reminder_offset_minutes: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@transaction.atomic
def reset_season_for_testing(
    year: AwardYear | int,
    *,
    opens_in_minutes: int | None = None,
    window_minutes: int = 30,
    eligibility_offset_minutes: int | None = None,
    invite_offset_minutes: int | None = None,
    closing_reminder_offset_minutes: int | None = None,
    delete_tokens: bool = False,
    rotate_preview_token: bool = False,
) -> ResetSeasonStats:
    """
    Reset voting + invite state for one award year.

    Intended for staging / production dry-runs. Does not delete awards,
    nominees, or OrgPerson rows.
    """
    if isinstance(year, int):
        year = AwardYear.objects.get(year=year)

    stats = ResetSeasonStats(year=year.year)
    award_ids = list(Award.objects.filter(year=year).values_list('id', flat=True))
    token_qs = BallotToken.objects.filter(year=year)

    stats.votes_deleted = Vote.objects.filter(award_id__in=award_ids).delete()[0]
    stats.audit_logs_deleted = VoteAuditLog.objects.filter(
        award_id__in=award_ids
    ).delete()[0]
    stats.deliveries_deleted = BallotInviteDelivery.objects.filter(
        token__year=year
    ).delete()[0]

    if delete_tokens:
        stats.tokens_deleted = token_qs.delete()[0]
    else:
        stats.tokens_unlocked = token_qs.update(
            submitted_at=None,
            revoked_at=None,
            last_accessed_at=None,
        )

    year.status = AwardYear.Status.SCHEDULED
    year.results_published_at = None
    stats.results_unpublished = True

    if opens_in_minutes is not None:
        if opens_in_minutes < 0:
            raise ValueError('opens_in_minutes must be >= 0')
        if window_minutes < 1:
            raise ValueError('window_minutes must be >= 1')
        opens = timezone.now() + timedelta(minutes=opens_in_minutes)
        closes = opens + timedelta(minutes=window_minutes)
        year.voting_opens_at = opens
        year.voting_closes_at = closes

    year.save()
    if rotate_preview_token:
        year.rotate_results_preview_token()
        stats.preview_token_rotated = True

    stats.status = year.status
    stats.voting_opens_at = (
        year.voting_opens_at.isoformat() if year.voting_opens_at else None
    )
    stats.voting_closes_at = (
        year.voting_closes_at.isoformat() if year.voting_closes_at else None
    )

    # Make sure all five season-email rows exist before applying offsets.
    ensure_default_notification_configs(year)

    if eligibility_offset_minutes is not None:
        AwardNotificationConfig.objects.filter(
            year=year,
            event=AwardNotificationConfig.Event.ELIGIBILITY_NOTICE,
        ).update(offset_minutes_before_open=eligibility_offset_minutes)
        stats.eligibility_offset_minutes = eligibility_offset_minutes

    if invite_offset_minutes is not None:
        AwardNotificationConfig.objects.filter(
            year=year,
            event=AwardNotificationConfig.Event.VOTE_INVITE,
        ).update(offset_minutes_before_open=invite_offset_minutes)
        stats.invite_offset_minutes = invite_offset_minutes

    if closing_reminder_offset_minutes is not None:
        AwardNotificationConfig.objects.filter(
            year=year,
            event=AwardNotificationConfig.Event.VOTING_CLOSING_REMINDER,
        ).update(offset_minutes_before_close=closing_reminder_offset_minutes)
        stats.closing_reminder_offset_minutes = closing_reminder_offset_minutes

    return stats
