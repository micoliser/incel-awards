"""
2026 seed package.

Prefer the gitignored private nominee overlay when present; otherwise use the
committed public fixture (placeholder nominees) so CI and fresh clones work.
"""

try:
    from awards.seed.year_2026 import AWARDS, YEAR, seed_year_2026
except ImportError:  # private overlay not checked out
    from awards.seed.year_2026_fixture import AWARDS, YEAR, seed_year_2026

__all__ = ['AWARDS', 'YEAR', 'seed_year_2026']
