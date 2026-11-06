import logging
import threading
from typing import Any, Dict, List, Optional

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from emails.config import EmailConfig

logger = logging.getLogger(__name__)


class BaseEmailService:
    """
    Base email service providing dual HTML/text rendering,
    graceful error handling, and non-blocking background dispatch.
    """

    @staticmethod
    def close_connection():
        """
        Explicitly close Django database connections used or opened
        in background daemon threads to prevent connection pool leaks.
        """
        try:
            from django.db import connection

            connection.close()
        except Exception:
            pass

    @staticmethod
    def send_email(
        subject: str,
        recipients: List[str],
        template_name: str,
        context: Dict[str, Any],
        reply_to: Optional[str] = None,
        is_async: bool = True,
    ) -> bool:
        """
        Send an email. In async mode, uses a background daemon thread
        to prevent external SMTP latency from blocking callers.
        """
        if not EmailConfig.is_enabled():
            logger.info(
                "Email sending is disabled (EMAIL_ENABLED=False). "
                "Would have sent '%s' to %s",
                subject,
                recipients,
            )
            return False

        if not recipients:
            logger.warning("No recipients provided for email '%s'", subject)
            return False

        clean_recipients = [r.strip() for r in recipients if r and r.strip()]
        if not clean_recipients:
            logger.warning(
                "Empty recipient list after cleaning for email '%s'", subject
            )
            return False

        if is_async:

            def _async_worker():
                try:
                    BaseEmailService._send_sync(
                        subject, clean_recipients, template_name, context, reply_to
                    )
                finally:
                    BaseEmailService.close_connection()

            thread = threading.Thread(
                target=_async_worker,
                daemon=True,
                name=f'EmailThread-{clean_recipients[0]}',
            )
            thread.start()
            return True

        return BaseEmailService._send_sync(
            subject, clean_recipients, template_name, context, reply_to
        )

    @staticmethod
    def _send_sync(
        subject: str,
        recipients: List[str],
        template_name: str,
        context: Dict[str, Any],
        reply_to: Optional[str] = None,
    ) -> bool:
        """Executes the synchronous rendering and transmission of the email."""
        try:
            html_message = render_to_string(template_name, context)
            text_message = strip_tags(html_message).strip()

            from_email = EmailConfig.format_from_email()
            reply_to_list = (
                [reply_to.strip()] if reply_to and reply_to.strip() else None
            )

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=from_email,
                to=recipients,
                reply_to=reply_to_list,
            )
            email.attach_alternative(html_message, 'text/html')

            if EmailConfig.is_debug_mode():
                logger.info(
                    '\n%s\n[DEBUG EMAIL TRANSMISSION]\nFrom: %s\nTo: %s\n'
                    'Subject: %s\nBody:\n%s\n%s',
                    '=' * 60,
                    from_email,
                    ', '.join(recipients),
                    subject,
                    text_message[:500] + ('...' if len(text_message) > 500 else ''),
                    '=' * 60,
                )
                return True

            email.send(fail_silently=False)
            logger.info(
                "Successfully sent email '%s' to %s",
                subject,
                ', '.join(recipients),
            )
            return True

        except Exception as exc:
            logger.exception(
                "Failed to send email '%s' to %s: %s", subject, recipients, exc
            )
            return False
