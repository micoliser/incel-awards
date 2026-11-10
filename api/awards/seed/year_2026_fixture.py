"""
Public 2026 awards catalogue + seed helpers.

Safe to commit: award structure, criteria, and placeholder nominees only.
Real committee nominees live in the gitignored ``year_2026`` overlay when present.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from awards.models import (
    Award,
    AwardCriterion,
    AwardYear,
    Nominee,
)
from awards.notification_defaults import ensure_default_notification_configs

YEAR = 2026


def _ideal(*lines: str) -> str:
    """Store ideal-winner traits as one line each (UI renders as a list)."""
    return '\n'.join(lines)


# About + ideal winner copy from Awards_Shortlist_Review_2026.pptx
EMPLOYEE_ABOUT = (
    "This award recognises the individual employee whose performance and "
    "reliability stood out above everyone else's. It celebrates someone who "
    "consistently delivers, can be depended on and lifts the team around them."
)
EMPLOYEE_IDEAL = _ideal(
    'Consistently delivers exceptional results',
    'Is reliable and dependable',
    'Collaborates well with the team',
    'Shows integrity and a good attitude to work',
)

DEPARTMENT_ABOUT = (
    'This award recognises the department that delivered the strongest '
    'collective results and the best teamwork. It celebrates collective '
    'achievement across the department, not the performance of an '
    'individual department head. All Nigeria-eligible staff and executives '
    'vote on both Tourism and Global lists.'
)
DEPARTMENT_IDEAL = _ideal(
    'Delivers strong collective results',
    'Works well with other departments',
    'Improves processes through innovation',
    'Upholds decorum and communicates well',
)

ROOKIE_ABOUT = (
    'This award recognises the standout newcomer, under one year in, who made '
    'the fastest and biggest impact. It celebrates someone who settled in '
    'quickly, learned fast and delivered beyond what is expected for their '
    'experience. Eligibility (under one year in the organisation) has been '
    'confirmed.'
)
ROOKIE_IDEAL = _ideal(
    'Delivers high-quality work early',
    'Learns quickly and masters the role',
    'Is a proactive team player',
    'Fits into the company culture',
)

LEADERSHIP_ABOUT = (
    'This award recognises an individual who inspires, motivates and guides '
    'others towards organisational objectives. It celebrates a leader who leads '
    'by example and empowers others, rewarding effectiveness and positive '
    'influence rather than seniority or designation. Cash prize: ₦300,000. '
    'All Nigeria-eligible staff and executives vote on both Tourism and Global lists.'
)
LEADERSHIP_IDEAL = _ideal(
    'Leads by example with strong ethics',
    'Inspires, mentors and empowers others',
    'Promotes collaboration and a positive culture',
)

PIONEER_ABOUT = (
    'This award recognises the staff member whose idea or initiative delivered '
    'a genuine improvement for the companies. It celebrates original thinking '
    'that improved how the business operates, backed by problem-solving and '
    'good use of technology.'
)
PIONEER_IDEAL = _ideal(
    'Brings original ideas to the business',
    'Delivers measurable business improvement',
    'Takes initiative in solving problems',
    'Uses technology well to improve operations',
)

BEST_DRESSED_ABOUT = (
    'This award recognises the staff member who consistently sets the standard '
    'for professional dressing. It is given in two categories, male and female, '
    'and rewards a polished appearance that follows the office dress code, day '
    'after day.'
)
BEST_DRESSED_IDEAL = _ideal(
    'Looks professional and well put together',
    'Is neat and well groomed',
    'Dresses consistently, not just occasionally',
    'Shows style and elegance',
)

STEEZE_ABOUT = (
    'This award recognises the staff member who stays composed, calm and sharp '
    'when the pressure is highest. High delivery of work is a key requirement, '
    'so composure alone is not enough.'
)
STEEZE_IDEAL = _ideal(
    'Stays calm and in control in a crisis',
    'Makes decisive calls under pressure',
    'Reassures and de-escalates for the team',
    'Still delivers high-quality work',
)

FOODIE_ABOUT = (
    'Foodie of the Year recognises the staff member most enthusiastic about food '
    'at work, from potlucks to lunch runs.'
)

EMPLOYEES_CHOICE_ABOUT = (
    "Employees' Choice of the Year recognises the colleague staff most enjoy "
    'working with and is decided purely by popular vote, with no scored criteria.'
)

# Shared criteria templates (label, weight_percent)
EMPLOYEE_CRITERIA = [
    ('Job performance and consistency', Decimal('30')),
    ('Reliability and dependability', Decimal('20')),
    ('Team collaboration', Decimal('20')),
    ('Integrity and professionalism', Decimal('15')),
    ('Communication and attitude towards work', Decimal('15')),
]

SUPERVISOR_CRITERIA = [
    ('Leadership and team management', Decimal('30')),
    ('Team performance and results', Decimal('20')),
    ('Initiative and problem-solving', Decimal('20')),
    ('Communication and mentorship', Decimal('15')),
    ('Attendance, discipline and team satisfaction', Decimal('15')),
]

DEPARTMENT_CRITERIA = [
    ('Collective proficiency', Decimal('30')),
    ('Inter-departmental relations', Decimal('25')),
    ('Innovation', Decimal('20')),
    ('Decorum & comportment', Decimal('15')),
    ('Communication', Decimal('10')),
]

ROOKIE_CRITERIA = [
    ('Quality of work', Decimal('30')),
    ('Learning ability', Decimal('20')),
    ('Role mastery', Decimal('20')),
    ('Team player and initiative', Decimal('20')),
    ('Culture integration', Decimal('10')),
]

PIONEER_CRITERIA = [
    ('Innovation and originality', Decimal('30')),
    ('Impact on business improvement', Decimal('25')),
    ('Problem-solving and initiative', Decimal('20')),
    ('Operational improvement', Decimal('15')),
    ('Adaptability and use of technology', Decimal('10')),
]

BEST_DRESSED_CRITERIA = [
    ('Overall appearance', Decimal('25')),
    ('Professional dressing', Decimal('20')),
    ('Neatness and grooming', Decimal('20')),
    ('Consistency', Decimal('20')),
    ('Style and elegance', Decimal('15')),
]

STEEZE_CRITERIA = [
    ('Emotional regulation and crisis calm', Decimal('25')),
    ('Tactical decisiveness under fire', Decimal('25')),
    ('Executive presence and poise', Decimal('20')),
    ('Reassurance and de-escalation', Decimal('15')),
    ('Flawless high-stakes delivery', Decimal('15')),
]

LEADERSHIP_CRITERIA = [
    ('Leadership and ability to inspire', Decimal('25')),
    ('Strategic thinking and objectives', Decimal('20')),
    ('Integrity and ethical conduct', Decimal('20')),
    ('Team development and mentorship', Decimal('20')),
    ('Communication and collaboration', Decimal('15')),
]


def _people(*labels: str) -> list[dict[str, Any]]:
    return [
        {
            'display_name': label,
            'nominee_type': Nominee.NomineeType.PERSON,
            'basis_for_nomination': 'Placeholder nominee for tests and local demos.',
            'is_confirmed': True,
        }
        for label in labels
    ]


def _departments(*labels: str) -> list[dict[str, Any]]:
    return [
        {
            'display_name': label,
            'nominee_type': Nominee.NomineeType.DEPARTMENT,
            'basis_for_nomination': 'Placeholder department nominee for tests and local demos.',
            'is_confirmed': True,
        }
        for label in labels
    ]


# Award catalogue: slug → config (14 awards). Expected: 6 weighted + 6 shortlist + 2 open.
AWARDS = [
    {
        'slug': 'employee-of-the-year-tourism',
        'name': 'Employee of the Year (Tourism)',
        'description': EMPLOYEE_ABOUT,
        'ideal_winner': EMPLOYEE_IDEAL,
        'division': Award.Division.TOURISM,
        'voting_mode': Award.VotingMode.WEIGHTED,
        'executive_weight': Decimal('0.30'),
        'staff_weight': Decimal('0.70'),
        'sort_order': 10,
        'criteria': EMPLOYEE_CRITERIA,
        'nominees': _people(
            'Tourism Employee A',
            'Tourism Employee B',
            'Tourism Employee C',
            'Tourism Employee D',
            'Tourism Employee E',
        ),
    },
    {
        'slug': 'employee-of-the-year-global',
        'name': 'Employee of the Year (Global)',
        'description': EMPLOYEE_ABOUT,
        'ideal_winner': EMPLOYEE_IDEAL,
        'division': Award.Division.GLOBAL,
        'voting_mode': Award.VotingMode.WEIGHTED,
        'executive_weight': Decimal('0.30'),
        'staff_weight': Decimal('0.70'),
        'sort_order': 20,
        'criteria': EMPLOYEE_CRITERIA,
        'nominees': _people(
            'Global Employee A',
            'Global Employee B',
            'Global Employee C',
            'Global Employee D',
            'Global Employee E',
        ),
    },
    {
        'slug': 'department-of-the-year-tourism',
        'name': 'Department of the Year (Tourism)',
        'description': DEPARTMENT_ABOUT,
        'ideal_winner': DEPARTMENT_IDEAL,
        'division': Award.Division.TOURISM,
        'voting_mode': Award.VotingMode.WEIGHTED,
        'executive_weight': Decimal('0.50'),
        'staff_weight': Decimal('0.50'),
        'company_vote_gated': False,
        'sort_order': 30,
        'criteria': DEPARTMENT_CRITERIA,
        'nominees': _departments(
            'Brand & Marketing',
            'IT',
            'Admin',
            'Internal Control',
            'Operations',
        ),
    },
    {
        'slug': 'department-of-the-year-global',
        'name': 'Department of the Year (Global)',
        'description': DEPARTMENT_ABOUT,
        'ideal_winner': DEPARTMENT_IDEAL,
        'division': Award.Division.GLOBAL,
        'voting_mode': Award.VotingMode.WEIGHTED,
        'executive_weight': Decimal('0.50'),
        'staff_weight': Decimal('0.50'),
        'company_vote_gated': False,
        'sort_order': 40,
        'criteria': DEPARTMENT_CRITERIA,
        'nominees': _departments(
            'IT',
            'Admin',
            'Transaction Processing',
            'Accounts',
            'Flexxus',
        ),
    },
    {
        'slug': 'rookie-of-the-year-tourism',
        'name': 'Rookie of the Year (Tourism)',
        'description': (
            f'{ROOKIE_ABOUT} Tourism staff vote on this list.'
        ),
        'ideal_winner': ROOKIE_IDEAL,
        'division': Award.Division.TOURISM,
        'voting_mode': Award.VotingMode.STAFF_SHORTLIST,
        'executive_weight': None,
        'staff_weight': None,
        'sort_order': 50,
        'criteria': ROOKIE_CRITERIA,
        'nominees': _people(
            'Tourism Rookie A',
            'Tourism Rookie B',
            'Tourism Rookie C',
            'Tourism Rookie D',
        ),
    },
    {
        'slug': 'rookie-of-the-year-global',
        'name': 'Rookie of the Year (Global)',
        'description': (
            f'{ROOKIE_ABOUT} Global staff vote on this list.'
        ),
        'ideal_winner': ROOKIE_IDEAL,
        'division': Award.Division.GLOBAL,
        'voting_mode': Award.VotingMode.STAFF_SHORTLIST,
        'executive_weight': None,
        'staff_weight': None,
        'sort_order': 55,
        'criteria': ROOKIE_CRITERIA,
        'nominees': _people(
            'Global Rookie A',
            'Global Rookie B',
            'Global Rookie C',
            'Global Rookie D',
        ),
    },
    {
        'slug': 'pioneer-award-for-innovation',
        'name': 'Pioneer Award for Innovation',
        'description': PIONEER_ABOUT,
        'ideal_winner': PIONEER_IDEAL,
        'division': Award.Division.SHARED,
        'voting_mode': Award.VotingMode.STAFF_SHORTLIST,
        'executive_weight': None,
        'staff_weight': None,
        'sort_order': 60,
        'criteria': PIONEER_CRITERIA,
        'nominees': _people(
            'Pioneer Nominee A',
            'Pioneer Nominee B',
            'Pioneer Nominee C',
            'Pioneer Nominee D',
            'Pioneer Nominee E',
        ),
    },
    {
        'slug': 'best-dressed-male',
        'name': 'Best Dressed (Male)',
        'description': BEST_DRESSED_ABOUT,
        'ideal_winner': BEST_DRESSED_IDEAL,
        'division': Award.Division.SHARED,
        'voting_mode': Award.VotingMode.STAFF_SHORTLIST,
        'executive_weight': None,
        'staff_weight': None,
        'sort_order': 70,
        'criteria': BEST_DRESSED_CRITERIA,
        'nominees': _people(
            'Best Dressed Male A',
            'Best Dressed Male B',
            'Best Dressed Male C',
            'Best Dressed Male D',
        ),
    },
    {
        'slug': 'best-dressed-female',
        'name': 'Best Dressed (Female)',
        'description': BEST_DRESSED_ABOUT,
        'ideal_winner': BEST_DRESSED_IDEAL,
        'division': Award.Division.SHARED,
        'voting_mode': Award.VotingMode.STAFF_SHORTLIST,
        'executive_weight': None,
        'staff_weight': None,
        'sort_order': 80,
        'criteria': BEST_DRESSED_CRITERIA,
        'nominees': _people(
            'Best Dressed Female A',
            'Best Dressed Female B',
            'Best Dressed Female C',
            'Best Dressed Female D',
        ),
    },
    {
        'slug': 'steeze-under-pressure',
        'name': 'Steeze Under Pressure',
        'description': STEEZE_ABOUT,
        'ideal_winner': STEEZE_IDEAL,
        'division': Award.Division.SHARED,
        'voting_mode': Award.VotingMode.STAFF_SHORTLIST,
        'executive_weight': None,
        'staff_weight': None,
        'sort_order': 90,
        'criteria': STEEZE_CRITERIA,
        'nominees': _people(
            'Steeze Nominee A',
            'Steeze Nominee B',
            'Steeze Nominee C',
            'Steeze Nominee D',
        ),
    },
    {
        'slug': 'excellent-leadership-award-tourism',
        'name': 'Excellent Leadership Award (Tourism)',
        'description': LEADERSHIP_ABOUT,
        'ideal_winner': LEADERSHIP_IDEAL,
        'division': Award.Division.TOURISM,
        'voting_mode': Award.VotingMode.WEIGHTED,
        'executive_weight': Decimal('0.20'),
        'staff_weight': Decimal('0.80'),
        'company_vote_gated': False,
        'sort_order': 25,
        'criteria': LEADERSHIP_CRITERIA,
        'nominees': _people(
            'Benjamin Okoro',
            'Joy Nwaise',
            'Uche Maduka',
            'Marcathy Atsegbua',
            'Solomon Aneke',
        ),
    },
    {
        'slug': 'excellent-leadership-award-global',
        'name': 'Excellent Leadership Award (Global)',
        'description': LEADERSHIP_ABOUT,
        'ideal_winner': LEADERSHIP_IDEAL,
        'division': Award.Division.GLOBAL,
        'voting_mode': Award.VotingMode.WEIGHTED,
        'executive_weight': Decimal('0.20'),
        'staff_weight': Decimal('0.80'),
        'company_vote_gated': False,
        'sort_order': 28,
        'criteria': LEADERSHIP_CRITERIA,
        'nominees': _people(
            'Oluwaseun Agunkejoye',
            'Festus Adeoye',
            'Oyedeji Oyedokun',
            'Okechukwu Osademe',
            'Oluwaseyi Elias',
        ),
    },
    {
        'slug': 'foodie-of-the-year',
        'name': 'Foodie of the Year',
        'description': FOODIE_ABOUT,
        'ideal_winner': '',
        'division': Award.Division.SHARED,
        'voting_mode': Award.VotingMode.STAFF_OPEN,
        'executive_weight': None,
        'staff_weight': None,
        'sort_order': 120,
        'criteria': [],
        'nominees': [],
    },
    {
        'slug': 'employees-choice-of-the-year',
        'name': "Employees' Choice of the Year",
        'description': EMPLOYEES_CHOICE_ABOUT,
        'ideal_winner': '',
        'division': Award.Division.SHARED,
        'voting_mode': Award.VotingMode.STAFF_OPEN,
        'executive_weight': None,
        'staff_weight': None,
        'sort_order': 130,
        'criteria': [],
        'nominees': [],
    },
]


def _sync_criteria(award: Award, criteria: list[tuple[str, Decimal]]) -> None:
    keep_ids = []
    for order, (label, weight) in enumerate(criteria, start=1):
        obj, _ = AwardCriterion.objects.update_or_create(
            award=award,
            label=label,
            defaults={
                'weight_percent': weight,
                'sort_order': order,
            },
        )
        keep_ids.append(obj.pk)
    AwardCriterion.objects.filter(award=award).exclude(pk__in=keep_ids).delete()


def _sync_nominees(award: Award, nominees: list[dict]) -> None:
    keep_ids = []
    for order, data in enumerate(nominees, start=1):
        obj, _ = Nominee.objects.update_or_create(
            award=award,
            display_name=data['display_name'],
            defaults={
                'nominee_type': data.get('nominee_type', Nominee.NomineeType.PERSON),
                # Public lists show names only; keep justifications empty for a consistent UI.
                'justification': '',
                'basis_for_nomination': data.get('basis_for_nomination', ''),
                'is_confirmed': data.get('is_confirmed', True),
                'sort_order': order,
            },
        )
        keep_ids.append(obj.pk)
    Nominee.objects.filter(award=award).exclude(pk__in=keep_ids).delete()


def seed_year_2026(awards: list[dict] | None = None) -> AwardYear:
    """Create/update the 2026 season. Safe to re-run.

    Pass ``awards`` to seed a private nominee catalogue; defaults to the public fixture.
    """
    catalogue = awards if awards is not None else AWARDS
    year, _ = AwardYear.objects.update_or_create(
        year=YEAR,
        defaults={
            'title': 'Employee Awards 2026',
            'slug': str(YEAR),
            'status': AwardYear.Status.SCHEDULED,
            'description': (
                'Incel Group Employee Awards 2026 recognises outstanding people and teams '
                'across Tourism and Global. Nominees were finalised by the awards committee '
                'using committee ballots, HR evaluation data, and deliberation. Staff vote '
                'from personal ballot links when the window opens.'
            ),
        },
    )

    ensure_default_notification_configs(year)

    for spec in catalogue:
        award, _ = Award.objects.update_or_create(
            year=year,
            slug=spec['slug'],
            defaults={
                'name': spec['name'],
                'description': spec['description'],
                'ideal_winner': spec.get('ideal_winner', ''),
                'division': spec['division'],
                'voting_mode': spec['voting_mode'],
                'executive_weight': spec['executive_weight'],
                'staff_weight': spec['staff_weight'],
                'company_vote_gated': spec.get('company_vote_gated', True),
                'sort_order': spec['sort_order'],
                'is_active': True,
            },
        )
        _sync_criteria(award, spec.get('criteria') or [])
        _sync_nominees(award, spec.get('nominees') or [])

    Award.objects.filter(year=year).exclude(
        slug__in=[a['slug'] for a in catalogue]
    ).delete()

    return year
