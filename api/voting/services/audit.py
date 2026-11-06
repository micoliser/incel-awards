"""
Committee-only voting audit report.

Includes season summary, per-award calculation detail (especially weighted),
and every ballot cast. Never expose via the public results endpoint.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db.models import Prefetch

from awards.models import Award, AwardYear, Nominee
from people.models import OrgPerson
from voting.models import BallotToken, Vote, VoteAuditLog
from voting.services.eligibility import eligible_executives_for_award
from voting.services.tally import ZERO, _as_decimal, tally_award


def _pct(value: Decimal) -> str:
    return f'{value * Decimal("100"):.2f}%'


def _dec_str(value: Decimal) -> str:
    return format(value, 'f')


def build_year_audit(year: AwardYear) -> dict[str, Any]:
    awards = list(
        Award.objects.filter(year=year, is_active=True)
        .prefetch_related(
            Prefetch(
                'nominees',
                queryset=Nominee.objects.filter(is_confirmed=True).order_by(
                    'sort_order', 'id'
                ),
            )
        )
        .order_by('sort_order', 'name')
    )

    tokens = BallotToken.objects.filter(year=year)
    ballots_issued = tokens.count()
    ballots_revoked = tokens.filter(revoked_at__isnull=False).count()

    all_votes = (
        Vote.objects.filter(award__year=year)
        .select_related(
            'voter',
            'nominee',
            'selected_person',
            'award',
        )
        .order_by('award__sort_order', 'award_id', 'voter__last_name', 'voter__first_name')
    )
    votes_list = list(all_votes)
    unique_voters = {v.voter_id for v in votes_list}
    voters_who_voted = len(unique_voters)

    award_reports = [_award_audit(award, votes_list) for award in awards]

    return {
        'year': year.year,
        'title': year.title,
        'status': year.status,
        'voting_opens_at': year.voting_opens_at,
        'voting_closes_at': year.voting_closes_at,
        'results_published_at': year.results_published_at,
        'summary': {
            'awards_count': len(awards),
            'ballots_issued': ballots_issued,
            'ballots_revoked': ballots_revoked,
            'ballots_active': ballots_issued - ballots_revoked,
            'unique_voters': voters_who_voted,
            'total_votes_cast': len(votes_list),
            'participation_rate': (
                _dec_str(
                    Decimal(voters_who_voted)
                    / Decimal(max(ballots_issued - ballots_revoked, 1))
                )
                if (ballots_issued - ballots_revoked) > 0
                else '0'
            ),
            'weighted_awards': sum(
                1 for a in awards if a.voting_mode == Award.VotingMode.WEIGHTED
            ),
            'shortlist_awards': sum(
                1 for a in awards if a.voting_mode == Award.VotingMode.STAFF_SHORTLIST
            ),
            'open_awards': sum(
                1 for a in awards if a.voting_mode == Award.VotingMode.STAFF_OPEN
            ),
        },
        'methodology': {
            'weighted': {
                'title': 'Weighted awards (Employee / Supervisor / Department)',
                'steps': [
                    'E = count of Nigeria-eligible executives allowed to vote on this award (division-gated).',
                    'Each executive ballot is worth executive_weight / E.',
                    'Nominee executive share = (executive_weight / E) × executive votes for that nominee.',
                    'Nominee staff share = (nominee staff votes ÷ total staff votes cast) × staff_weight. If no staff votes, staff share = 0.',
                    'Final score = executive share + staff share.',
                    'Winner = highest final score. Tie-break: more executive votes, then more staff votes; otherwise leave as a committee tie.',
                ],
                'note': (
                    'Executives who did not cast a ballot still count in E for per-vote value. '
                    'Staff and executive votes are snapshotted via electorate_at_vote on each Vote row.'
                ),
            },
            'staff_shortlist': {
                'title': 'Staff shortlist',
                'steps': [
                    'Each eligible voter casts one ballot for a confirmed nominee.',
                    'Winner = highest vote count. Equal counts remain a tie for committee review.',
                    'Executive ballots count the same as staff (no extra weight).',
                ],
            },
            'staff_open': {
                'title': 'Open popular vote',
                'steps': [
                    'Each eligible voter picks any Nigeria-eligible colleague from the directory.',
                    'Winner = highest vote count. Equal counts remain a tie.',
                ],
            },
        },
        'awards': award_reports,
    }


def _award_audit(award: Award, year_votes: list[Vote]) -> dict[str, Any]:
    tally = tally_award(award)
    award_votes = [v for v in year_votes if v.award_id == award.id]

    e_count = tally.eligible_exec_count
    exec_weight = _as_decimal(award.executive_weight)
    staff_weight = _as_decimal(award.staff_weight)
    exec_vote_value = (exec_weight / Decimal(e_count)) if e_count else ZERO

    total_staff_votes = sum(
        1
        for v in award_votes
        if v.electorate_at_vote != OrgPerson.Electorate.EXECUTIVE
    )
    total_exec_votes = sum(
        1
        for v in award_votes
        if v.electorate_at_vote == OrgPerson.Electorate.EXECUTIVE
    )

    eligible_execs = list(
        eligible_executives_for_award(award).order_by('last_name', 'first_name')
    )
    exec_who_voted = {
        v.voter_id
        for v in award_votes
        if v.electorate_at_vote == OrgPerson.Electorate.EXECUTIVE
    }

    nominee_rows: list[dict[str, Any]] = []
    for row in tally.nominees:
        exec_share = ZERO
        staff_share = ZERO
        if award.voting_mode == Award.VotingMode.WEIGHTED:
            exec_share = exec_vote_value * Decimal(row.exec_votes)
            if total_staff_votes:
                staff_share = (
                    Decimal(row.staff_votes) / Decimal(total_staff_votes)
                ) * staff_weight
            formula = (
                f'({_dec_str(exec_weight)} / {e_count}) × {row.exec_votes} exec'
                f' + ({row.staff_votes}/{total_staff_votes or 0}) × {_dec_str(staff_weight)} staff'
                f' = {_dec_str(exec_share)} + {_dec_str(staff_share)} = {_dec_str(row.score)}'
            )
        else:
            formula = f'{row.total_votes} ballot(s) → score {_dec_str(row.score)}'

        nominee_rows.append({
            'nominee_id': row.nominee_id,
            'selected_person_id': row.selected_person_id,
            'display_name': row.display_name,
            'exec_votes': row.exec_votes,
            'staff_votes': row.staff_votes,
            'total_votes': row.total_votes,
            'exec_share': _dec_str(exec_share),
            'staff_share': _dec_str(staff_share),
            'score': _dec_str(row.score),
            'score_display': (
                _pct(row.score)
                if award.voting_mode == Award.VotingMode.WEIGHTED
                else str(row.total_votes)
            ),
            'formula': formula,
            'is_winner': row.is_winner,
            'is_tie': row.is_tie,
        })

    ballots = []
    for vote in award_votes:
        if vote.nominee_id:
            choice = vote.nominee.display_name if vote.nominee else f'nominee:{vote.nominee_id}'
            choice_kind = 'nominee'
        else:
            person = vote.selected_person
            choice = person.display_name if person else f'person:{vote.selected_person_id}'
            choice_kind = 'open_person'
        ballots.append({
            'voter_id': vote.voter_id,
            'voter_name': vote.voter.display_name,
            'voter_email': vote.voter.email,
            'voter_company': vote.voter.company,
            'voter_department': vote.voter.department_name or vote.voter.department_code,
            'electorate_at_vote': vote.electorate_at_vote,
            'choice_kind': choice_kind,
            'choice_name': choice,
            'nominee_id': vote.nominee_id,
            'selected_person_id': vote.selected_person_id,
            'created_at': vote.created_at,
            'updated_at': vote.updated_at,
            'was_changed': vote.created_at != vote.updated_at,
        })

    audit_logs = list(
        VoteAuditLog.objects.filter(award=award)
        .select_related(
            'voter',
            'previous_nominee',
            'new_nominee',
            'previous_selected_person',
            'new_selected_person',
        )
        .order_by('-created_at')[:200]
    )
    log_rows = []
    for log in audit_logs:
        log_rows.append({
            'action': log.action,
            'voter_name': log.voter.display_name if log.voter_id else '',
            'voter_email': log.voter.email if log.voter_id else '',
            'previous': _audit_choice_label(
                log.previous_nominee, log.previous_selected_person
            ),
            'new': _audit_choice_label(log.new_nominee, log.new_selected_person),
            'created_at': log.created_at,
        })

    calculation = None
    if award.voting_mode == Award.VotingMode.WEIGHTED:
        calculation = {
            'executive_weight': _dec_str(exec_weight),
            'staff_weight': _dec_str(staff_weight),
            'eligible_exec_count': e_count,
            'exec_vote_value': _dec_str(exec_vote_value),
            'exec_vote_value_display': _pct(exec_vote_value) if e_count else '0%',
            'total_exec_votes_cast': total_exec_votes,
            'total_staff_votes_cast': total_staff_votes,
            'eligible_executives': [
                {
                    'id': p.id,
                    'name': p.display_name,
                    'email': p.email,
                    'voted': p.id in exec_who_voted,
                }
                for p in eligible_execs
            ],
            'worked_example': (
                f'Each exec vote worth {_dec_str(exec_weight)}/{e_count} = {_dec_str(exec_vote_value)} '
                f'({_pct(exec_vote_value)} of the final score). '
                f'Staff pool is {_dec_str(staff_weight)} ({_pct(staff_weight)}) split by share of '
                f'{total_staff_votes} staff ballot(s) cast.'
            ),
        }
    else:
        calculation = {
            'executive_weight': None,
            'staff_weight': None,
            'eligible_exec_count': e_count,
            'total_votes_cast': len(award_votes),
            'note': 'Simple plurality: one ballot = one count. No executive weighting.',
        }

    return {
        'award_id': award.id,
        'award_slug': award.slug,
        'award_name': award.name,
        'division': award.division,
        'voting_mode': award.voting_mode,
        'description': award.description,
        'votes_cast': len(award_votes),
        'calculation': calculation,
        'nominees': nominee_rows,
        'winners': [n for n in nominee_rows if n['is_winner']],
        'ballots': ballots,
        'vote_changes': log_rows,
    }


def _audit_choice_label(nominee, selected_person) -> str:
    if nominee is not None:
        return nominee.display_name
    if selected_person is not None:
        return selected_person.display_name
    return '—'
