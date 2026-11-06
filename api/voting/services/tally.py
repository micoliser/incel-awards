"""
Award tally algorithms (docs/domain-rules.md §5).

Weighted mode:
  - E = count of eligible executives for this award (division-gated), NOT hardcoded 2.
  - exec_vote_value = executive_weight / E
  - nominee exec share = exec_vote_value * votes_from_executives_for_nominee
  - staff share = (nominee_staff_votes / total_staff_votes_cast) * staff_weight
    (0 if no staff votes cast)
  - final = exec share + staff share
  - Tie-break: more exec votes, then more staff votes, else leave as tie.

Staff shortlist / staff open:
  - Simple count of votes; highest wins (tie if equal).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from django.db.models import Count

from awards.models import Award, Nominee
from people.models import OrgPerson
from voting.models import Vote
from voting.services.eligibility import eligible_executives_for_award


ZERO = Decimal('0')


@dataclass
class NomineeTally:
    nominee_id: int | None
    selected_person_id: int | None
    display_name: str
    score: Decimal
    exec_votes: int = 0
    staff_votes: int = 0
    total_votes: int = 0
    is_winner: bool = False
    is_tie: bool = False


@dataclass
class AwardTallyResult:
    award_id: int
    award_slug: str
    voting_mode: str
    eligible_exec_count: int
    nominees: list[NomineeTally] = field(default_factory=list)
    winners: list[NomineeTally] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        def row(n: NomineeTally) -> dict[str, Any]:
            return {
                'nominee_id': n.nominee_id,
                'selected_person_id': n.selected_person_id,
                'display_name': n.display_name,
                'score': str(n.score),
                'exec_votes': n.exec_votes,
                'staff_votes': n.staff_votes,
                'total_votes': n.total_votes,
                'is_winner': n.is_winner,
                'is_tie': n.is_tie,
            }

        return {
            'award_id': self.award_id,
            'award_slug': self.award_slug,
            'voting_mode': self.voting_mode,
            'eligible_exec_count': self.eligible_exec_count,
            'nominees': [row(n) for n in self.nominees],
            'winners': [row(n) for n in self.winners],
        }


def _as_decimal(value) -> Decimal:
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def tally_award(award: Award) -> AwardTallyResult:
    if award.voting_mode == Award.VotingMode.WEIGHTED:
        return _tally_weighted(award)
    return _tally_simple(award)


def _mark_winners(rows: list[NomineeTally], *, use_exec_tiebreak: bool) -> list[NomineeTally]:
    if not rows:
        return []

    best = rows[0]
    contenders = [best]
    for row in rows[1:]:
        if row.score < best.score:
            break
        if row.score > best.score:
            best = row
            contenders = [row]
            continue
        # equal score
        if use_exec_tiebreak:
            if row.exec_votes > best.exec_votes:
                best = row
                contenders = [row]
            elif row.exec_votes == best.exec_votes:
                if row.staff_votes > best.staff_votes:
                    best = row
                    contenders = [row]
                elif row.staff_votes == best.staff_votes:
                    contenders.append(row)
        else:
            contenders.append(row)

    tied = len(contenders) > 1
    for c in contenders:
        c.is_winner = True
        c.is_tie = tied
    return contenders


def _tally_weighted(award: Award) -> AwardTallyResult:
    eligible_execs = eligible_executives_for_award(award)
    e_count = eligible_execs.count()
    exec_weight = _as_decimal(award.executive_weight)
    staff_weight = _as_decimal(award.staff_weight)

    # PDF spirit: each exec vote worth executive_weight / E_eligible.
    # If E=0, exec share is 0 (avoid division by zero).
    exec_vote_value = (exec_weight / Decimal(e_count)) if e_count else ZERO

    nominees = list(
        Nominee.objects.filter(award=award, is_confirmed=True).order_by('sort_order', 'id')
    )
    votes = list(
        Vote.objects.filter(award=award, nominee__isnull=False).select_related('nominee')
    )

    staff_votes_by_nominee: dict[int, int] = {n.id: 0 for n in nominees}
    exec_votes_by_nominee: dict[int, int] = {n.id: 0 for n in nominees}
    total_staff_votes = 0

    for vote in votes:
        nid = vote.nominee_id
        if nid not in staff_votes_by_nominee:
            continue
        if vote.electorate_at_vote == OrgPerson.Electorate.EXECUTIVE:
            exec_votes_by_nominee[nid] += 1
        else:
            staff_votes_by_nominee[nid] += 1
            total_staff_votes += 1

    rows: list[NomineeTally] = []
    for nominee in nominees:
        exec_v = exec_votes_by_nominee[nominee.id]
        staff_v = staff_votes_by_nominee[nominee.id]
        exec_share = exec_vote_value * Decimal(exec_v)
        if total_staff_votes:
            staff_share = (Decimal(staff_v) / Decimal(total_staff_votes)) * staff_weight
        else:
            staff_share = ZERO
        score = exec_share + staff_share
        rows.append(
            NomineeTally(
                nominee_id=nominee.id,
                selected_person_id=None,
                display_name=nominee.display_name,
                score=score,
                exec_votes=exec_v,
                staff_votes=staff_v,
                total_votes=exec_v + staff_v,
            )
        )

    rows.sort(key=lambda r: (r.score, r.exec_votes, r.staff_votes), reverse=True)
    winners = _mark_winners(rows, use_exec_tiebreak=True)

    return AwardTallyResult(
        award_id=award.id,
        award_slug=award.slug,
        voting_mode=award.voting_mode,
        eligible_exec_count=e_count,
        nominees=rows,
        winners=winners,
    )


def _tally_simple(award: Award) -> AwardTallyResult:
    """staff_shortlist / staff_open — highest vote count wins."""
    e_count = eligible_executives_for_award(award).count()

    if award.voting_mode == Award.VotingMode.STAFF_OPEN:
        # Aggregate by selected_person
        counts = (
            Vote.objects.filter(award=award, selected_person__isnull=False)
            .values('selected_person_id', 'selected_person__first_name', 'selected_person__last_name')
            .annotate(total=Count('id'))
            .order_by('-total', 'selected_person_id')
        )
        rows = [
            NomineeTally(
                nominee_id=None,
                selected_person_id=row['selected_person_id'],
                display_name=f"{row['selected_person__first_name']} {row['selected_person__last_name']}".strip(),
                score=Decimal(row['total']),
                total_votes=row['total'],
                staff_votes=row['total'],
            )
            for row in counts
        ]
    else:
        nominees = list(
            Nominee.objects.filter(award=award, is_confirmed=True).order_by('sort_order', 'id')
        )
        vote_counts = dict(
            Vote.objects.filter(award=award, nominee__isnull=False)
            .values('nominee_id')
            .annotate(c=Count('id'))
            .values_list('nominee_id', 'c')
        )
        rows = [
            NomineeTally(
                nominee_id=n.id,
                selected_person_id=None,
                display_name=n.display_name,
                score=Decimal(vote_counts.get(n.id, 0)),
                total_votes=vote_counts.get(n.id, 0),
                staff_votes=vote_counts.get(n.id, 0),
            )
            for n in nominees
        ]
        rows.sort(key=lambda r: (r.score, r.nominee_id or 0), reverse=True)

    winners = _mark_winners(rows, use_exec_tiebreak=False)
    return AwardTallyResult(
        award_id=award.id,
        award_slug=award.slug,
        voting_mode=award.voting_mode,
        eligible_exec_count=e_count,
        nominees=rows,
        winners=winners,
    )


def tally_year(year) -> list[AwardTallyResult]:
    awards = Award.objects.filter(year=year, is_active=True).order_by('sort_order', 'name')
    return [tally_award(a) for a in awards]
