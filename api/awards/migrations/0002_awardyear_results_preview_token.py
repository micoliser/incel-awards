import secrets

from django.db import migrations, models


def _token():
    return secrets.token_urlsafe(32)


def backfill_preview_tokens(apps, schema_editor):
    AwardYear = apps.get_model('awards', 'AwardYear')
    for year in AwardYear.objects.all():
        if not year.results_preview_token:
            year.results_preview_token = _token()
            year.save(update_fields=['results_preview_token'])


class Migration(migrations.Migration):
    dependencies = [
        ('awards', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='awardyear',
            name='results_preview_token',
            field=models.CharField(
                blank=True,
                default='',
                help_text=(
                    'Secret for committee-only results preview. Share the preview URL; '
                    'do not publish results_published_at until after the ceremony.'
                ),
                max_length=64,
            ),
        ),
        migrations.RunPython(backfill_preview_tokens, migrations.RunPython.noop),
    ]
