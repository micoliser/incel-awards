"""Idempotent notification dispatch driven by AwardNotificationConfig."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from django.db.models import Q, QuerySet
from django.utils import timezone

from awards.models import AwardNotificationConfig, AwardYear
from emails.config import EmailConfig
from emails.services.eligibility_notice_emails import (
    EVENT as ELIGIBILITY_NOTICE_EVENT,
)
from emails.services.eligibility_notice_emails import send_eligibility_notice_email
from emails.services.vote_invite_emails import EVENT as VOTE_INVITE_EVENT
from emails.services.vote_invite_emails import send_vote_invite_email
from people.models import OrgPerson
from voting.models import BallotInviteDelivery, BallotToken

logger = logging.getLogger(__name__)

SendFn = Callable[..., bool]


@dataclass
class DispatchStats:
    sent: int = 0
    failed: int = 0
    skipped_already_sent: int = 0
    skipped_timing: int = 0
    skipped_disabled: int = 0
    skipped_revoked: int = 0
    skipped_email_off: int = 0
    audience_total: int = 0
    exited_early: str = ''
    event: str = ''


def _audience_filter(audience: str) -> Q:
    """Map AwardNotificationConfig.audience to BallotToken person filters."""
    base = Q(
        person__is_active=True,
        person__is_nigeria_eligible=True,
        person__electorate__in=(
            OrgPerson.Electorate.STAFF,
            OrgPerson.Electorate.EXECUTIVE,
        ),
    )
    if audience == AwardNotificationConfig.Audience.ALL_ELIGIBLE:
        return base
    if audience == AwardNotificationConfig.Audience.STAFF_ONLY:
        return base & Q(person__electorate=OrgPerson.Electorate.STAFF)
    if audience == AwardNotificationConfig.Audience.EXECUTIVES_ONLY:
        return base & Q(person__electorate=OrgPerson.Electorate.EXECUTIVE)
    if audience == AwardNotificationConfig.Audience.TOURISM_ONLY:
        return base & Q(person__company=OrgPerson.Company.TOURISM)
    if audience == AwardNotificationConfig.Audience.GLOBAL_ONLY:
        return base & Q(person__company=OrgPerson.Company.GLOBAL)
    return base


def tokens_for_audience(year: AwardYear, audience: str) -> QuerySet[BallotToken]:
    return (
        BallotToken.objects.filter(year=year)
        .filter(_audience_filter(audience))
        .filter(revoked_at__isnull=True)
        .select_related('person', 'year')
        .order_by('id')
    )


def earliest_send_at(
    year: AwardYear, config: AwardNotificationConfig
):
    if year.voting_opens_at is None:
        return None
    return year.voting_opens_at - timedelta(
        minutes=config.offset_minutes_before_open
    )


def _record_delivery(
    token: BallotToken,
    *,
    event: str,
    status: str,
    error_message: str = '',
) -> BallotInviteDelivery:
    delivery, _ = BallotInviteDelivery.objects.update_or_create(
        token=token,
        event=event,
        defaults={
            'sent_at': timezone.now(),
            'status': status,
            'error_message': error_message[:2000] if error_message else '',
        },
    )
    return delivery


def dispatch_notification(
    year: AwardYear | int,
    *,
    event: str,
    send_fn: SendFn,
    force: bool = False,
) -> DispatchStats:
    """
    Send one notification event for tokens that lack a successful delivery row.

    Timing gate: now >= voting_opens_at - offset_minutes_before_open
    (bypassed with force=True). Prefer sync send for reliability.
    """
    stats = DispatchStats(event=event)

    if isinstance(year, int):
        year = AwardYear.objects.get(year=year)

    config = AwardNotificationConfig.objects.filter(
        year=year,
        event=event,
    ).first()

    if config is None:
        stats.exited_early = 'no_config'
        logger.info('No %s AwardNotificationConfig for year %s', event, year.year)
        return stats

    if not config.enabled:
        stats.exited_early = 'disabled'
        stats.skipped_disabled = 1
        logger.info('%s config disabled for year %s — exiting', event, year.year)
        return stats

    if not force:
        gate = earliest_send_at(year, config)
        if gate is None:
            stats.exited_early = 'no_voting_opens_at'
            logger.info(
                'AwardYear %s has no voting_opens_at — cannot schedule %s '
                '(use --force to override)',
                year.year,
                event,
            )
            return stats
        now = timezone.now()
        if now < gate:
            stats.exited_early = 'too_early'
            stats.skipped_timing = 1
            logger.info(
                'Too early to dispatch %s for %s '
                '(now=%s, earliest=%s, opens=%s, offset=%sm)',
                event,
                year.year,
                now.isoformat(),
                gate.isoformat(),
                year.voting_opens_at.isoformat(),
                config.offset_minutes_before_open,
            )
            return stats

    if not EmailConfig.is_enabled():
        tokens = list(tokens_for_audience(year, config.audience))
        stats.audience_total = len(tokens)
        stats.exited_early = 'email_disabled'
        stats.skipped_email_off = len(tokens)
        logger.info(
            'EMAIL_ENABLED=False — would dispatch %s %s emails for %s',
            len(tokens),
            event,
            year.year,
        )
        if tokens:
            send_fn(tokens[0], config=config, is_async=False)
        return stats

    tokens = list(tokens_for_audience(year, config.audience))
    stats.audience_total = len(tokens)

    already_sent = set(
        BallotInviteDelivery.objects.filter(
            token__year=year,
            event=event,
            status=BallotInviteDelivery.Status.SENT,
        ).values_list('token_id', flat=True)
    )

    for token in tokens:
        if token.pk in already_sent:
            stats.skipped_already_sent += 1
            continue
        if token.is_revoked:
            stats.skipped_revoked += 1
            continue

        ok = send_fn(token, config=config, is_async=False)
        if ok:
            _record_delivery(
                token,
                event=event,
                status=BallotInviteDelivery.Status.SENT,
            )
            stats.sent += 1
        else:
            _record_delivery(
                token,
                event=event,
                status=BallotInviteDelivery.Status.FAILED,
                error_message=f'{send_fn.__name__} returned False',
            )
            stats.failed += 1

    return stats


def dispatch_vote_invites(
    year: AwardYear | int,
    *,
    force: bool = False,
) -> DispatchStats:
    return dispatch_notification(
        year,
        event=VOTE_INVITE_EVENT,
        send_fn=send_vote_invite_email,
        force=force,
    )


def dispatch_eligibility_notices(
    year: AwardYear | int,
    *,
    force: bool = False,
) -> DispatchStats:
    return dispatch_notification(
        year,
        event=ELIGIBILITY_NOTICE_EVENT,
        send_fn=send_eligibility_notice_email,
        force=force,
    )
