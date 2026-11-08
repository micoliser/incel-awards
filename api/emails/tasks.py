"""Celery tasks for season automation."""

from __future__ import annotations

from celery import shared_task

from emails.services.season import run_org_sync_tick, run_season_mail_tick, run_season_tick


@shared_task(name='emails.org_sync_tick')
def org_sync_tick() -> dict:
    """Infrequent: workspace API sync + mint tokens for new people."""
    stats = run_org_sync_tick()
    return {
        'sync': stats.sync,
        'sync_error': stats.sync_error,
        'tokens': stats.tokens,
    }


@shared_task(name='emails.season_tick')
def season_tick(force_invites: bool = False) -> dict:
    """
    Frequent: tokens + due emails + status flips.

    Does not call the workspace org API.
    """
    stats = run_season_mail_tick(force_invites=force_invites)
    return {
        'tokens': stats.tokens,
        'eligibility_notices': stats.eligibility_notices,
        'invites': stats.invites,
        'closing_reminders': stats.closing_reminders,
        'status_changes': stats.status_changes,
        'voting_opened': stats.voting_opened,
        'voting_closed': stats.voting_closed,
    }


@shared_task(name='emails.season_tick_full')
def season_tick_full(force_invites: bool = False) -> dict:
    """Optional: sync + mail in one task (same as ``run_season_tick``)."""
    stats = run_season_tick(force_invites=force_invites)
    return {
        'sync': stats.sync,
        'sync_error': stats.sync_error,
        'tokens': stats.tokens,
        'eligibility_notices': stats.eligibility_notices,
        'invites': stats.invites,
        'closing_reminders': stats.closing_reminders,
        'status_changes': stats.status_changes,
        'voting_opened': stats.voting_opened,
        'voting_closed': stats.voting_closed,
    }
