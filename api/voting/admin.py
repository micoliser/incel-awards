from django.contrib import admin

from voting.models import BallotInviteDelivery, BallotToken, Vote, VoteAuditLog


@admin.register(BallotToken)
class BallotTokenAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'year',
        'person',
        'created_at',
        'submitted_at',
        'revoked_at',
        'last_accessed_at',
    )
    list_filter = ('year',)
    search_fields = ('token', 'person__email', 'person__first_name', 'person__last_name')
    autocomplete_fields = ('person',)
    readonly_fields = ('token', 'created_at', 'last_accessed_at', 'submitted_at')


@admin.register(BallotInviteDelivery)
class BallotInviteDeliveryAdmin(admin.ModelAdmin):
    list_display = ('token', 'event', 'status', 'sent_at')
    list_filter = ('event', 'status')
    search_fields = ('token__person__email',)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = (
        'award',
        'voter',
        'nominee',
        'selected_person',
        'electorate_at_vote',
        'updated_at',
    )
    list_filter = ('award__year', 'electorate_at_vote')
    search_fields = ('voter__email', 'nominee__display_name')
    autocomplete_fields = ('voter', 'nominee', 'selected_person')


@admin.register(VoteAuditLog)
class VoteAuditLogAdmin(admin.ModelAdmin):
    """Readonly audit trail — no add/change/delete in admin."""

    list_display = (
        'created_at',
        'action',
        'award',
        'voter',
        'electorate',
        'previous_nominee',
        'new_nominee',
        'previous_selected_person',
        'new_selected_person',
        'ballot_token',
    )
    list_filter = ('action', 'electorate', 'award__year')
    search_fields = (
        'voter__email',
        'previous_nominee__display_name',
        'new_nominee__display_name',
    )
    readonly_fields = (
        'award',
        'voter',
        'ballot_token',
        'action',
        'electorate',
        'previous_nominee',
        'new_nominee',
        'previous_selected_person',
        'new_selected_person',
        'created_at',
    )
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
