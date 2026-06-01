"""Pure-Python season leaderboard model (R6 / docs/specs/seasonal-reset.md §4).

No Evennia imports — fully unit-testable. The season_manager persists the entry
list via Evennia Attributes and reads both the per-season and all-time views
from here.

Two outcomes are recorded (spec §4):
  * ``fell``     — a hardcore death (R7), appended immediately at the death.
  * ``survived`` — a character still standing at season end, captured by the
                   reset snapshot before the new season opens.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

SURVIVED = "survived"
FELL = "fell"


@dataclass(frozen=True)
class LeaderboardEntry:
    """One immutable placement (spec §4 entry fields)."""

    character_name: str
    char_class: str
    level: int
    season_number: int
    hardcore: bool
    outcome: str
    recorded_at: float


@dataclass(frozen=True)
class Survivor:
    """A character still standing at season end, to be snapshotted (spec §4).

    Built by the manager from a live Character; the pure leaderboard turns each
    into a ``survived`` entry under the closing season.
    """

    character_name: str
    char_class: str
    level: int
    hardcore: bool


class Leaderboard:
    """Append-only store of placements with per-season and all-time views."""

    def __init__(self, entries: Iterable[LeaderboardEntry] | None = None) -> None:
        self._entries: list[LeaderboardEntry] = list(entries or ())

    def append_fell(
        self,
        character_name: str,
        char_class: str,
        level: int,
        season_number: int,
        recorded_at: float,
    ) -> LeaderboardEntry:
        """Record a hardcore death immediately (spec §4; R7). Always hardcore."""
        entry = LeaderboardEntry(
            character_name=character_name,
            char_class=char_class,
            level=level,
            season_number=season_number,
            hardcore=True,
            outcome=FELL,
            recorded_at=recorded_at,
        )
        self._entries.append(entry)
        return entry

    def snapshot_survivors(
        self,
        season_number: int,
        survivors: Sequence[Survivor],
        recorded_at: float,
    ) -> tuple[LeaderboardEntry, ...]:
        """Freeze the closing season's survivors (spec §3.2, §4).

        Called before the season counter advances, so ``season_number`` is the
        *closing* season — that is what stamps the entries.
        """
        snapped = tuple(
            LeaderboardEntry(
                character_name=s.character_name,
                char_class=s.char_class,
                level=s.level,
                season_number=season_number,
                hardcore=s.hardcore,
                outcome=SURVIVED,
                recorded_at=recorded_at,
            )
            for s in survivors
        )
        self._entries.extend(snapped)
        return snapped

    def entries(self) -> tuple[LeaderboardEntry, ...]:
        """All entries in insertion order."""
        return tuple(self._entries)

    def per_season(self, season_number: int) -> tuple[LeaderboardEntry, ...]:
        """Entries recorded in a single season, in insertion order (spec §4)."""
        return tuple(e for e in self._entries if e.season_number == season_number)

    def all_time(self) -> tuple[LeaderboardEntry, ...]:
        """All entries ranked by level (highest first), ties by earliest record."""
        return tuple(sorted(self._entries, key=lambda e: (-e.level, e.recorded_at)))
