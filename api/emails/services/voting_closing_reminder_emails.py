"""Reminder email before voting closes (unsubmitted ballots only)."""

from __future__ import annotations

import logging
from typing import Any, Optional

from django.utils import timezone

from awards.models import AwardNotificationConfig, AwardYear
from emails.config import EmailConfig
from emails.formatting import format_email_datetime
from emails.services.base import BaseEmailService
from emails.services.vote_invite_emails import ballot_vote_url, frontend_base_url
from voting.models import BallotToken
from voting.services.eligibility import awards_for_voter

logger = logging.getLogger(__name__)

VOTING_CLOSING_REMINDER_TEMPLATE = 'emails/voting_closing_reminder.html'
EVENT = AwardNotificationConfig.Event.VOTING_CLOSING_REMINDER


def minutes_until_close(year: AwardYear, *, now=None) -> int | None:
    now = now or timezone.now()
    closes = year.voting_closes_at
    if closes is None:
        return None
    delta = closes - now
    return max(0, int(delta.total_seconds() // 60))


def build_voting_closing_reminder_context(
    token: BallotToken,
    *,
    recipient_override: Optional[str] = None,
) -> dict[str, Any]:
    person = token.person
    year = token.year
    awards = awards_for_voter(person, year)
    company_label = person.get_company_display() if person.company else ''
    mins = minutes_until_close(year)
    return {
        'first_name': person.first_name or 'Colleague',
        'full_name': person.display_name,
        'email': recipient_override or person.email,
        'year': year.year,
        'year_title': year.title,
        'voting_closes_at': year.voting_closes_at,
        'voting_closes_formatted': format_email_datetime(year.voting_closes_at),
        'minutes_remaining': mins,
        'minutes_remaining_label': (
            f'{mins} minute{"s" if mins != 1 else ""}'
            if mins is not None
            else 'soon'
        ),
        'ballot_url': ballot_vote_url(token),
        'company_label': company_label,
        'award_count': len(awards),
        'sender_name': EmailConfig.get_sender_name(),
        'sender_email': EmailConfig.get_default_from_email(),
        'support_email': EmailConfig.get_default_from_email(),
        'frontend_url': frontend_base_url(),
    }


def resolve_subject(
    config: Optional[AwardNotificationConfig],
    year: AwardYear,
    *,
    minutes_remaining: int | None = None,
) -> str:
    template = (
        (config.subject_template if config else '')
        or 'Reminder: voting closes soon — Incel Employee Awards {year}'
    )
    try:
        return template.format(
            year=year.year,
            title=year.title,
            minutes=minutes_remaining if minutes_remaining is not None else '',
        )
    except (KeyError, ValueError):
        return template


def send_voting_closing_reminder_email(
    token: BallotToken,
    *,
    config: Optional[AwardNotificationConfig] = None,
    recipient_override: Optional[str] = None,
    is_async: bool = False,
) -> bool:
    """Remind an eligible voter who has not submitted yet."""
    try:
        year = token.year
        if config is None:
            config = AwardNotificationConfig.objects.filter(
                year=year,
                event=EVENT,
            ).first()

        context = build_voting_closing_reminder_context(
            token, recipient_override=recipient_override
        )
        subject = resolve_subject(
            config,
            year,
            minutes_remaining=context.get('minutes_remaining'),
        )
        recipient = recipient_override or token.person.email
        return BaseEmailService.send_email(
            subject=subject,
            recipients=[recipient],
            template_name=VOTING_CLOSING_REMINDER_TEMPLATE,
            context=context,
            reply_to=EmailConfig.get_default_from_email(),
            is_async=is_async,
        )
    except Exception as exc:
        logger.exception(
            'Failed to prepare voting closing reminder for token %s: %s',
            token.pk,
            exc,
        )
        return False
