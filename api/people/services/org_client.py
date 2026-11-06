"""
HTTP client for the company users (org directory) API.

Production call shape (parity with local fake API):

  GET {ORG_USERS_API_BASE_URL}/api/v1/external/users
  Authorization: Bearer {ORG_USERS_API_TOKEN}
  Accept: application/json

ORG_USERS_API_BASE_URL is the origin only (e.g. https://workspace.example.com
or http://127.0.0.1:8000). If the env value already ends with
/api/v1/external/users, it is used as-is.
"""

from __future__ import annotations

from typing import Any, Iterator

import requests
from django.conf import settings

EXTERNAL_USERS_PATH = '/api/v1/external/users'


class OrgUsersAPIError(Exception):
    """Raised when the org users API returns an unexpected response."""


class OrgUsersClient:
    """
    Fetch organization users from the external users API.

    Expected list payload shapes (any of):
    - bare list: [{...}, ...]
    - {"results": [...], "next": "..."}  (DRF-style pagination)
    - {"data": [...]} / {"users": [...]}
    """

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        session: requests.Session | None = None,
        timeout: float = 30.0,
    ):
        self.base_url = (
            base_url if base_url is not None else settings.ORG_USERS_API_BASE_URL
        ).rstrip('/')
        self.token = token if token is not None else settings.ORG_USERS_API_TOKEN
        self.session = session or requests.Session()
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {'Accept': 'application/json'}
        if self.token:
            scheme = (
                getattr(settings, 'ORG_USERS_API_AUTH_SCHEME', 'Bearer') or 'Bearer'
            ).strip()
            headers['Authorization'] = f'{scheme} {self.token}'
        return headers

    def _list_url(self) -> str:
        if not self.base_url:
            raise OrgUsersAPIError('ORG_USERS_API_BASE_URL is not configured')

        base = self.base_url.rstrip('/')
        if base.endswith(EXTERNAL_USERS_PATH):
            return base
        if base.endswith('/api/v1'):
            return f'{base}/external/users'
        return f'{base}{EXTERNAL_USERS_PATH}'

    def _extract_page(self, payload: Any) -> tuple[list[dict], str | None]:
        if isinstance(payload, list):
            return payload, None
        if not isinstance(payload, dict):
            raise OrgUsersAPIError(f'Unexpected org API payload type: {type(payload)!r}')

        for key in ('results', 'data', 'users'):
            if key in payload and isinstance(payload[key], list):
                next_url = payload.get('next')
                return payload[key], next_url if isinstance(next_url, str) else None

        raise OrgUsersAPIError('Org API payload missing results/data/users list')

    def iter_users(self) -> Iterator[dict]:
        url = self._list_url()
        while url:
            response = self.session.get(url, headers=self._headers(), timeout=self.timeout)
            if response.status_code >= 400:
                raise OrgUsersAPIError(
                    f'Org API HTTP {response.status_code}: {response.text[:200]}'
                )
            try:
                payload = response.json()
            except ValueError as exc:
                raise OrgUsersAPIError('Org API returned non-JSON body') from exc

            users, next_url = self._extract_page(payload)
            for user in users:
                if isinstance(user, dict):
                    yield user
            url = next_url

    def fetch_all_users(self) -> list[dict]:
        return list(self.iter_users())
