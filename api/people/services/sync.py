"""
Sync OrgPerson rows from the company users API.

1. Fetch all users
2. Optionally keep only ORG_USERS_TEST_EMAILS (live-test allowlist)
3. Upsert by external_id
4. Reclassify company / electorate / nigeria eligibility
5. Soft-deactivate people missing from feed or is_active=false
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from people.models import OrgPerson
from people.services.classify import apply_classification
from people.services.org_client import OrgUsersClient


@dataclass
class SyncStats:
    fetched: int = 0
    kept: int = 0
    filtered_out: int = 0
    created: int = 0
    updated: int = 0
    deactivated: int = 0


def test_email_allowlist() -> frozenset[str]:
    """Normalized emails from ORG_USERS_TEST_EMAILS (empty = no filter)."""
    raw = getattr(settings, 'ORG_USERS_TEST_EMAILS', None) or []
    return frozenset(str(e).strip().lower() for e in raw if str(e).strip())


def filter_users_for_sync(
    users: Iterable[dict[str, Any]],
    *,
    allowlist: frozenset[str] | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """
    Apply ORG_USERS_TEST_EMAILS allowlist when non-empty.

    Returns (kept_users, filtered_out_count).
    """
    users_list = list(users)
    if allowlist is None:
        allowlist = test_email_allowlist()
    if not allowlist:
        return users_list, 0

    kept: list[dict[str, Any]] = []
    filtered_out = 0
    for payload in users_list:
        email = str(payload.get('email') or '').strip().lower()
        if email and email in allowlist:
            kept.append(payload)
        else:
            filtered_out += 1
    return kept, filtered_out


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
    test_emails: Iterable[str] | None = None,
) -> SyncStats:
    """
    Upsert OrgPerson from org API payloads and soft-deactivate missing/inactive.

    Pass `users` explicitly in tests; otherwise fetch via OrgUsersClient.

    When ``ORG_USERS_TEST_EMAILS`` is non-empty (or ``test_emails`` is passed),
    only those emails are kept active. Everyone else is treated as missing from
    the feed and soft-deactivated, so tokens/emails stay limited to the allowlist.
    Empty allowlist = use the full API roster.
    """
    if users is None:
        client = client or OrgUsersClient()
        users = client.fetch_all_users()

    stats = SyncStats()
    allowlist = (
        frozenset(str(e).strip().lower() for e in test_emails if str(e).strip())
        if test_emails is not None
        else test_email_allowlist()
    )
    kept_users, filtered_out = filter_users_for_sync(users, allowlist=allowlist)
    stats.fetched = filtered_out + len(kept_users)
    stats.filtered_out = filtered_out
    stats.kept = len(kept_users)

    seen_ids: set[int] = set()
    now = timezone.now()

    for payload in kept_users:
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
