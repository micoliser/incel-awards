"""
Scoped DRF throttles for ballot endpoints.

Keyed by SHA-256 of the ballot token when present, otherwise client IP.
Rates come from REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] (see settings / .env).
"""

from __future__ import annotations

import hashlib

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework.throttling import SimpleRateThrottle

from voting.authentication import extract_raw_token


class BallotScopedThrottle(SimpleRateThrottle):
    """
    Rate-limit ballot traffic per token (preferred) or IP.

    Subclasses set ``scope``; rates are read live from Django settings so
    tests can override via ``@override_settings``.
    """

    scope = None
    # Force get_rate() each instance so settings overrides apply.
    rate = None

    def get_rate(self):
        rates = settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_RATES', {})
        try:
            return rates[self.scope]
        except KeyError as exc:
            raise ImproperlyConfigured(
                f"No DEFAULT_THROTTLE_RATES entry for scope '{self.scope}'."
            ) from exc

    def get_cache_key(self, request, view):
        raw = extract_raw_token(request)
        if raw:
            digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:32]
            ident = f'token:{digest}'
        else:
            ident = self.get_ident(request)
            if ident is None:
                return None
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class BallotResolveRateThrottle(BallotScopedThrottle):
    """GET ballot resolve."""

    scope = 'ballot_resolve'


class BallotVoteRateThrottle(BallotScopedThrottle):
    """PUT vote submit."""

    scope = 'ballot_vote'


class BallotDirectoryRateThrottle(BallotScopedThrottle):
    """GET ballot directory search."""

    scope = 'ballot_directory'
