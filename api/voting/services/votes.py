"""
Final ballot submit with eligibility + window enforcement + audit logging.

Votes are written once. After a successful complete submit the ballot token is
marked submitted and further changes are rejected.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.utils import timezone

from awards.models import Award, AwardYear, Nominee
from people.models import OrgPerson
from voting.models import BallotToken, Vote, VoteAuditLog
from voting.services.eligibility import awards_for_voter, person_may_vote_on_award


class VoteValidationError(Exception):
    def __init__(self, message: str, *, code: str = 'invalid'):
        super().__init__(message)
        self.message = message
        self.code = code


def voting_writes_allowed(year: AwardYear, now=None) -> bool:
    """
    Accept votes when:
    - voting_opens_at / voting_closes_at are set and now is inside the window, OR
    - windows are unset and year.status == voting (test / early open path).

    Draft with unset windows → closed for writes.
    """
    now = now or timezone.now()
    opens = year.voting_opens_at
    closes = year.voting_closes_at

    if opens is not None or closes is not None:
        if opens is not None and now < opens:
            return False
        if closes is not None and now >= closes:
            return False
        return True

    return year.status == AwardYear.Status.VOTING


def ballot_is_submitted(ballot_token: BallotToken | None) -> bool:
    return bool(ballot_token is not None and ballot_token.submitted_at is not None)


def ballot_writes_allowed(year: AwardYear, ballot_token: BallotToken | None, now=None) -> bool:
    return voting_writes_allowed(year, now=now) and not ballot_is_submitted(ballot_token)


@dataclass
class UpsertResult:
    votes: list[Vote]
    created: int = 0
    updated: int = 0


def _resolve_award(year: AwardYear, slug: str) -> Award:
    award = Award.objects.filter(year=year, slug=slug, is_active=True).first()
    if award is None:
        raise VoteValidationError(f'Unknown award: {slug}', code='unknown_award')
    return award


def _validate_choice(award: Award, item: dict[str, Any]) -> tuple[Nominee | None, OrgPerson | None]:
    nominee_id = item.get('nominee_id')
    selected_person_id = item.get('selected_person_id')

    if award.voting_mode == Award.VotingMode.STAFF_OPEN:
        if selected_person_id is None:
            raise VoteValidationError(
                f'Award {award.slug} requires selected_person_id',
                code='missing_selected_person',
            )
        if nominee_id is not None:
            raise VoteValidationError(
                f'Award {award.slug} does not accept nominee_id',
                code='invalid_choice',
            )
        person = OrgPerson.objects.filter(
            pk=selected_person_id,
            is_active=True,
            is_nigeria_eligible=True,
        ).first()
        if person is None:
            raise VoteValidationError(
                f'selected_person_id {selected_person_id} is not Nigeria-eligible',
                code='invalid_selected_person',
            )
        return None, person

    # weighted / staff_shortlist
    if nominee_id is None:
        raise VoteValidationError(
            f'Award {award.slug} requires nominee_id',
            code='missing_nominee',
        )
    if selected_person_id is not None:
        raise VoteValidationError(
            f'Award {award.slug} does not accept selected_person_id',
            code='invalid_choice',
        )
    nominee = Nominee.objects.filter(
        pk=nominee_id,
        award=award,
        is_confirmed=True,
    ).first()
    if nominee is None:
        raise VoteValidationError(
            f'nominee_id {nominee_id} is not a confirmed nominee for {award.slug}',
            code='invalid_nominee',
        )
    return nominee, None


def _write_audit(
    *,
    award: Award,
    voter: OrgPerson,
    ballot_token: BallotToken | None,
    action: str,
    electorate: str,
    previous_nominee: Nominee | None,
    new_nominee: Nominee | None,
    previous_selected: OrgPerson | None,
    new_selected: OrgPerson | None,
) -> VoteAuditLog:
    return VoteAuditLog.objects.create(
        award=award,
        voter=voter,
        ballot_token=ballot_token,
        action=action,
        electorate=electorate,
        previous_nominee=previous_nominee,
        new_nominee=new_nominee,
        previous_selected_person=previous_selected,
        new_selected_person=new_selected,
    )


def _require_complete_ballot(
    *,
    year: AwardYear,
    voter: OrgPerson,
    items: list[dict[str, Any]],
) -> None:
    allowed = awards_for_voter(voter, year)
    required = {a.slug for a in allowed}
    provided = set()
    for item in items:
        if not isinstance(item, dict):
            raise VoteValidationError('Each vote must be an object', code='invalid_payload')
        slug = item.get('award_slug')
        if not slug:
            raise VoteValidationError('award_slug is required', code='missing_award_slug')
        if slug in provided:
            raise VoteValidationError(
                f'Duplicate award_slug in ballot: {slug}',
                code='duplicate_award',
            )
        provided.add(slug)

    if provided != required:
        missing = sorted(required - provided)
        extra = sorted(provided - required)
        parts = []
        if missing:
            parts.append(f'missing {", ".join(missing)}')
        if extra:
            parts.append(f'unexpected {", ".join(extra)}')
        raise VoteValidationError(
            'Submit a complete ballot covering every award you can vote on'
            + (f' ({"; ".join(parts)})' if parts else ''),
            code='incomplete_ballot',
        )


@transaction.atomic
def upsert_votes(
    *,
    year: AwardYear,
    voter: OrgPerson,
    items: list[dict[str, Any]],
    ballot_token: BallotToken | None = None,
) -> UpsertResult:
    if not voting_writes_allowed(year):
        raise VoteValidationError('Voting is closed for this year', code='window_closed')

    if not voter.is_nigeria_eligible or voter.electorate not in (
        OrgPerson.Electorate.STAFF,
        OrgPerson.Electorate.EXECUTIVE,
    ):
        raise VoteValidationError('Voter is not eligible', code='ineligible_voter')

    locked_token = None
    if ballot_token is not None:
        locked_token = (
            BallotToken.objects.select_for_update()
            .filter(pk=ballot_token.pk)
            .first()
        )
        if locked_token is None:
            raise VoteValidationError('Ballot token not found', code='invalid_token')
        if locked_token.submitted_at is not None:
            raise VoteValidationError(
                'This ballot has already been submitted and cannot be changed',
                code='already_submitted',
            )

    _require_complete_ballot(year=year, voter=voter, items=items)

    result = UpsertResult(votes=[])
    for item in items:
        slug = item.get('award_slug')
        award = _resolve_award(year, slug)
        if not person_may_vote_on_award(voter, award):
            raise VoteValidationError(
                f'Voter may not vote on award {slug}',
                code='division_forbidden',
            )

        nominee, selected = _validate_choice(award, item)

        locked = (
            Vote.objects.select_for_update()
            .filter(award=award, voter=voter)
            .first()
        )
        if locked is not None:
            # Should not happen for a first-time complete submit; treat as locked.
            raise VoteValidationError(
                'This ballot has already been submitted and cannot be changed',
                code='already_submitted',
            )

        vote = Vote(
            award=award,
            voter=voter,
            nominee=nominee,
            selected_person=selected,
            electorate_at_vote=voter.electorate,
        )
        vote.full_clean()
        vote.save()
        _write_audit(
            award=award,
            voter=voter,
            ballot_token=locked_token or ballot_token,
            action=VoteAuditLog.Action.CREATED,
            electorate=voter.electorate,
            previous_nominee=None,
            new_nominee=nominee,
            previous_selected=None,
            new_selected=selected,
        )
        result.created += 1
        result.votes.append(vote)

    if locked_token is not None:
        locked_token.submitted_at = timezone.now()
        locked_token.save(update_fields=['submitted_at'])

    return result
