import logging
from typing import Any, Dict, Optional

from django.conf import settings
from django.utils import timezone
from django.utils.formats import date_format

from awards.models import AwardNotificationConfig, AwardYear
from emails.config import EmailConfig
from emails.services.base import BaseEmailService
from voting.models import BallotToken
from voting.services.eligibility import awards_for_voter

logger = logging.getLogger(__name__)

ELIGIBILITY_NOTICE_TEMPLATE = 'emails/eligibility_notice.html'
EVENT = AwardNotificationConfig.Event.ELIGIBILITY_NOTICE


def frontend_base_url() -> str:
    base = getattr(settings, 'FRONTEND_BASE_URL', '') or 'http://localhost:3000'
    return base.rstrip('/')


def year_hub_url(year: AwardYear) -> str:
    return f'{frontend_base_url()}/{year.year}'


def _format_dt(value) -> str:
    if value is None:
        return 'TBD'
    local = timezone.localtime(value) if timezone.is_aware(value) else value
    return date_format(local, 'DATETIME_FORMAT')


def build_eligibility_notice_context(
    token: BallotToken,
    *,
    recipient_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Template context: eligible categories only — never nominee names."""
    person = token.person
    year: AwardYear = token.year
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
        'year_url': year_hub_url(year),
        'company_label': company_label,
        'award_names': [a.name for a in awards],
        'award_count': len(awards),
        'sender_name': EmailConfig.get_sender_name(),
        'sender_email': EmailConfig.get_default_from_email(),
        'support_email': EmailConfig.get_default_from_email(),
        'frontend_url': frontend_base_url(),
    }


def resolve_subject(config: Optional[AwardNotificationConfig], year: AwardYear) -> str:
    template = (
        (config.subject_template if config else '')
        or "You're eligible to vote — Incel Employee Awards {year}"
    )
    try:
        return template.format(year=year.year, title=year.title)
    except (KeyError, ValueError):
        return template


def send_eligibility_notice_email(
    token: BallotToken,
    *,
    config: Optional[AwardNotificationConfig] = None,
    recipient_override: Optional[str] = None,
    is_async: bool = False,
) -> bool:
    """
    Confirm eligibility for the upcoming awards season.

    Lists award categories the voter will see — never nominees.
    Does not include a personal ballot token link.
    """
    try:
        year = token.year
        if config is None:
            config = AwardNotificationConfig.objects.filter(
                year=year,
                event=EVENT,
            ).first()

        context = build_eligibility_notice_context(
            token, recipient_override=recipient_override
        )
        subject = resolve_subject(config, year)
        recipient = recipient_override or token.person.email
        reply_to = EmailConfig.get_default_from_email()

        return BaseEmailService.send_email(
            subject=subject,
            recipients=[recipient],
            template_name=ELIGIBILITY_NOTICE_TEMPLATE,
            context=context,
            reply_to=reply_to,
            is_async=is_async,
        )
    except Exception as exc:
        logger.exception(
            'Failed to prepare eligibility notice for token %s: %s', token.pk, exc
        )
        return False
