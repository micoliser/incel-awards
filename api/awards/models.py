import secrets

from django.db import models


def generate_results_preview_token() -> str:
    return secrets.token_urlsafe(32)


class AwardYear(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SCHEDULED = 'scheduled', 'Scheduled'
        VOTING = 'voting', 'Voting'
        CLOSED = 'closed', 'Closed'
        ARCHIVED = 'archived', 'Archived'

    year = models.PositiveIntegerField(unique=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=64)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    voting_opens_at = models.DateTimeField(null=True, blank=True)
    voting_closes_at = models.DateTimeField(null=True, blank=True)
    results_published_at = models.DateTimeField(null=True, blank=True)
    # Private committee link: /{year}/results?preview=<token>
    # Public /results stays closed until results_published_at is set.
    results_preview_token = models.CharField(
        max_length=64,
        blank=True,
        default=generate_results_preview_token,
        help_text=(
            'Secret for committee-only results preview. Share the preview URL; '
            'do not publish results_published_at until after the ceremony.'
        ),
    )
    description = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-year']
        verbose_name = 'Award year'
        verbose_name_plural = 'Award years'

    def __str__(self):
        return self.title or str(self.year)

    def ensure_results_preview_token(self) -> str:
        if not self.results_preview_token:
            self.results_preview_token = generate_results_preview_token()
            self.save(update_fields=['results_preview_token'])
        return self.results_preview_token

    def rotate_results_preview_token(self) -> str:
        self.results_preview_token = generate_results_preview_token()
        self.save(update_fields=['results_preview_token'])
        return self.results_preview_token



class AwardNotificationConfig(models.Model):
    class Event(models.TextChoices):
        # One row per season email. Timing fields apply only where noted.
        ELIGIBILITY_NOTICE = (
            'eligibility_notice',
            '1. Eligibility notice (before open)',
        )
        VOTE_INVITE = (
            'vote_invite',
            '2. Vote ballot invite (before open)',
        )
        VOTING_OPENED = (
            'voting_opened',
            '3. Voting open (when window opens)',
        )
        VOTING_CLOSING_REMINDER = (
            'voting_closing_reminder',
            '4. Voting closing reminder (before close)',
        )
        VOTING_CLOSED = (
            'voting_closed',
            '5. Voting ended (when window closes)',
        )

    # Events that use offset_minutes_before_open / offset_minutes_before_close.
    OPEN_OFFSET_EVENTS = frozenset({
        Event.ELIGIBILITY_NOTICE.value,
        Event.VOTE_INVITE.value,
    })
    CLOSE_OFFSET_EVENTS = frozenset({
        Event.VOTING_CLOSING_REMINDER.value,
    })
    # Fired at status transition; no minute offset.
    STATUS_EVENTS = frozenset({
        Event.VOTING_OPENED.value,
        Event.VOTING_CLOSED.value,
    })

    class Channel(models.TextChoices):
        EMAIL = 'email', 'Email'

    class Audience(models.TextChoices):
        ALL_ELIGIBLE = 'all_eligible', 'All eligible'
        STAFF_ONLY = 'staff_only', 'Staff only'
        EXECUTIVES_ONLY = 'executives_only', 'Executives only'
        TOURISM_ONLY = 'tourism_only', 'Tourism only'
        GLOBAL_ONLY = 'global_only', 'Global only'

    year = models.ForeignKey(
        AwardYear,
        on_delete=models.CASCADE,
        related_name='notification_configs',
    )
    event = models.CharField(max_length=32, choices=Event.choices)
    enabled = models.BooleanField(default=True)
    channel = models.CharField(
        max_length=16,
        choices=Channel.choices,
        default=Channel.EMAIL,
    )
    audience = models.CharField(
        max_length=32,
        choices=Audience.choices,
        default=Audience.ALL_ELIGIBLE,
    )
    offset_minutes_before_open = models.PositiveIntegerField(
        default=60,
        help_text='Minutes before voting_opens_at (eligibility notice / vote invite).',
    )
    offset_minutes_before_close = models.PositiveIntegerField(
        default=60,
        help_text=(
            'Minutes before voting_closes_at (closing reminder; unsubmitted only).'
        ),
    )
    subject_template = models.CharField(
        max_length=255,
        blank=True,
        default='Cast your vote — Incel Employee Awards {year}',
    )
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['year', 'event'],
                name='uniq_award_notification_year_event',
            ),
        ]
        verbose_name = 'Award notification config'
        verbose_name_plural = 'Award notification configs'

    def __str__(self):
        return f'{self.year_id}:{self.event}'


class Award(models.Model):
    class Division(models.TextChoices):
        TOURISM = 'tourism', 'Tourism'
        GLOBAL = 'global', 'Global'
        SHARED = 'shared', 'Shared'

    class VotingMode(models.TextChoices):
        WEIGHTED = 'weighted', 'Weighted'
        STAFF_SHORTLIST = 'staff_shortlist', 'Staff shortlist'
        STAFF_OPEN = 'staff_open', 'Staff open'

    year = models.ForeignKey(
        AwardYear,
        on_delete=models.CASCADE,
        related_name='awards',
    )
    slug = models.SlugField(max_length=128)
    name = models.CharField(max_length=255)
    description = models.TextField(
        blank=True,
        default='',
        help_text='About the award — shown on award pages and ballots.',
    )
    ideal_winner = models.TextField(
        blank=True,
        default='',
        help_text=(
            'An ideal winner — one trait per line. Shown under About on award '
            'pages and ballots when set.'
        ),
    )
    division = models.CharField(max_length=16, choices=Division.choices)
    voting_mode = models.CharField(max_length=32, choices=VotingMode.choices)
    executive_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Fraction of total for executives (weighted mode only), e.g. 0.30',
    )
    staff_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Fraction of total for staff (weighted mode only), e.g. 0.70',
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    company_vote_gated = models.BooleanField(
        default=True,
        help_text=(
            'If true, tourism/global awards are limited to that company\'s staff. '
            'If false, every Nigeria-eligible staff and executive may vote '
            '(e.g. Excellent Leadership Tourism/Global).'
        ),
    )

    class Meta:
        ordering = ['sort_order', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['year', 'slug'],
                name='uniq_award_year_slug',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.year.year})'


class AwardCriterion(models.Model):
    award = models.ForeignKey(
        Award,
        on_delete=models.CASCADE,
        related_name='criteria',
    )
    label = models.CharField(max_length=255)
    weight_percent = models.DecimalField(max_digits=5, decimal_places=2)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Award criterion'
        verbose_name_plural = 'Award criteria'

    def __str__(self):
        return f'{self.label} ({self.weight_percent}%)'


class Nominee(models.Model):
    class NomineeType(models.TextChoices):
        PERSON = 'person', 'Person'
        DEPARTMENT = 'department', 'Department'

    award = models.ForeignKey(
        Award,
        on_delete=models.CASCADE,
        related_name='nominees',
    )
    nominee_type = models.CharField(
        max_length=16,
        choices=NomineeType.choices,
        default=NomineeType.PERSON,
    )
    display_name = models.CharField(max_length=255)
    org_person = models.ForeignKey(
        'people.OrgPerson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nominations',
    )
    justification = models.TextField(blank=True, default='')
    basis_for_nomination = models.TextField(blank=True, default='')
    is_confirmed = models.BooleanField(
        default=True,
        help_text='Only confirmed nominees appear on ballots.',
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.display_name
