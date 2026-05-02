"""Wyscout-style pitch geometry (0–100 coordinates) and football-specific checks."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

# Wyscout main/sub event ids (see ``data/eventid2name.csv``).
_SHOT_EVENT_ID: Final[int] = 10
_CROSS_SUBEVENT_ID: Final[int] = 80  # Pass → Cross

# Opponent penalty area when the team attacks toward increasing ``x`` (goal at ``x == 100``).
# Corners ``(84, 19)``, ``(100, 19)``, ``(84, 81)``, ``(100, 81)`` — axis-aligned rectangle.
WYSCOUT_PENALTY_BOX_HIGH_X: Final[tuple[float, float, float, float]] = (84.0, 19.0, 100.0, 81.0)
# Same box mirrored when attacking toward ``x == 0`` (width 16 = 100 − 84 on this scale).
WYSCOUT_PENALTY_BOX_LOW_X: Final[tuple[float, float, float, float]] = (0.0, 19.0, 16.0, 81.0)


def _in_closed_rect(
    x: float,
    y: float,
    bounds: tuple[float, float, float, float],
) -> bool:
    xmin, ymin, xmax, ymax = bounds
    return xmin <= x <= xmax and ymin <= y <= ymax


def is_penalty_box_attacking(
    x: float,
    y: float,
    *,
    attacking_positive_x: bool = True,
) -> bool:
    """Return True if ``(x, y)`` lies in the **opponent** penalty box for the attack direction.

    Uses Wyscout-style pitch coordinates: ``x`` and ``y`` in ``[0, 100]``, goals at ``x = 0`` and
    ``x = 100``.

    - ``attacking_positive_x=True``: attacking toward ``x = 100``; opponent box is
      ``WYSCOUT_PENALTY_BOX_HIGH_X``.
    - ``attacking_positive_x=False``: attacking toward ``x = 0``; opponent box is the mirror
      ``WYSCOUT_PENALTY_BOX_LOW_X``.
    """
    bounds = WYSCOUT_PENALTY_BOX_HIGH_X if attacking_positive_x else WYSCOUT_PENALTY_BOX_LOW_X
    return _in_closed_rect(float(x), float(y), bounds)


def event_end_position_xy(event: Mapping[str, Any]) -> tuple[float, float] | None:
    """Return ``(x, y)`` for the last entry in ``event['positions']``, or ``None`` if missing."""
    positions = event.get("positions")
    if not isinstance(positions, list) or not positions:
        return None
    last = positions[-1]
    if not isinstance(last, Mapping):
        return None
    x, y = last.get("x"), last.get("y")
    if x is None or y is None:
        return None
    return (float(x), float(y))


def is_unstable_gamestate(
    event: Mapping[str, Any],
    *,
    attacking_positive_x: bool = True,
) -> bool:
    """Return True if ``event`` matches an unstable game-state rule (short-circuit, in order).

    Checks are applied **in this order**; the first match wins:

    1. **Shot:** ``eventId == 10``.
    2. **Cross:** ``subEventId == 80`` (Wyscout Pass → Cross).
    3. **Penalty box:** end position of the event (last ``positions`` entry) lies in the
       opponent penalty area for ``attacking_positive_x`` (see :func:`is_penalty_box_attacking`).
    """
    if event.get("eventId") == _SHOT_EVENT_ID:
        return True
    if event.get("subEventId") == _CROSS_SUBEVENT_ID:
        return True
    end_xy = event_end_position_xy(event)
    if end_xy is not None:
        x, y = end_xy
        if is_penalty_box_attacking(x, y, attacking_positive_x=attacking_positive_x):
            return True
    return False
