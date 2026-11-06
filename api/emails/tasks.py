"""Celery tasks for season automation."""

from __future__ import annotations

from celery import shared_task

from emails.services.season import run_season_tick


@shared_task(name='emails.season_tick')
def season_tick(force_invites: bool = False) -> dict:
    """Periodic: sync org users, mint tokens, send due invites, advance status."""
    stats = run_season_tick(force_invites=force_invites)
    return {
        'sync': stats.sync,
        'sync_error': stats.sync_error,
        'tokens': stats.tokens,
        'invites': stats.invites,
        'status_changes': stats.status_changes,
    }
