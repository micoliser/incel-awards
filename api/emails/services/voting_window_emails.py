"""Emails fired when a year transitions into or out of the voting window."""

from __future__ import annotations

import logging
from typing import Any, Optional

from django.utils import timezone
from django.utils.formats import date_format

from emails.config import EmailConfig
from emails.services.base import BaseEmailService
from emails.services.vote_invite_emails import ballot_vote_url, frontend_base_url
from voting.models import BallotToken
from voting.services.eligibility import awards_for_voter

logger = logging.getLogger(__name__)

VOTING_OPENED_TEMPLATE = 'emails/voting_opened.html'
VOTING_CLOSED_TEMPLATE = 'emails/voting_closed.html'
VOTING_OPENED_EVENT = 'voting_opened'
VOTING_CLOSED_EVENT = 'voting_closed'


def _format_dt(value) -> str:
    if value is None:
        return 'TBD'
    local = timezone.localtime(value) if timezone.is_aware(value) else value
    return date_format(local, 'DATETIME_FORMAT')


def _base_context(
    token: BallotToken,
    *,
    recipient_override: Optional[str] = None,
) -> dict[str, Any]:
    person = token.person
    year = token.year
    awards = awards_for_voter(person, year)
    company_label = person.get_company_display() if person.company else ''
    return {
        'first_name': person.first_name or 'Colleague',
        'full_name': person.display_name,
        'email': recipient_override or person.email,
        'year': year.year,
        'year_title': year.title,
        'voting_opens_at': year.voting_opens_at,
        'voting_closes_at': year.voting_closes_at,
        'voting_opens_formatted': _format_dt(year.voting_opens_at),
        'voting_closes_formatted': _format_dt(year.voting_closes_at),
        'ballot_url': ballot_vote_url(token),
        'results_url': f'{frontend_base_url()}/{year.year}/results',
        'company_label': company_label,
        'award_names': [a.name for a in awards],
        'award_count': len(awards),
        'sender_name': EmailConfig.get_sender_name(),
        'sender_email': EmailConfig.get_default_from_email(),
        'support_email': EmailConfig.get_default_from_email(),
        'frontend_url': frontend_base_url(),
    }


def send_voting_opened_email(
    token: BallotToken,
    *,
    config=None,  # unused; keeps dispatch_notification-compatible signature
    recipient_override: Optional[str] = None,
    is_async: bool = False,
) -> bool:
    """Notify that voting is open now, with personal ballot link."""
    try:
        context = _base_context(token, recipient_override=recipient_override)
        subject = f'Voting is open — {token.year.title}'
        recipient = recipient_override or token.person.email
        return BaseEmailService.send_email(
            subject=subject,
            recipients=[recipient],
            template_name=VOTING_OPENED_TEMPLATE,
            context=context,
            reply_to=EmailConfig.get_default_from_email(),
            is_async=is_async,
        )
    except Exception as exc:
        logger.exception(
            'Failed to prepare voting-opened email for token %s: %s',
            token.pk,
            exc,
        )
        return False


def send_voting_closed_email(
    token: BallotToken,
    *,
    config=None,
    recipient_override: Optional[str] = None,
    is_async: bool = False,
) -> bool:
    """Notify that the voting window has closed."""
    try:
        context = _base_context(token, recipient_override=recipient_override)
        subject = f'Voting has closed — {token.year.title}'
        recipient = recipient_override or token.person.email
        return BaseEmailService.send_email(
            subject=subject,
            recipients=[recipient],
            template_name=VOTING_CLOSED_TEMPLATE,
            context=context,
            reply_to=EmailConfig.get_default_from_email(),
            is_async=is_async,
        )
    except Exception as exc:
        logger.exception(
            'Failed to prepare voting-closed email for token %s: %s',
            token.pk,
            exc,
        )
        return False
