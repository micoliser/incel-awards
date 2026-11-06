from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0002_vote_audit_log'),
    ]

    operations = [
        migrations.AddField(
            model_name='ballottoken',
            name='submitted_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When set, this ballot is final and votes can no longer be changed.',
                null=True,
            ),
        ),
    ]
