"""Pure-Python faction state: per-player standings and per-pair tensions.

No Evennia imports — fully unit-testable without booting the server.
The FactionManager GlobalScript (world/managers/faction_manager.py) wraps
this class and persists the dictionaries via Evennia Attributes.

Design: all arithmetic lives here; bands are always recomputed from the
hidden integer (never set directly) so every transition is traceable.
"""

from __future__ import annotations

from world.factions import config as _cfg

# Factions that participate in pair-politics.
# Lawful hub (keep) and solitary monsters (minotaur, owlbear) are excluded.
_PAIR_FACTIONS: frozenset[str] = frozenset(
    k for k, v in _cfg.FACTIONS.items() if v["kind"] in ("tribe", "mercenary", "cult")
)

# Bribe result is capped at the top of the neutral band (one below friendly).
_NEUTRAL_CAP: int = 14


def _pair_key(a: str, b: str) -> tuple[str, str]:
    """Return a canonical sorted pair key so (a,b) == (b,a)."""
    return (min(a, b), max(a, b))


def _initial_tensions() -> dict[tuple[str, str], int]:
    result: dict[tuple[str, str], int] = {}
    for pair_set, val in _cfg.INITIAL_RELATIONS.items():
        sorted_pair = sorted(pair_set)
        result[_pair_key(sorted_pair[0], sorted_pair[1])] = val
    return result


class FactionState:
    """Holds and mutates faction standings and tensions.

    standings: {(faction_id, player_key): R_int}  — initial 0 per pair
    tensions:  {(faction_a, faction_b): T_int}    — seeded from INITIAL_RELATIONS
    """

    def __init__(
        self,
        standings: dict[tuple[str, str], int] | None = None,
        tensions: dict[tuple[str, str], int] | None = None,
    ) -> None:
        self.standings: dict[tuple[str, str], int] = standings if standings is not None else {}
        self.tensions: dict[tuple[str, str], int] = (
            tensions if tensions is not None else _initial_tensions()
        )

    # ── Standing accessors ──────────────────────────────────────────────────

    def get_standing(self, faction_id: str, player_key: str) -> int:
        return self.standings.get((faction_id, player_key), 0)

    def standing_band(self, faction_id: str, player_key: str) -> str:
        return _cfg.band_for(self.get_standing(faction_id, player_key), _cfg.STANDING_LADDER)

    # ── Tension accessors ───────────────────────────────────────────────────

    def get_tension(self, faction_a: str, faction_b: str) -> int:
        pair = _pair_key(faction_a, faction_b)
        if pair in self.tensions:
            return self.tensions[pair]
        return _cfg.INITIAL_RELATIONS.get(frozenset({faction_a, faction_b}), _cfg.DEFAULT_RELATION)

    def relation_band(self, faction_a: str, faction_b: str) -> str:
        return _cfg.band_for(self.get_tension(faction_a, faction_b), _cfg.RELATION_LADDER)

    # ── Internal helpers ────────────────────────────────────────────────────

    def _add_standing(self, faction_id: str, player_key: str, delta: int) -> None:
        key = (faction_id, player_key)
        self.standings[key] = self.standings.get(key, 0) + delta

    def _add_tension(self, faction_a: str, faction_b: str, delta: int) -> None:
        pair = _pair_key(faction_a, faction_b)
        self.tensions[pair] = self.get_tension(faction_a, faction_b) + delta

    # ── Standing events ─────────────────────────────────────────────────────

    def apply_kill_member(self, faction_id: str, player_key: str) -> None:
        """Kill a member: standing -3; thaw rival pairs that are tense/war by -1."""
        self._add_standing(faction_id, player_key, _cfg.STANDING_EVENTS["kill_member"])
        for other in _PAIR_FACTIONS:
            if other == faction_id:
                continue
            if self.relation_band(faction_id, other) in ("tense", "war"):
                self._add_tension(faction_id, other, _cfg.RELATION_EVENTS["kill_member_thaw"])

    def apply_kill_leader(self, faction_id: str, player_key: str) -> None:
        """Kill a faction leader: standing -8."""
        self._add_standing(faction_id, player_key, _cfg.STANDING_EVENTS["kill_leader"])

    def apply_quest_aid(self, faction_id: str, player_key: str) -> None:
        """Complete a quest aiding the faction: standing +10."""
        self._add_standing(faction_id, player_key, _cfg.STANDING_EVENTS["quest_aid"])

    def apply_quest_harm(self, faction_id: str, player_key: str) -> None:
        """Complete a quest harming the faction: standing -10."""
        self._add_standing(faction_id, player_key, _cfg.STANDING_EVENTS["quest_harm"])

    def apply_bribe(self, faction_id: str, player_key: str) -> None:
        """Bribe: standing +5, capped at top of neutral (+14); cannot buy friendly."""
        key = (faction_id, player_key)
        current = self.standings.get(key, 0)
        self.standings[key] = min(current + _cfg.STANDING_EVENTS["bribe"], _NEUTRAL_CAP)

    # ── Relation events ─────────────────────────────────────────────────────

    def apply_quest_aid_vs(self, faction_a: str, faction_b: str) -> None:
        """Quest aiding A against B: T(A,B) +8 (escalates toward war)."""
        self._add_tension(faction_a, faction_b, _cfg.RELATION_EVENTS["quest_aid_vs"])

    def apply_leadership_broken(self, faction_id: str) -> None:
        """Tribe's chief+shaman killed: T(faction, rival) +6 for every rival."""
        for other in _PAIR_FACTIONS:
            if other == faction_id:
                continue
            self._add_tension(faction_id, other, _cfg.RELATION_EVENTS["leadership_broken"])

    # ── Lifecycle ───────────────────────────────────────────────────────────

    def decay_tick(self) -> None:
        """Drift standings toward 0 and tensions toward initial by DECAY_PER_DAY.

        Never overshoots the target (0 for standings, initial for tensions).
        No-op when config.DECAY_ENABLED is False.
        """
        if not _cfg.DECAY_ENABLED:
            return
        d = _cfg.DECAY_PER_DAY
        for key, r in list(self.standings.items()):
            if r > 0:
                self.standings[key] = max(0, r - d)
            elif r < 0:
                self.standings[key] = min(0, r + d)

        for pair, t in list(self.tensions.items()):
            a, b = pair
            initial = _cfg.INITIAL_RELATIONS.get(frozenset({a, b}), _cfg.DEFAULT_RELATION)
            if t > initial:
                self.tensions[pair] = max(initial, t - d)
            elif t < initial:
                self.tensions[pair] = min(initial, t + d)

    def reset_season(self) -> None:
        """Season reset: clear all player standings, re-seed tensions from initial matrix."""
        self.standings = {}
        self.tensions = _initial_tensions()
