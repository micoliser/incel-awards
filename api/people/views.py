"""HTTP views for people app (including local fake org directory)."""

from __future__ import annotations

from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from people.dev_fixtures import build_dev_org_users


class DevOrgUsersView(APIView):
    """
    Fake org users list for local development.

    Mirrors production:
      GET /api/v1/external/users
      Authorization: Bearer <ORG_USERS_API_TOKEN>
      Accept: application/json

    Point ORG_USERS_API_BASE_URL at http://127.0.0.1:8000 (origin only).
    """

    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request: Request) -> Response:
        if not getattr(settings, 'DEV_ORG_USERS_ENABLED', False):
            return Response(
                {'detail': 'Dev org users API is disabled.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        expected = (getattr(settings, 'ORG_USERS_API_TOKEN', '') or '').strip()
        if expected:
            auth = (request.headers.get('Authorization') or '').strip()
            scheme = (
                getattr(settings, 'ORG_USERS_API_AUTH_SCHEME', 'Bearer') or 'Bearer'
            ).strip()
            valid = {
                f'{scheme} {expected}',
                f'Bearer {expected}',
                f'Token {expected}',
            }
            if auth not in valid:
                return Response(
                    {'detail': 'Invalid or missing token.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        return Response({'results': build_dev_org_users()})
