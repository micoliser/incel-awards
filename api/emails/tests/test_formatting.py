from datetime import datetime, timezone as dt_timezone

from django.test import SimpleTestCase, override_settings
from django.utils import timezone

from emails.formatting import format_email_datetime


class FormatEmailDatetimeTests(SimpleTestCase):
    @override_settings(TIME_ZONE='Africa/Lagos')
    def test_converts_utc_instant_to_lagos_wall_clock(self):
        # 14:00 UTC → 15:00 WAT
        instant = datetime(2026, 3, 15, 14, 0, tzinfo=dt_timezone.utc)
        self.assertEqual(
            format_email_datetime(instant),
            'Mar 15, 2026, 3:00 p.m.',
        )

    def test_none_uses_empty_label(self):
        self.assertEqual(format_email_datetime(None), 'TBD')
        self.assertEqual(
            format_email_datetime(None, empty='just now'),
            'just now',
        )

    @override_settings(TIME_ZONE='Africa/Lagos')
    def test_matches_timezone_localtime_pattern(self):
        instant = timezone.now().replace(microsecond=0)
        local = timezone.localtime(instant)
        from django.utils.formats import date_format

        self.assertEqual(
            format_email_datetime(instant),
            date_format(local, 'M j, Y, g:i a'),
        )
