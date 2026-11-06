from django.db import migrations, models


def seed_eligibility_notice_configs(apps, schema_editor):
    AwardYear = apps.get_model('awards', 'AwardYear')
    AwardNotificationConfig = apps.get_model('awards', 'AwardNotificationConfig')
    for year in AwardYear.objects.all():
        AwardNotificationConfig.objects.update_or_create(
            year=year,
            event='eligibility_notice',
            defaults={
                'enabled': True,
                'channel': 'email',
                'audience': 'all_eligible',
                'offset_minutes_before_open': 10,
                'subject_template': (
                    "You're eligible to vote — Incel Employee Awards {year}"
                ),
                'extra': {},
            },
        )


def unseed_eligibility_notice_configs(apps, schema_editor):
    AwardNotificationConfig = apps.get_model('awards', 'AwardNotificationConfig')
    AwardNotificationConfig.objects.filter(event='eligibility_notice').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('awards', '0003_results_preview_token_fix'),
    ]

    operations = [
        migrations.AlterField(
            model_name='awardnotificationconfig',
            name='event',
            field=models.CharField(
                choices=[
                    ('eligibility_notice', 'Eligibility notice'),
                    ('vote_invite', 'Vote invite'),
                ],
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name='awardnotificationconfig',
            name='offset_minutes_before_open',
            field=models.PositiveIntegerField(
                default=60,
                help_text=(
                    'Send this email this many minutes before voting_opens_at. '
                    'Example: 10 = ten minutes before voting begins.'
                ),
            ),
        ),
        migrations.RunPython(
            seed_eligibility_notice_configs,
            unseed_eligibility_notice_configs,
        ),
    ]
