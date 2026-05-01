"""Map Wyscout competition ``wyId`` to ``events_*`` / ``matches_*`` filename stems."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from pmf_data.io import load_json
from pmf_data.paths import DataPaths


def _stem_from_competition(comp: Mapping[str, Any]) -> str:
    area = comp.get("area") or {}
    area_name = str(area.get("name") or "").strip()
    if area_name:
        return area_name.replace(" ", "_")
    name = str(comp.get("name") or "").strip()
    return name.replace(" ", "_")


@lru_cache(maxsize=4)
def _wyid_to_stem_pairs(data_dir_str: str) -> tuple[tuple[int, str], ...]:
    paths = DataPaths(Path(data_dir_str))
    raw = load_json(paths.metadata_file("competitions.json"))
    if not isinstance(raw, list):
        raise ValueError("competitions.json must contain a JSON array")
    pairs: list[tuple[int, str]] = []
    for comp in raw:
        if not isinstance(comp, Mapping):
            continue
        wy_id = comp.get("wyId")
        if isinstance(wy_id, int):
            pairs.append((wy_id, _stem_from_competition(comp)))
    return tuple(sorted(pairs))


def competition_stems(paths: DataPaths | None = None) -> dict[int, str]:
    """Return mapping ``wyId`` → filename stem (e.g. ``England``, ``World_Cup``)."""
    p = paths or DataPaths()
    return dict(_wyid_to_stem_pairs(str(p.data_dir)))


def area_stem_for_competition(wy_id: int, paths: DataPaths | None = None) -> str:
    """Resolve stem used by ``events_<stem>.json`` / ``matches_<stem>.json``."""
    stems = competition_stems(paths)
    try:
        return stems[wy_id]
    except KeyError as exc:
        raise KeyError(f"No competition wyId={wy_id} in competitions.json") from exc
