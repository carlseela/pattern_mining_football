"""Helpers for turning JSON rows into ``pandas.DataFrame``.

Events are deeply nested (tags, positions, …). Prefer keeping ``list[dict]`` for custom
walkers; use ``events_partial_frame`` on a **slice** or filtered subset when you need a
tabular view. Avoid ``json_normalize`` on full league dumps unless memory allows.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd


def records_to_frame(records: Sequence[Mapping[str, Any]], *, sep: str = "_") -> pd.DataFrame:
    """Build a frame from homogeneous dict rows.

    Uses ``pd.json_normalize(..., sep=sep)`` so nested mappings (e.g. competition
    ``area``) become dotted columns; mostly-flat match rows behave like a normal table.
    """
    return pd.json_normalize(records, sep=sep)


def events_partial_frame(
    events: Sequence[Mapping[str, Any]],
    *,
    max_level: int = 1,
) -> pd.DataFrame:
    """Shallow flatten of event dicts via ``pd.json_normalize``.

    League-level event arrays are huge—pass only ``events[:N]``, filter by match, or
    similar before calling this.
    """
    return pd.json_normalize(events, max_level=max_level)
