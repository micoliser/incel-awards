from django.db import models
from django.core.exceptions import ValidationError


class BallotToken(models.Model):
    year = models.ForeignKey(
        'awards.AwardYear',
        on_delete=models.CASCADE,
        related_name='ballot_tokens',
    )
    person = models.ForeignKey(
        'people.OrgPerson',
        on_delete=models.CASCADE,
        related_name='ballot_tokens',
    )
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When set, this ballot is final and votes can no longer be changed.',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['year', 'person'],
                name='uniq_ballot_token_year_person',
            ),
        ]

    def __str__(self):
        return f'Token {self.person_id} @ {self.year_id}'

    @property
    def is_revoked(self):
        return self.revoked_at is not None


class BallotInviteDelivery(models.Model):
    class Status(models.TextChoices):
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'
        SKIPPED = 'skipped', 'Skipped'

    token = models.ForeignKey(
        BallotToken,
        on_delete=models.CASCADE,
        related_name='invite_deliveries',
    )
    event = models.CharField(max_length=32, default='vote_invite')
    sent_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=Status.choices)
    error_message = models.TextField(blank=True, default='')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['token', 'event'],
                name='uniq_ballot_invite_token_event',
            ),
        ]
        verbose_name = 'Ballot invite delivery'
        verbose_name_plural = 'Ballot invite deliveries'

    def __str__(self):
        return f'{self.event}:{self.token_id}:{self.status}'


class Vote(models.Model):
    award = models.ForeignKey(
        'awards.Award',
        on_delete=models.CASCADE,
        related_name='votes',
    )
    voter = models.ForeignKey(
        'people.OrgPerson',
        on_delete=models.CASCADE,
        related_name='votes',
    )
    nominee = models.ForeignKey(
        'awards.Nominee',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='votes',
    )
    selected_person = models.ForeignKey(
        'people.OrgPerson',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='open_award_votes',
    )
    electorate_at_vote = models.CharField(max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['award', 'voter'],
                name='uniq_vote_award_voter',
            ),
        ]

    def __str__(self):
        return f'Vote {self.voter_id} → award {self.award_id}'

    def clean(self):
        has_nominee = self.nominee_id is not None
        has_selected = self.selected_person_id is not None
        if has_nominee == has_selected:
            raise ValidationError(
                'Exactly one of nominee or selected_person must be set.'
            )


class VoteAuditLog(models.Model):
    """Immutable audit trail of vote creates / overwrites."""

    class Action(models.TextChoices):
        CREATED = 'created', 'Created'
        UPDATED = 'updated', 'Updated'

    award = models.ForeignKey(
        'awards.Award',
        on_delete=models.CASCADE,
        related_name='vote_audit_logs',
    )
    voter = models.ForeignKey(
        'people.OrgPerson',
        on_delete=models.CASCADE,
        related_name='vote_audit_logs',
    )
    ballot_token = models.ForeignKey(
        BallotToken,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vote_audit_logs',
    )
    action = models.CharField(max_length=16, choices=Action.choices)
    electorate = models.CharField(max_length=16)
    previous_nominee = models.ForeignKey(
        'awards.Nominee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    new_nominee = models.ForeignKey(
        'awards.Nominee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    previous_selected_person = models.ForeignKey(
        'people.OrgPerson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    new_selected_person = models.ForeignKey(
        'people.OrgPerson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vote audit log'
        verbose_name_plural = 'Vote audit logs'

    def __str__(self):
        return f'{self.action} vote award={self.award_id} voter={self.voter_id}'
