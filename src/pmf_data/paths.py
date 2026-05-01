"""Portable resolution of repo `data/` directory and event/match file paths."""

from __future__ import annotations

import os
from pathlib import Path

_PM_DATA_ENV = "PMF_DATA_DIR"


def repo_root(*, start: Path | None = None) -> Path:
    """Walk parents from ``start`` (default: this file) until the project root is found.

    Root is detected when a directory contains ``pyproject.toml`` and ``README.md``.
    Falls back to the first ancestor that has a ``data`` subdirectory plus ``README.md``.
    """
    here = start or Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        has_pyproject = (parent / "pyproject.toml").is_file()
        has_readme = (parent / "README.md").is_file()
        if has_pyproject and has_readme:
            return parent
        if has_readme and (parent / "data").is_dir():
            return parent
    raise FileNotFoundError(
        "Could not locate project root (expected pyproject.toml + README.md, or README.md + data/)."
    )


def default_data_dir() -> Path:
    """``PMF_DATA_DIR`` if set, else ``<repo_root>/data``."""
    override = os.environ.get(_PM_DATA_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return repo_root() / "data"


class DataPaths:
    """Paths under the dataset root (metadata, per-league events/matches)."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = (data_dir or default_data_dir()).resolve()

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    def metadata_file(self, name: str) -> Path:
        return self._data_dir / name

    def events_file(self, area_stem: str) -> Path:
        return self._data_dir / "events" / f"events_{area_stem}.json"

    def matches_file(self, area_stem: str) -> Path:
        return self._data_dir / "matches" / f"matches_{area_stem}.json"
