from django.contrib import admin

from people.models import OrgPerson


@admin.register(OrgPerson)
class OrgPersonAdmin(admin.ModelAdmin):
    list_display = (
        'external_id',
        'email',
        'first_name',
        'last_name',
        'role_code',
        'department_code',
        'unit_name',
        'company',
        'electorate',
        'is_nigeria_eligible',
        'is_active',
        'synced_at',
    )
    list_filter = (
        'company',
        'electorate',
        'is_nigeria_eligible',
        'is_active',
        'role_code',
        'department_code',
    )
    search_fields = ('email', 'first_name', 'last_name', 'external_id')
    readonly_fields = ('synced_at',)
