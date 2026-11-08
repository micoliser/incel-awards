# Ensure every AwardYear has all five season-email notification configs.

from django.db import migrations, models


DEFAULT_SPECS = (
    (
        'eligibility_notice',
        10,
        0,
        "You're eligible to vote — Incel Employee Awards {year}",
    ),
    (
        'vote_invite',
        60,
        0,
        'Cast your vote — Incel Employee Awards {year}',
    ),
    (
        'voting_opened',
        0,
        0,
        'Voting is open — Incel Employee Awards {year}',
    ),
    (
        'voting_closing_reminder',
        0,
        60,
        'Reminder: voting closes soon — Incel Employee Awards {year}',
    ),
    (
        'voting_closed',
        0,
        0,
        'Voting has closed — Incel Employee Awards {year}',
    ),
)

EVENT_CHOICES = [
    ('eligibility_notice', '1. Eligibility notice (before open)'),
    ('vote_invite', '2. Vote ballot invite (before open)'),
    ('voting_opened', '3. Voting open (when window opens)'),
    ('voting_closing_reminder', '4. Voting closing reminder (before close)'),
    ('voting_closed', '5. Voting ended (when window closes)'),
]


def ensure_configs(apps, schema_editor):
    AwardYear = apps.get_model('awards', 'AwardYear')
    AwardNotificationConfig = apps.get_model('awards', 'AwardNotificationConfig')
    for year in AwardYear.objects.all():
        for event, open_offset, close_offset, subject in DEFAULT_SPECS:
            AwardNotificationConfig.objects.get_or_create(
                year=year,
                event=event,
                defaults={
                    'enabled': True,
                    'channel': 'email',
                    'audience': 'all_eligible',
                    'offset_minutes_before_open': open_offset,
                    'offset_minutes_before_close': close_offset,
                    'subject_template': subject,
                    'extra': {},
                },
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('awards', '0005_voting_closing_reminder'),
    ]

    operations = [
        migrations.AlterField(
            model_name='awardnotificationconfig',
            name='event',
            field=models.CharField(choices=EVENT_CHOICES, max_length=32),
        ),
        migrations.RunPython(ensure_configs, noop_reverse),
    ]
