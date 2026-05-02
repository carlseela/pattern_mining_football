"""Ball-sequence segmentation from Wyscout-style event streams (one match, time order)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pmf_data.loaders import (
    load_events,
    load_events_for_match,
    load_events_for_match_by_competition,
)
from pmf_data.paths import DataPaths
from pmf_data.pitch import is_unstable_gamestate

# Wyscout event ids used by :func:`ball_sequences_from_events` (see notebook rules).
EXCLUDED_FROM_SEQUENCE_CONTENT: frozenset[int] = frozenset({1, 2, 4, 6, 9})
INTERRUPTION_EVENT_ID: int = 5
SHOT_EVENT_ID: int = 10

# Wyscout ``matchPeriod`` ordering for stable time sort within a match.
_MATCH_PERIOD_ORDER: dict[str, int] = {
    "1H": 0,
    "2H": 1,
    "E1": 2,
    "E2": 3,
    "P": 4,
}


def _event_sort_key(ev: Mapping[str, Any]) -> tuple[int, float]:
    period = str(ev.get("matchPeriod") or "")
    sec = ev.get("eventSec")
    try:
        sec_f = float(sec) if sec is not None else 0.0
    except (TypeError, ValueError):
        sec_f = 0.0
    return (_MATCH_PERIOD_ORDER.get(period, 99), sec_f)


def _match_wy_ids_ordered_unique(match_rows: Sequence[Mapping[str, Any]]) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for row in match_rows:
        mid = int(row["wyId"])
        if mid not in seen:
            seen.add(mid)
            out.append(mid)
    return out


def _events_for_match_ids(
    events: Sequence[Mapping[str, Any]],
    match_wy_ids: set[int],
) -> dict[int, list[Mapping[str, Any]]]:
    """Single pass: bucket events by ``matchId`` for ids in ``match_wy_ids`` (stream order)."""
    buckets: dict[int, list[Mapping[str, Any]]] = {mid: [] for mid in match_wy_ids}
    for ev in events:
        mid = ev.get("matchId")
        if mid in match_wy_ids:
            buckets[int(mid)].append(ev)
    return buckets


def ball_sequences_from_events(
    events: Sequence[Mapping[str, Any]],
) -> list[list[dict[Any, Any]]]:
    """Split ordered match events into ball-relevant sequences (possession-style).

    Rules (aligned with ``data_playground``):

    - Each output sequence keeps a single ``teamId`` (from the first included event).
    - End the sequence on any **team change** in the raw stream (next event not
      appended to the current sequence).
    - End if the **next** event is an interruption (``eventId == 5``); interruption
      is not included.
    - If the **immediate** next event is a shot (``eventId == 10``) by the **same**
      team, include that shot and then end.
    - Events with ``eventId`` in ``{1, 2, 4, 6, 9}`` are skipped from sequence
      *content* but still advance the scan.

    For a **whole league**, group events by ``matchId`` (or iterate matches) and call
    this once per match so sequences do not span games.
    """
    sequences: list[list[dict[Any, Any]]] = []
    current_seq: list[dict[Any, Any]] = []
    seq_team_id: Any = None

    excluded = EXCLUDED_FROM_SEQUENCE_CONTENT
    interruption_id = INTERRUPTION_EVENT_ID
    shot_id = SHOT_EVENT_ID

    i = 0
    n = len(events)
    while i < n:
        curr = events[i]
        curr_event_id = curr.get("eventId")

        if curr_event_id not in excluded and curr_event_id != interruption_id:
            if seq_team_id is None:
                seq_team_id = curr.get("teamId")
            current_seq.append(dict(curr))

        nxt = events[i + 1] if i + 1 < n else None
        end_seq = False
        skip_next = False

        if nxt is None:
            end_seq = True
        else:
            next_event_id = nxt.get("eventId")
            next_team_id = nxt.get("teamId")

            if seq_team_id is not None and next_team_id != seq_team_id:
                end_seq = True
            elif next_event_id == interruption_id:
                end_seq = True
            elif next_event_id == shot_id and (seq_team_id is None or next_team_id == seq_team_id):
                if seq_team_id is None:
                    seq_team_id = next_team_id
                current_seq.append(dict(nxt))
                end_seq = True
                skip_next = True

        if end_seq:
            if current_seq:
                sequences.append(current_seq)
            current_seq = []
            seq_team_id = None

        i += 2 if skip_next else 1

    return sequences


def get_sequences(
    match_wy_id: int,
    area_stem: str | None = None,
    *,
    competition_wy_id: int | None = None,
    paths: DataPaths | None = None,
    cached: bool = True,
) -> list[list[dict[Any, Any]]]:
    """Load events for one match, then :func:`ball_sequences_from_events`.

    Pass exactly one of ``area_stem`` (e.g. ``\"England\"``) or ``competition_wy_id``
    (resolved via ``competitions.json``), same idea as the loaders.
    """
    if (area_stem is None) == (competition_wy_id is None):
        raise ValueError("Pass exactly one of area_stem or competition_wy_id.")

    if area_stem is not None:
        ev = load_events_for_match(match_wy_id, area_stem, paths=paths, cached=cached)
    else:
        ev = load_events_for_match_by_competition(
            match_wy_id, competition_wy_id, paths=paths, cached=cached
        )
    return ball_sequences_from_events(ev)


def ball_sequences_for_team_in_match(
    team_wy_id: int,
    match_wy_id: int,
    area_stem: str | None = None,
    *,
    competition_wy_id: int | None = None,
    paths: DataPaths | None = None,
    cached: bool = True,
) -> list[list[dict[Any, Any]]]:
    """Ball sequences from :func:`get_sequences` that belong to ``team_wy_id`` (first event team)."""
    all_seqs = get_sequences(
        match_wy_id,
        area_stem,
        competition_wy_id=competition_wy_id,
        paths=paths,
        cached=cached,
    )
    return [s for s in all_seqs if s and s[0].get("teamId") == team_wy_id]


def ball_sequences_for_team_across_matches(
    team_wy_id: int,
    match_rows: Sequence[Mapping[str, Any]],
    area_stem: str,
    *,
    paths: DataPaths | None = None,
    cached: bool = True,
) -> list[list[dict[Any, Any]]]:
    """Ball sequences for ``team_wy_id`` over many matches using one league events load.

    ``match_rows`` should be Wyscout-style match dicts (e.g. from :func:`pmf_data.loaders.load_matches`)
    including ``wyId``. Typically filter those rows to games where ``team_wy_id`` participates, then
    pass them here.

    Events are grouped by ``matchId``, sorted by ``matchPeriod`` / ``eventSec``, then segmented with
    :func:`ball_sequences_from_events`. Only sequences whose first included event has
    ``teamId == team_wy_id`` are returned (flat list; each event still carries ``matchId``).
    """
    ordered_ids = _match_wy_ids_ordered_unique(match_rows)
    if not ordered_ids:
        return []

    wanted = set(ordered_ids)
    events = load_events(area_stem, paths=paths, cached=cached)
    by_match = _events_for_match_ids(events, wanted)

    out: list[list[dict[Any, Any]]] = []
    for mid in ordered_ids:
        evs = by_match.get(mid, [])
        if not evs:
            continue
        evs_sorted = sorted(evs, key=_event_sort_key)
        for seq in ball_sequences_from_events(evs_sorted):
            if seq and seq[0].get("teamId") == team_wy_id:
                out.append(seq)
    return out


def get_unstable_sequences(
    sequences: Sequence[Sequence[Mapping[str, Any]]],
    *,
    attacking_positive_x: bool = True,
) -> list[list[dict[Any, Any]]]:
    """Return only ball sequences whose **last** event is an unstable game state.

    Delegates to :func:`pmf_data.pitch.is_unstable_gamestate` (same ``attacking_positive_x`` meaning
    as for penalty-box classification there).
    """
    return [
        list(seq)
        for seq in sequences
        if seq and is_unstable_gamestate(seq[-1], attacking_positive_x=attacking_positive_x)
    ]
