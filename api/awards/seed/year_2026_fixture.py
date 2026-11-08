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
    AwardNotificationConfig,
    AwardYear,
    Nominee,
)

YEAR = 2026

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
    ('Decorum and comportment', Decimal('15')),
    ('Communication', Decimal('10')),
]

ROOKIE_CRITERIA = [
    ('Quality of work', Decimal('30')),
    ('Learning ability', Decimal('20')),
    ('Role mastery', Decimal('20')),
    ('Team player and proactive initiative', Decimal('20')),
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
    ('Influence without formal authority', Decimal('30')),
    ('Initiative and ownership', Decimal('20')),
    ('Guidance and support to colleagues', Decimal('20')),
    ('Reliability and leading by example', Decimal('15')),
    ('Collaboration and culture', Decimal('15')),
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
        'description': (
            "This award recognises the individual employee whose performance and "
            "reliability stood out above everyone else's."
        ),
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
        ),
    },
    {
        'slug': 'employee-of-the-year-global',
        'name': 'Employee of the Year (Global)',
        'description': (
            "This award recognises the individual employee whose performance and "
            "reliability stood out above everyone else's."
        ),
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
        ),
    },
    {
        'slug': 'supervisor-of-the-year-tourism',
        'name': 'Supervisor of the Year (Tourism)',
        'description': (
            'This award recognises the supervisor who led, developed and got the '
            'most out of their team this year.'
        ),
        'division': Award.Division.TOURISM,
        'voting_mode': Award.VotingMode.WEIGHTED,
        'executive_weight': Decimal('0.60'),
        'staff_weight': Decimal('0.40'),
        'sort_order': 30,
        'criteria': SUPERVISOR_CRITERIA,
        'nominees': _people(
            'Tourism Supervisor A',
            'Tourism Supervisor B',
            'Tourism Supervisor C',
            'Tourism Supervisor D',
        ),
    },
    {
        'slug': 'supervisor-of-the-year-global',
        'name': 'Supervisor of the Year (Global)',
        'description': (
            'This award recognises the supervisor who led, developed and got the '
            'most out of their team this year.'
        ),
        'division': Award.Division.GLOBAL,
        'voting_mode': Award.VotingMode.WEIGHTED,
        'executive_weight': Decimal('0.60'),
        'staff_weight': Decimal('0.40'),
        'sort_order': 40,
        'criteria': SUPERVISOR_CRITERIA,
        'nominees': _people(
            'Global Supervisor A',
            'Global Supervisor B',
            'Global Supervisor C',
            'Global Supervisor D',
        ),
    },
    {
        'slug': 'department-of-the-year-tourism',
        'name': 'Department of the Year (Tourism)',
        'description': (
            'This award recognises the department that delivered the strongest '
            'collective results and the best teamwork.'
        ),
        'division': Award.Division.TOURISM,
        'voting_mode': Award.VotingMode.WEIGHTED,
        'executive_weight': Decimal('0.50'),
        'staff_weight': Decimal('0.50'),
        'sort_order': 50,
        'criteria': DEPARTMENT_CRITERIA,
        'nominees': _departments(
            'Operations',
            'Sales',
            'Brands and Marketing',
            'Internal Control and Risk',
            'Accounts',
        ),
    },
    {
        'slug': 'department-of-the-year-global',
        'name': 'Department of the Year (Global)',
        'description': (
            'This award recognises the department that delivered the strongest '
            'collective results and the best teamwork.'
        ),
        'division': Award.Division.GLOBAL,
        'voting_mode': Award.VotingMode.WEIGHTED,
        'executive_weight': Decimal('0.50'),
        'staff_weight': Decimal('0.50'),
        'sort_order': 60,
        'criteria': DEPARTMENT_CRITERIA,
        'nominees': _departments(
            'Transaction Processing',
            'HR and Admin',
            'Internal Control and Audit',
            'IT',
            'Export (Flexus)',
            'Accounts',
        ),
    },
    {
        'slug': 'rookie-of-the-year',
        'name': 'Rookie of the Year',
        'description': (
            'This award recognises the standout newcomer, under one year in, who made '
            'the fastest and biggest impact.'
        ),
        'division': Award.Division.SHARED,
        'voting_mode': Award.VotingMode.STAFF_SHORTLIST,
        'executive_weight': None,
        'staff_weight': None,
        'sort_order': 70,
        'criteria': ROOKIE_CRITERIA,
        'nominees': _people(
            'Rookie Nominee A',
            'Rookie Nominee B',
            'Rookie Nominee C',
            'Rookie Nominee D',
        ),
    },
    {
        'slug': 'pioneer-award-for-innovation',
        'name': 'Pioneer Award for Innovation',
        'description': (
            'This award recognises the staff member whose idea or initiative delivered '
            'a genuine improvement for the companies.'
        ),
        'division': Award.Division.SHARED,
        'voting_mode': Award.VotingMode.STAFF_SHORTLIST,
        'executive_weight': None,
        'staff_weight': None,
        'sort_order': 80,
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
        'description': (
            'This award recognises the staff member who consistently sets the standard '
            'for professional dressing.'
        ),
        'division': Award.Division.SHARED,
        'voting_mode': Award.VotingMode.STAFF_SHORTLIST,
        'executive_weight': None,
        'staff_weight': None,
        'sort_order': 90,
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
        'description': (
            'This award recognises the staff member who consistently sets the standard '
            'for professional dressing.'
        ),
        'division': Award.Division.SHARED,
        'voting_mode': Award.VotingMode.STAFF_SHORTLIST,
        'executive_weight': None,
        'staff_weight': None,
        'sort_order': 100,
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
        'description': (
            'This award recognises the staff member who stays composed, calm and sharp '
            'when the pressure is highest. High delivery of work is a key requirement.'
        ),
        'division': Award.Division.SHARED,
        'voting_mode': Award.VotingMode.STAFF_SHORTLIST,
        'executive_weight': None,
        'staff_weight': None,
        'sort_order': 110,
        'criteria': STEEZE_CRITERIA,
        'nominees': _people(
            'Steeze Nominee A',
            'Steeze Nominee B',
            'Steeze Nominee C',
            'Steeze Nominee D',
        ),
    },
    {
        'slug': 'excellent-leadership-award',
        'name': 'Excellent Leadership Award',
        'description': (
            'This award recognises staff who hold no official leadership title but lead '
            'in practice: colleagues others turn to, who step up, guide teammates and move '
            'work forward without being asked. Supervisors and other formal team leads are '
            'not eligible.'
        ),
        'division': Award.Division.SHARED,
        'voting_mode': Award.VotingMode.STAFF_SHORTLIST,
        'executive_weight': None,
        'staff_weight': None,
        'sort_order': 120,
        'criteria': LEADERSHIP_CRITERIA,
        'nominees': _people(
            'Leadership Nominee A',
            'Leadership Nominee B',
            'Leadership Nominee C',
            'Leadership Nominee D',
        ),
    },
    {
        'slug': 'foodie-of-the-year',
        'name': 'Foodie of the Year',
        'description': (
            'Foodie of the Year recognises the staff member most enthusiastic about food '
            'at work, from potlucks to lunch runs.'
        ),
        'division': Award.Division.SHARED,
        'voting_mode': Award.VotingMode.STAFF_OPEN,
        'executive_weight': None,
        'staff_weight': None,
        'sort_order': 130,
        'criteria': [],
        'nominees': [],
    },
    {
        'slug': 'employees-choice-of-the-year',
        'name': "Employees' Choice of the Year",
        'description': (
            "Employees' Choice of the Year recognises the colleague staff most enjoy "
            "working with and is decided purely by popular vote, with no scored criteria."
        ),
        'division': Award.Division.SHARED,
        'voting_mode': Award.VotingMode.STAFF_OPEN,
        'executive_weight': None,
        'staff_weight': None,
        'sort_order': 140,
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

    notification_specs = (
        {
            'event': AwardNotificationConfig.Event.ELIGIBILITY_NOTICE,
            'offset_minutes_before_open': 10,
            'offset_minutes_before_close': 0,
            'subject_template': (
                "You're eligible to vote — Incel Employee Awards {year}"
            ),
        },
        {
            'event': AwardNotificationConfig.Event.VOTE_INVITE,
            'offset_minutes_before_open': 60,
            'offset_minutes_before_close': 0,
            'subject_template': 'Cast your vote — Incel Employee Awards {year}',
        },
        {
            'event': AwardNotificationConfig.Event.VOTING_OPENED,
            'offset_minutes_before_open': 0,
            'offset_minutes_before_close': 0,
            'subject_template': 'Voting is open — Incel Employee Awards {year}',
        },
        {
            'event': AwardNotificationConfig.Event.VOTING_CLOSING_REMINDER,
            'offset_minutes_before_open': 0,
            'offset_minutes_before_close': 60,
            'subject_template': (
                'Reminder: voting closes soon — Incel Employee Awards {year}'
            ),
        },
        {
            'event': AwardNotificationConfig.Event.VOTING_CLOSED,
            'offset_minutes_before_open': 0,
            'offset_minutes_before_close': 0,
            'subject_template': 'Voting has closed — Incel Employee Awards {year}',
        },
    )
    for spec in notification_specs:
        AwardNotificationConfig.objects.update_or_create(
            year=year,
            event=spec['event'],
            defaults={
                'enabled': True,
                'channel': AwardNotificationConfig.Channel.EMAIL,
                'audience': AwardNotificationConfig.Audience.ALL_ELIGIBLE,
                'offset_minutes_before_open': spec['offset_minutes_before_open'],
                'offset_minutes_before_close': spec['offset_minutes_before_close'],
                'subject_template': spec['subject_template'],
                'extra': {},
            },
        )

    for spec in catalogue:
        award, _ = Award.objects.update_or_create(
            year=year,
            slug=spec['slug'],
            defaults={
                'name': spec['name'],
                'description': spec['description'],
                'division': spec['division'],
                'voting_mode': spec['voting_mode'],
                'executive_weight': spec['executive_weight'],
                'staff_weight': spec['staff_weight'],
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
