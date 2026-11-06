"""
Deterministic fake org-directory users for local development.

Served by GET /api/v1/external/users when DEV_ORG_USERS_ENABLED=True.
Same path + Bearer auth as production; shape matches OrgUsersClient / sync.
"""

from __future__ import annotations

from typing import Any


def build_dev_org_users() -> list[dict[str, Any]]:
    """Return 15 portal-shaped user dicts covering Tourism, Global, exec, and edge cases."""
    users: list[dict[str, Any]] = [
        # Tourism staff
        _u(1, 'ada', 'Okoro', 'TOURISM', 'STAFF', 'Tourism'),
        _u(2, 'ben', 'Adeyemi', 'TOURISM', 'STAFF', 'Tourism'),
        _u(3, 'chioma', 'Eze', 'TOURISM', 'STAFF', 'Tourism'),
        _u(4, 'david', 'Bello', 'TOURISM', 'STAFF', 'Tourism'),
        _u(5, 'esther', 'Nwosu', 'INTERNAL_CONTROL', 'STAFF', 'Internal Control',
           unit='Tourism Internal Control'),
        # Tourism executive
        _u(6, 'funke', 'Adewale', 'TOURISM', 'ED', 'Executive Director'),
        # Global staff
        _u(7, 'gabriel', 'Ibrahim', 'HR', 'STAFF', 'HR'),
        _u(8, 'halima', 'Yusuf', 'IT', 'STAFF', 'IT'),
        _u(9, 'ifeanyi', 'Okafor', 'ACCOUNTS', 'STAFF', 'Accounts'),
        _u(10, 'joyce', 'Mensah', 'EXPORT', 'STAFF', 'Export'),
        _u(11, 'kunle', 'Adebayo', 'TRADING', 'STAFF', 'Trading'),
        # Global executive
        _u(12, 'lola', 'Banjo', 'HR', 'MD', 'Managing Director'),
        # Edge cases (no ballot tokens)
        _u(13, 'musa', 'Ali', 'TOURISM_DUBAI', 'STAFF', 'Tourism Dubai'),
        _u(14, 'ngozi', 'Uche', 'IT', 'INTERN', 'Intern'),
        # Extra Tourism staff
        _u(15, 'oscar', 'James', 'TOURISM', 'STAFF', 'Tourism'),
    ]
    return users


def _u(
    uid: int,
    first: str,
    last: str,
    dept: str,
    role: str,
    role_name: str,
    *,
    unit: str | None = None,
    active: bool = True,
) -> dict[str, Any]:
    return {
        'id': uid,
        'email': f'{first}.{last.lower()}@incelgroup.com',
        'first_name': first.title(),
        'last_name': last,
        'is_active': active,
        'role_code': role,
        'role_name': role_name,
        'department_code': dept,
        'department_name': role_name if dept == 'TOURISM_DUBAI' else dept.replace('_', ' ').title(),
        'unit_name': unit,
    }
