"""Confirmation email after a ballot is successfully submitted."""

from __future__ import annotations

import logging
from typing import Any, Optional

from django.utils import timezone
from django.utils.formats import date_format

from emails.config import EmailConfig
from emails.services.base import BaseEmailService
from emails.services.vote_invite_emails import frontend_base_url
from voting.models import BallotInviteDelivery, BallotToken

logger = logging.getLogger(__name__)

VOTE_CONFIRMATION_TEMPLATE = 'emails/vote_confirmation.html'
EVENT = 'vote_confirmation'


def _format_dt(value) -> str:
    if value is None:
        return 'just now'
    local = timezone.localtime(value) if timezone.is_aware(value) else value
    return date_format(local, 'DATETIME_FORMAT')


def build_vote_confirmation_context(
    token: BallotToken,
    *,
    award_count: int,
    recipient_override: Optional[str] = None,
) -> dict[str, Any]:
    person = token.person
    year = token.year
    company_label = person.get_company_display() if person.company else ''

    return {
        'first_name': person.first_name or 'Colleague',
        'full_name': person.display_name,
        'email': recipient_override or person.email,
        'year': year.year,
        'year_title': year.title,
        'submitted_at': token.submitted_at,
        'submitted_at_formatted': _format_dt(token.submitted_at),
        'voting_closes_at': year.voting_closes_at,
        'voting_closes_formatted': _format_dt(year.voting_closes_at)
        if year.voting_closes_at
        else 'TBD',
        'award_count': award_count,
        'company_label': company_label,
        'sender_name': EmailConfig.get_sender_name(),
        'sender_email': EmailConfig.get_default_from_email(),
        'support_email': EmailConfig.get_default_from_email(),
        'frontend_url': frontend_base_url(),
        'results_url': f'{frontend_base_url()}/{year.year}/results',
    }


def send_vote_confirmation_email(
    token: BallotToken,
    *,
    award_count: int,
    recipient_override: Optional[str] = None,
    is_async: bool = False,
) -> bool:
    """
    Thank the voter after a final ballot submit.

    Does not list individual choices. Idempotent via BallotInviteDelivery
    event ``vote_confirmation``.
    """
    token.refresh_from_db()
    if BallotInviteDelivery.objects.filter(
        token=token,
        event=EVENT,
        status=BallotInviteDelivery.Status.SENT,
    ).exists():
        logger.info(
            'vote confirmation already sent for token=%s — skipping',
            token.pk,
        )
        return True

    try:
        if not EmailConfig.is_enabled():
            BallotInviteDelivery.objects.update_or_create(
                token=token,
                event=EVENT,
                defaults={
                    'sent_at': timezone.now(),
                    'status': BallotInviteDelivery.Status.SKIPPED,
                    'error_message': 'EMAIL_ENABLED=False',
                },
            )
            logger.info(
                'EMAIL_ENABLED=False — skipped vote confirmation for token=%s',
                token.pk,
            )
            return False

        context = build_vote_confirmation_context(
            token,
            award_count=award_count,
            recipient_override=recipient_override,
        )
        subject = f'Ballot received — {token.year.title}'
        recipient = recipient_override or token.person.email
        reply_to = EmailConfig.get_default_from_email()

        ok = BaseEmailService.send_email(
            subject=subject,
            recipients=[recipient],
            template_name=VOTE_CONFIRMATION_TEMPLATE,
            context=context,
            reply_to=reply_to,
            is_async=is_async,
        )
        BallotInviteDelivery.objects.update_or_create(
            token=token,
            event=EVENT,
            defaults={
                'sent_at': timezone.now(),
                'status': (
                    BallotInviteDelivery.Status.SENT
                    if ok
                    else BallotInviteDelivery.Status.FAILED
                ),
                'error_message': '' if ok else 'send_vote_confirmation_email returned False',
            },
        )
        return ok
    except Exception as exc:
        logger.exception(
            'Failed to send vote confirmation for token %s: %s', token.pk, exc
        )
        try:
            BallotInviteDelivery.objects.update_or_create(
                token=token,
                event=EVENT,
                defaults={
                    'sent_at': timezone.now(),
                    'status': BallotInviteDelivery.Status.FAILED,
                    'error_message': str(exc)[:2000],
                },
            )
        except Exception:
            logger.exception(
                'Failed to record vote confirmation delivery for token %s',
                token.pk,
            )
        return False


def queue_vote_confirmation_email(token_id: int, award_count: int) -> None:
    """Load token and send confirmation (safe for transaction.on_commit)."""
    try:
        token = BallotToken.objects.select_related('person', 'year').get(pk=token_id)
    except BallotToken.DoesNotExist:
        logger.warning('vote confirmation skipped — token %s missing', token_id)
        return
    send_vote_confirmation_email(token, award_count=award_count, is_async=False)
