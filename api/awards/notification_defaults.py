"""Default season-email rows for an AwardYear (one per notification event)."""

from __future__ import annotations

from awards.models import AwardNotificationConfig, AwardYear

# (event, open_offset, close_offset, subject_template)
DEFAULT_NOTIFICATION_SPECS: tuple[tuple[str, int, int, str], ...] = (
    (
        AwardNotificationConfig.Event.ELIGIBILITY_NOTICE,
        10,
        0,
        "You're eligible to vote — Incel Employee Awards {year}",
    ),
    (
        AwardNotificationConfig.Event.VOTE_INVITE,
        60,
        0,
        'Cast your vote — Incel Employee Awards {year}',
    ),
    (
        AwardNotificationConfig.Event.VOTING_OPENED,
        0,
        0,
        'Voting is open — Incel Employee Awards {year}',
    ),
    (
        AwardNotificationConfig.Event.VOTING_CLOSING_REMINDER,
        0,
        60,
        'Reminder: voting closes soon — Incel Employee Awards {year}',
    ),
    (
        AwardNotificationConfig.Event.VOTING_CLOSED,
        0,
        0,
        'Voting has closed — Incel Employee Awards {year}',
    ),
)


def ensure_default_notification_configs(year: AwardYear) -> int:
    """
    Create any missing season-email configs for ``year``.

    Does not overwrite existing rows (preserves admin timing / subject edits).
    Returns the number of rows created.
    """
    created = 0
    for event, open_offset, close_offset, subject in DEFAULT_NOTIFICATION_SPECS:
        _, was_created = AwardNotificationConfig.objects.get_or_create(
            year=year,
            event=event,
            defaults={
                'enabled': True,
                'channel': AwardNotificationConfig.Channel.EMAIL,
                'audience': AwardNotificationConfig.Audience.ALL_ELIGIBLE,
                'offset_minutes_before_open': open_offset,
                'offset_minutes_before_close': close_offset,
                'subject_template': subject,
                'extra': {},
            },
        )
        if was_created:
            created += 1
    return created
