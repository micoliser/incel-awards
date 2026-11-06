"""
Sync OrgPerson rows from the company users API.

1. Fetch all users
2. Upsert by external_id
3. Reclassify company / electorate / nigeria eligibility
4. Soft-deactivate people missing from feed or is_active=false
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from django.db import transaction
from django.utils import timezone

from people.models import OrgPerson
from people.services.classify import apply_classification
from people.services.org_client import OrgUsersClient


@dataclass
class SyncStats:
    fetched: int = 0
    created: int = 0
    updated: int = 0
    deactivated: int = 0


def _str_field(payload: dict, *keys: str, default: str = '') -> str:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        return str(value).strip()
    return default


def map_org_user_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize a portal user dict into OrgPerson field kwargs (sans classification)."""
    external_id = payload.get('id')
    if external_id is None:
        raise ValueError('Org user payload missing id')

    unit = payload.get('unit_name')
    if unit is not None:
        unit = str(unit).strip() or None

    return {
        'external_id': int(external_id),
        'email': _str_field(payload, 'email'),
        'first_name': _str_field(payload, 'first_name'),
        'last_name': _str_field(payload, 'last_name'),
        'is_active': bool(payload.get('is_active', True)),
        'role_code': _str_field(payload, 'role_code'),
        'role_name': _str_field(payload, 'role_name', 'role'),
        'department_code': _str_field(payload, 'department_code'),
        'department_name': _str_field(payload, 'department_name', 'department'),
        'unit_name': unit,
        'raw_payload': payload,
    }


@transaction.atomic
def sync_org_people(
    users: Iterable[dict[str, Any]] | None = None,
    *,
    client: OrgUsersClient | None = None,
) -> SyncStats:
    """
    Upsert OrgPerson from org API payloads and soft-deactivate missing/inactive.

    Pass `users` explicitly in tests; otherwise fetch via OrgUsersClient.
    """
    if users is None:
        client = client or OrgUsersClient()
        users = client.fetch_all_users()

    stats = SyncStats()
    seen_ids: set[int] = set()
    now = timezone.now()

    for payload in users:
        stats.fetched += 1
        try:
            fields = map_org_user_payload(payload)
        except (TypeError, ValueError):
            continue

        external_id = fields.pop('external_id')
        seen_ids.add(external_id)

        person, created = OrgPerson.objects.get_or_create(
            external_id=external_id,
            defaults=fields,
        )
        if created:
            stats.created += 1
        else:
            for key, value in fields.items():
                setattr(person, key, value)
            stats.updated += 1

        # Source inactive → soft-deactivate locally before classification
        if not fields.get('is_active', True):
            person.is_active = False

        apply_classification(person)
        person.synced_at = now
        person.save()

    # Soft-deactivate people missing from this sync feed
    missing_qs = OrgPerson.objects.exclude(external_id__in=seen_ids).filter(is_active=True)
    for person in missing_qs:
        person.is_active = False
        apply_classification(person)
        person.synced_at = now
        person.save(update_fields=[
            'is_active',
            'company',
            'electorate',
            'is_nigeria_eligible',
            'synced_at',
        ])
        stats.deactivated += 1

    return stats
