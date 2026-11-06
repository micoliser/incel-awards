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


class AwardCriterionInline(admin.TabularInline):
    model = AwardCriterion
    extra = 0
    ordering = ('sort_order',)


class NomineeInline(admin.TabularInline):
    model = Nominee
    extra = 0
    ordering = ('sort_order',)
    autocomplete_fields = ('org_person',)


class AwardNotificationConfigInline(admin.StackedInline):
    model = AwardNotificationConfig
    extra = 0


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
    list_display = (
        'year',
        'event',
        'enabled',
        'channel',
        'audience',
        'offset_minutes_before_open',
    )
    list_filter = ('event', 'enabled', 'audience', 'channel')


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
