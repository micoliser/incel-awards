"""
Ballot token generation for Nigeria-eligible staff + executive voters.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from awards.models import AwardYear
from people.models import OrgPerson
from voting.models import BallotToken


@dataclass
class TokenGenStats:
    created: int = 0
    skipped_existing: int = 0
    eligible: int = 0


def generate_token_value() -> str:
    return secrets.token_urlsafe(32)


def eligible_voters_queryset():
    """People who receive ballot tokens for a year."""
    return OrgPerson.objects.filter(
        is_active=True,
        is_nigeria_eligible=True,
        electorate__in=(
            OrgPerson.Electorate.STAFF,
            OrgPerson.Electorate.EXECUTIVE,
        ),
    )


@transaction.atomic
def generate_ballot_tokens(year: AwardYear | int) -> TokenGenStats:
    """
    Ensure a BallotToken exists for each Nigeria-eligible staff/executive for year.

    Unique (year, person). Does not create for Dubai / ineligible roles.
    Does not revive revoked tokens — existing rows are left alone.
    """
    if isinstance(year, int):
        year = AwardYear.objects.get(year=year)

    stats = TokenGenStats()
    voters = list(eligible_voters_queryset())
    stats.eligible = len(voters)

    existing = set(
        BallotToken.objects.filter(year=year).values_list('person_id', flat=True)
    )

    to_create = []
    for person in voters:
        if person.id in existing:
            stats.skipped_existing += 1
            continue
        to_create.append(
            BallotToken(
                year=year,
                person=person,
                token=generate_token_value(),
            )
        )
        stats.created += 1

    if to_create:
        BallotToken.objects.bulk_create(to_create)

    return stats


def resolve_ballot_token(raw_token: str, year: AwardYear | int) -> BallotToken | None:
    """
    Look up a non-revoked token for the given year.
    Returns None if missing / revoked / wrong year.
    """
    if not raw_token:
        return None
    if isinstance(year, int):
        year_filter = {'year__year': year}
    else:
        year_filter = {'year': year}

    token = (
        BallotToken.objects.filter(token=raw_token, **year_filter)
        .select_related('person', 'year')
        .first()
    )
    if token is None or token.is_revoked:
        return None
    return token


def touch_token_access(token: BallotToken) -> None:
    BallotToken.objects.filter(pk=token.pk).update(last_accessed_at=timezone.now())
