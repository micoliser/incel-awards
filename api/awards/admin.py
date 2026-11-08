from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.utils.html import format_html

from awards.models import (
    Award,
    AwardCriterion,
    AwardNotificationConfig,
    AwardYear,
    Nominee,
)
from awards.notification_defaults import ensure_default_notification_configs


class AwardCriterionInline(admin.TabularInline):
    model = AwardCriterion
    extra = 0
    ordering = ('sort_order',)


class NomineeInline(admin.TabularInline):
    model = Nominee
    extra = 0
    ordering = ('sort_order',)
    autocomplete_fields = ('org_person',)


class AwardNotificationConfigForm(forms.ModelForm):
    """
    One config = one email. Expose a single timing field that maps to the
    correct DB column for that event (open-offset, close-offset, or none).
    """

    send_offset_minutes = forms.IntegerField(
        required=False,
        min_value=0,
        label='Send this many minutes beforehand',
        help_text='Only used for timed emails (eligibility, ballot invite, closing reminder).',
    )

    class Meta:
        model = AwardNotificationConfig
        fields = (
            'event',
            'enabled',
            'channel',
            'audience',
            'send_offset_minutes',
            'subject_template',
            'extra',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        event = None
        if instance and instance.pk:
            event = instance.event
        elif self.data.get(self.add_prefix('event')):
            event = self.data.get(self.add_prefix('event'))
        elif self.initial.get('event'):
            event = self.initial.get('event')

        timing = self.fields['send_offset_minutes']
        if event in AwardNotificationConfig.OPEN_OFFSET_EVENTS:
            timing.label = 'Minutes before voting opens'
            timing.help_text = (
                'Send this email this many minutes before voting_opens_at.'
            )
            if instance and instance.pk and not self.is_bound:
                timing.initial = instance.offset_minutes_before_open
        elif event in AwardNotificationConfig.CLOSE_OFFSET_EVENTS:
            timing.label = 'Minutes before voting closes'
            timing.help_text = (
                'Send this reminder this many minutes before voting_closes_at '
                '(unsubmitted ballots only).'
            )
            if instance and instance.pk and not self.is_bound:
                timing.initial = instance.offset_minutes_before_close
        elif event in AwardNotificationConfig.STATUS_EVENTS:
            timing.label = 'Timing'
            timing.help_text = (
                'Not used — this email sends when the voting window opens or closes.'
            )
            timing.widget = forms.HiddenInput()
        else:
            # New empty inline row: keep field visible until an event is chosen.
            timing.help_text = (
                'Pick an event first. Timed emails need minutes; open/end emails do not.'
            )

    def save(self, commit=True):
        obj = super().save(commit=False)
        minutes = self.cleaned_data.get('send_offset_minutes')
        if minutes is None:
            minutes = 0
        if obj.event in AwardNotificationConfig.OPEN_OFFSET_EVENTS:
            obj.offset_minutes_before_open = minutes
        elif obj.event in AwardNotificationConfig.CLOSE_OFFSET_EVENTS:
            obj.offset_minutes_before_close = minutes
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class AwardNotificationConfigInline(admin.StackedInline):
    model = AwardNotificationConfig
    form = AwardNotificationConfigForm
    extra = 0
    ordering = ('event',)
    verbose_name = 'Season email'
    verbose_name_plural = (
        'Season emails — one row per notification '
        '(eligibility → ballot invite → voting open → closing reminder → voting ended)'
    )
    fields = (
        'event',
        'enabled',
        'channel',
        'audience',
        'send_offset_minutes',
        'subject_template',
        'extra',
    )

    class Media:
        js = ('awards/admin/notification_offsets.js',)


@admin.register(AwardYear)
class AwardYearAdmin(admin.ModelAdmin):
    list_display = (
        'year',
        'title',
        'status',
        'voting_opens_at',
        'voting_closes_at',
        'results_published_at',
    )
    list_filter = ('status',)
    search_fields = ('title', 'slug', 'year')
    prepopulated_fields = {'slug': ('year',)}
    readonly_fields = ('committee_results_preview_link',)
    fieldsets = (
        (None, {
            'fields': (
                'year',
                'title',
                'slug',
                'status',
                'description',
            ),
        }),
        ('Voting window', {
            'fields': ('voting_opens_at', 'voting_closes_at'),
        }),
        ('Results', {
            'description': (
                'Leave results_published_at empty until after the ceremony. '
                'Share the committee preview link only with the awards committee.'
            ),
            'fields': (
                'results_published_at',
                'results_preview_token',
                'committee_results_preview_link',
            ),
        }),
    )
    inlines = [AwardNotificationConfigInline]
    actions = ('rotate_results_preview_token',)

    class Media:
        js = ('awards/admin/notification_offsets.js',)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        if object_id:
            year = AwardYear.objects.filter(pk=object_id).first()
            if year is not None:
                ensure_default_notification_configs(year)
        return super().changeform_view(
            request, object_id, form_url, extra_context
        )

    @admin.display(description='Committee preview URL')
    def committee_results_preview_link(self, obj: AwardYear):
        if not obj.pk:
            return 'Save the year first.'
        token = obj.ensure_results_preview_token()
        base = (getattr(settings, 'FRONTEND_BASE_URL', '') or 'http://localhost:3000').rstrip('/')
        results_url = f'{base}/{obj.year}/results?preview={token}'
        audit_url = f'{base}/{obj.year}/results/audit?preview={token}'
        return format_html(
            '<p><strong>Results preview</strong><br>'
            '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a></p>'
            '<p><strong>Full voting audit</strong><br>'
            '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a></p>'
            '<p class="help">Both links require this preview token. '
            'Do not post them publicly. Leave results_published_at empty until '
            'after the ceremony (that only unlocks the public winners page, never the audit).</p>',
            results_url,
            results_url,
            audit_url,
            audit_url,
        )

    @admin.action(description='Rotate committee results preview token')
    def rotate_results_preview_token(self, request, queryset):
        for year in queryset:
            year.rotate_results_preview_token()
        self.message_user(
            request,
            f'Rotated preview token for {queryset.count()} year(s). '
            'Old committee links stop working.',
            messages.WARNING,
        )


@admin.register(AwardNotificationConfig)
class AwardNotificationConfigAdmin(admin.ModelAdmin):
    form = AwardNotificationConfigForm
    list_display = (
        'year',
        'event',
        'enabled',
        'channel',
        'audience',
        'timing_offset',
    )
    list_filter = ('event', 'enabled', 'audience', 'channel')
    ordering = ('year', 'event')
    fields = (
        'year',
        'event',
        'enabled',
        'channel',
        'audience',
        'send_offset_minutes',
        'subject_template',
        'extra',
    )

    class Media:
        js = ('awards/admin/notification_offsets.js',)

    @admin.display(description='Timing')
    def timing_offset(self, obj: AwardNotificationConfig):
        if obj.event in AwardNotificationConfig.CLOSE_OFFSET_EVENTS:
            return f'{obj.offset_minutes_before_close} min before close'
        if obj.event in AwardNotificationConfig.OPEN_OFFSET_EVENTS:
            return f'{obj.offset_minutes_before_open} min before open'
        if obj.event in AwardNotificationConfig.STATUS_EVENTS:
            return 'At window open/close'
        return '—'


@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'year',
        'slug',
        'division',
        'voting_mode',
        'executive_weight',
        'staff_weight',
        'sort_order',
        'is_active',
    )
    list_filter = ('year', 'division', 'voting_mode', 'is_active')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [AwardCriterionInline, NomineeInline]


@admin.register(AwardCriterion)
class AwardCriterionAdmin(admin.ModelAdmin):
    list_display = ('label', 'award', 'weight_percent', 'sort_order')
    list_filter = ('award__year',)
    search_fields = ('label', 'award__name')


@admin.register(Nominee)
class NomineeAdmin(admin.ModelAdmin):
    list_display = (
        'display_name',
        'award',
        'nominee_type',
        'is_confirmed',
        'sort_order',
    )
    list_filter = ('nominee_type', 'is_confirmed', 'award__year')
    search_fields = ('display_name', 'award__name')
    autocomplete_fields = ('org_person',)
