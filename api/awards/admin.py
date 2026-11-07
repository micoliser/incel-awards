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

OPEN_OFFSET_EVENTS = {
    AwardNotificationConfig.Event.ELIGIBILITY_NOTICE,
    AwardNotificationConfig.Event.VOTE_INVITE,
}
CLOSE_OFFSET_EVENTS = {
    AwardNotificationConfig.Event.VOTING_CLOSING_REMINDER,
}


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
    class Meta:
        model = AwardNotificationConfig
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        open_field = self.fields.get('offset_minutes_before_open')
        close_field = self.fields.get('offset_minutes_before_close')
        if open_field:
            open_field.label = 'Minutes before voting opens'
            open_field.help_text = (
                'Used for eligibility notice and vote invite only.'
            )
        if close_field:
            close_field.label = 'Minutes before voting closes'
            close_field.help_text = (
                'Used for the closing reminder only (unsubmitted ballots).'
            )


class AwardNotificationConfigInline(admin.StackedInline):
    model = AwardNotificationConfig
    form = AwardNotificationConfigForm
    extra = 0
    fields = (
        'event',
        'enabled',
        'channel',
        'audience',
        'offset_minutes_before_open',
        'offset_minutes_before_close',
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
    fields = (
        'year',
        'event',
        'enabled',
        'channel',
        'audience',
        'offset_minutes_before_open',
        'offset_minutes_before_close',
        'subject_template',
        'extra',
    )

    class Media:
        js = ('awards/admin/notification_offsets.js',)

    @admin.display(description='Timing offset')
    def timing_offset(self, obj: AwardNotificationConfig):
        if obj.event in CLOSE_OFFSET_EVENTS:
            return f'{obj.offset_minutes_before_close} min before close'
        if obj.event in OPEN_OFFSET_EVENTS:
            return f'{obj.offset_minutes_before_open} min before open'
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
