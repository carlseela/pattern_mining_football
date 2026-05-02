"""High-level loaders for Wyscout-style matches, events, and metadata JSON."""

from __future__ import annotations

from typing import Any

from pmf_data.io import load_json, load_json_array, load_json_array_cached
from pmf_data.names import area_stem_for_competition
from pmf_data.paths import DataPaths


def load_matches(
    area_stem: str,
    *,
    paths: DataPaths | None = None,
    cached: bool = False,
) -> list[dict[Any, Any]] | tuple[dict[Any, Any], ...]:
    """Load all match rows for ``matches_<area_stem>.json``.

    When ``cached`` is False (default), returns a mutable ``list`` like
    :func:`pmf_data.io.load_json_array`. When True, returns a read-only ``tuple``
    from :func:`pmf_data.io.load_json_array_cached`.
    """
    p = paths or DataPaths()
    path = p.matches_file(area_stem)
    if cached:
        return load_json_array_cached(path)
    return load_json_array(path)


def load_matches_for_competition(
    competition_wy_id: int,
    *,
    paths: DataPaths | None = None,
    cached: bool = False,
) -> list[dict[Any, Any]] | tuple[dict[Any, Any], ...]:
    """Like :func:`load_matches` but resolves the file stem from ``competitions.json``."""
    p = paths or DataPaths()
    stem = area_stem_for_competition(competition_wy_id, p)
    return load_matches(stem, paths=p, cached=cached)


def load_events(
    area_stem: str,
    *,
    paths: DataPaths | None = None,
    cached: bool = True,
) -> list[dict[Any, Any]] | tuple[dict[Any, Any], ...]:
    """Load all event rows for ``events_<area_stem>.json``.

    Defaults to ``cached=True`` because league event dumps are large; use
    ``cached=False`` for a one-off parse into a mutable list.

    Returns a ``tuple`` when ``cached`` is True, else a ``list``.
    """
    p = paths or DataPaths()
    path = p.events_file(area_stem)
    if cached:
        return load_json_array_cached(path)
    return load_json_array(path)


def load_events_for_competition(
    competition_wy_id: int,
    *,
    paths: DataPaths | None = None,
    cached: bool = True,
) -> list[dict[Any, Any]] | tuple[dict[Any, Any], ...]:
    """Like :func:`load_events` but resolves the file stem from ``competitions.json``."""
    p = paths or DataPaths()
    stem = area_stem_for_competition(competition_wy_id, p)
    return load_events(stem, paths=p, cached=cached)


def load_events_for_match(
    match_wy_id: int,
    area_stem: str,
    *,
    paths: DataPaths | None = None,
    cached: bool = True,
) -> list[dict[Any, Any]]:
    """Return events whose ``matchId`` equals ``match_wy_id``.

    Still loads the full league events file (subject to ``cached``); filtering is
    in-memory, same as typical notebook workflows.
    """
    rows = load_events(area_stem, paths=paths, cached=cached)
    return [e for e in rows if e.get("matchId") == match_wy_id]


def load_events_for_match_by_competition(
    match_wy_id: int,
    competition_wy_id: int,
    *,
    paths: DataPaths | None = None,
    cached: bool = True,
) -> list[dict[Any, Any]]:
    """Resolve stem from ``competition_wy_id``, then :func:`load_events_for_match`."""
    p = paths or DataPaths()
    stem = area_stem_for_competition(competition_wy_id, p)
    return load_events_for_match(match_wy_id, stem, paths=p, cached=cached)


def load_metadata_json(name: str, *, paths: DataPaths | None = None) -> Any:
    """Load arbitrary metadata JSON (e.g. ``teams.json``, ``competitions.json``)."""
    p = paths or DataPaths()
    return load_json(p.metadata_file(name))


def load_teams(*, paths: DataPaths | None = None) -> Any:
    """Load ``teams.json`` from the dataset root."""
    return load_metadata_json("teams.json", paths=paths)


def load_competitions(*, paths: DataPaths | None = None) -> Any:
    """Load ``competitions.json`` from the dataset root."""
    return load_metadata_json("competitions.json", paths=paths)
