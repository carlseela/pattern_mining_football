"""JSON/CSV loading for Wyscout-style files.

If full-file JSON parsing becomes too slow or memory-heavy, consider ``ijson`` for
streaming the top-level array, or loading chunks; Polars can replace DataFrame
construction in callers without changing path or loader APIs here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


def load_json(path: Path) -> Any:
    """Load JSON from ``path`` (UTF-8)."""
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


def load_json_array(path: Path) -> list[dict[Any, Any]]:
    """Load JSON array of objects; raises ``ValueError`` if root is not a ``list``."""
    raw = load_json(path)
    if not isinstance(raw, list):
        raise ValueError(f"Expected JSON array at root, got {type(raw).__name__}: {path}")
    out: list[dict[Any, Any]] = []
    for i, item in enumerate(raw):
        if not isinstance(item, Mapping):
            raise ValueError(f"Expected object at index {i}, got {type(item).__name__}: {path}")
        out.append(dict(item))
    return out


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


@lru_cache(maxsize=8)
def _load_json_array_cached(path_str: str) -> tuple[dict[Any, Any], ...]:
    """Return an immutable tuple of dicts for LRU-safe caching."""
    path = Path(path_str)
    rows = load_json_array(path)
    return tuple(rows)


def load_json_array_cached(path: Path) -> tuple[dict[Any, Any], ...]:
    """Like ``load_json_array`` but memoized (small LRU); returns a tuple (read-only rows)."""
    return _load_json_array_cached(str(path.resolve()))


@dataclass(frozen=True)
class LazyJsonArray:
    """Notebook-friendly handle: ``LazyJsonArray(paths.events_file('England')).read()``."""

    path: Path

    def read(self) -> tuple[dict[Any, Any], ...]:
        return load_json_array_cached(self.path)
