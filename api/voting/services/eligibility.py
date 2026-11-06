"""
Award-division gating for ballots and tallies.

| award.division | Who may vote                                      |
|----------------|---------------------------------------------------|
| tourism        | Nigeria-eligible AND company = tourism            |
| global         | Nigeria-eligible AND company = global             |
| shared         | All Nigeria-eligible voters                       |

Dubai / ineligible electorate are excluded via is_nigeria_eligible / electorate.
"""

from __future__ import annotations

from awards.models import Award
from people.models import OrgPerson


def person_may_vote_on_award(person: OrgPerson, award: Award) -> bool:
    """Return True if this voter is allowed to cast a ballot for the award."""
    if not person.is_nigeria_eligible:
        return False
    if person.electorate not in (
        OrgPerson.Electorate.STAFF,
        OrgPerson.Electorate.EXECUTIVE,
    ):
        return False
    if not award.is_active:
        return False

    division = award.division
    if division == Award.Division.SHARED:
        return True
    if division == Award.Division.TOURISM:
        return person.company == OrgPerson.Company.TOURISM
    if division == Award.Division.GLOBAL:
        return person.company == OrgPerson.Company.GLOBAL
    return False


def awards_for_voter(person: OrgPerson, year):
    """Active awards in `year` that this person may vote on."""
    from awards.models import Award as AwardModel

    qs = AwardModel.objects.filter(year=year, is_active=True).order_by('sort_order', 'name')
    return [a for a in qs if person_may_vote_on_award(person, a)]


def eligible_executives_for_award(award: Award):
    """
    Nigeria-eligible executives whose company may vote on this award.

    Used as E in weighted tallies (not hardcoded 2).
    """
    qs = OrgPerson.objects.filter(
        is_active=True,
        is_nigeria_eligible=True,
        electorate=OrgPerson.Electorate.EXECUTIVE,
    )
    if award.division == Award.Division.TOURISM:
        qs = qs.filter(company=OrgPerson.Company.TOURISM)
    elif award.division == Award.Division.GLOBAL:
        qs = qs.filter(company=OrgPerson.Company.GLOBAL)
    # shared: all nigeria-eligible executives
    return qs
