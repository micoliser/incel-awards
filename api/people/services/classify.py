"""
Org-person classification for Nigeria awards eligibility.

Rules (docs/domain-rules.md):
- Nigeria eligible: active AND department_code != TOURISM_DUBAI
- Company tourism if Tourism dept or Tourism IC / Tourism Accounts units
- Electorate: ED/MD → executive; STAFF → staff; else ineligible
"""

from __future__ import annotations

from typing import Literal, Protocol

DUBAI_DEPARTMENT = 'TOURISM_DUBAI'
TOURISM_DEPARTMENT = 'TOURISM'
EXEC_ROLE_CODES = frozenset({'ED', 'MD'})
STAFF_ROLE_CODES = frozenset({'STAFF'})

TOURISM_UNIT_EXCEPTIONS = frozenset({
    ('INTERNAL_CONTROL', 'Tourism Internal Control'),
    ('TRADING', 'Tourism Accounts'),
})

CompanyLabel = Literal['tourism', 'global', 'excluded']
ElectorateLabel = Literal['staff', 'executive', 'ineligible']


class PersonLike(Protocol):
    is_active: bool
    department_code: str
    unit_name: str | None
    role_code: str


def is_nigeria_eligible(person: PersonLike) -> bool:
    """Whether the person may vote / appear on open-award directories."""
    if not person.is_active:
        return False
    return (person.department_code or '') != DUBAI_DEPARTMENT


def resolve_company(person: PersonLike) -> CompanyLabel:
    """
    tourism | global among Nigeria-eligible people; excluded otherwise.

    Tourism exceptions:
    - INTERNAL_CONTROL + unit Tourism Internal Control
    - TRADING + unit Tourism Accounts
    """
    if not is_nigeria_eligible(person):
        return 'excluded'

    dept = person.department_code or ''
    unit = person.unit_name or ''

    if dept == TOURISM_DEPARTMENT:
        return 'tourism'
    if (dept, unit) in TOURISM_UNIT_EXCEPTIONS:
        return 'tourism'
    return 'global'


def resolve_electorate(person: PersonLike) -> ElectorateLabel:
    role = (person.role_code or '').upper()
    if role in EXEC_ROLE_CODES:
        return 'executive'
    if role in STAFF_ROLE_CODES:
        return 'staff'
    return 'ineligible'


def apply_classification(person) -> None:
    """Mutate an OrgPerson (or similar) with cached classification fields."""
    person.is_nigeria_eligible = is_nigeria_eligible(person)
    person.company = resolve_company(person)
    person.electorate = resolve_electorate(person)
