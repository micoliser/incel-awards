"""Shared datetime display for outbound emails.

Mirrors incel-portal's pattern: ``date_format(timezone.localtime(...), ...)``.
Display zone comes from Django ``TIME_ZONE`` (Africa/Lagos for awards).
"""

from __future__ import annotations

from typing import Any, Optional

from django.utils import timezone
from django.utils.formats import date_format

# Same format string as incel-portal daily_report_emails.
EMAIL_DATETIME_FORMAT = 'M j, Y, g:i a'


def format_email_datetime(value: Optional[Any], *, empty: str = 'TBD') -> str:
    if value is None:
        return empty
    local = timezone.localtime(value) if timezone.is_aware(value) else value
    return date_format(local, EMAIL_DATETIME_FORMAT)
