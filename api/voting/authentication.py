"""
Ballot token resolution helpers (query ?token= or header X-Ballot-Token).
"""

from __future__ import annotations

from rest_framework.exceptions import AuthenticationFailed, NotFound, PermissionDenied

from awards.models import AwardYear
from voting.services.tokens import resolve_ballot_token, touch_token_access


HEADER_NAME = 'HTTP_X_BALLOT_TOKEN'


def extract_raw_token(request) -> str | None:
    raw = request.query_params.get('token') or request.META.get(HEADER_NAME)
    if raw is None:
        return None
    raw = str(raw).strip()
    return raw or None


def get_year_or_404(year: int) -> AwardYear:
    try:
        return AwardYear.objects.get(year=year)
    except AwardYear.DoesNotExist as exc:
        raise NotFound('Year not found.') from exc


def authenticate_ballot(request, year: int, *, touch: bool = True):
    """
    Resolve ballot token for year.

    Raises AuthenticationFailed (401) if token missing/invalid/revoked.
    Raises NotFound (404) if year missing.
    """
    award_year = get_year_or_404(year)
    raw = extract_raw_token(request)
    if not raw:
        raise AuthenticationFailed('Ballot token required (?token= or X-Ballot-Token).')

    ballot = resolve_ballot_token(raw, award_year)
    if ballot is None:
        raise AuthenticationFailed('Invalid or revoked ballot token.')

    person = ballot.person
    if not person.is_active or not person.is_nigeria_eligible:
        raise PermissionDenied('Voter is no longer eligible.')

    if touch:
        touch_token_access(ballot)

    return award_year, ballot, person
