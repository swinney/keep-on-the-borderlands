# Fan-out Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the infrastructure to run M10's cave tribes as parallel Ralph Loops — restructure the caves zone for conflict-free per-tribe packages, parameterise the loop runner, and add a host orchestrator that clones/branches/pools/auto-PRs each tribe.

**Architecture:** Three layers. (A) `world/zones/caves/` becomes a shared `_hub` + a filesystem-**discovery** aggregator over per-tribe subpackages (M9 kobold migrates into `caves/kobold/`). (B) `ralph.sh` gains `RALPH_TASKS`/`RALPH_STATE_DIR` so loops don't collide. (C) host shell scripts (`fanout.sh`, `fanout-status.sh`) clone per tribe, pool-launch ≤2 containers, and land each tribe on its gate.

**Tech Stack:** Python 3.12 (Evennia-free pure-data modules + `pkgutil` discovery), Bash, Podman, git, pytest.

Spec: `docs/specs/fanout-harness.md`. Build order follows spec §11 but does the independent `ralph.sh` change first (quick, de-risking).

---

## File Structure

**Create:**
- `mudgame/world/zones/caves/_hub.py` — shared ravine-spine rooms/exits + wilderness link
- `mudgame/world/zones/caves/_tribe.py` — `build_tribe()` helper (build_zone + spawn registration + npc placement)
- `mudgame/world/zones/caves/discovery.py` — enumerate + import tribe subpackages
- `mudgame/world/zones/caves/kobold/__init__.py` + `rooms.py` `exits.py` `mobs.py` `spawns.py` `npcs.py`
- `scripts/fanout.sh` — host orchestrator
- `scripts/fanout-status.sh` — aggregate status across clones
- `scripts/m10-tribes.txt` — tribe manifest

**Modify:**
- `mudgame/world/zones/caves/build.py` — `build()` = hub + discovered tribes
- `mudgame/world/zones/caves/__init__.py` — re-export aggregated data + `build`
- `mudgame/world/zones/caves/rooms.py` `exits.py` `mobs.py` `spawns.py` `npcs.py` — **deleted** after content moves to `_hub.py` + `kobold/`
- `tests/zones/test_caves.py` — update import paths to `caves.kobold.*` / `caves._hub`
- `scripts/ralph.sh` — parameterise task file + state dir

---

## Task 1: Parameterise `ralph.sh` (RALPH_TASKS, RALPH_STATE_DIR)

**Files:**
- Modify: `scripts/ralph.sh`

Single-loop behaviour must stay identical when the vars are unset.

- [ ] **Step 1: Add env defaults** next to `limit_poll` (after line ~43):

```bash
tasks_file=${RALPH_TASKS:-tasks.md}
state_dir=${RALPH_STATE_DIR:-.ralph}
```

- [ ] **Step 2: Use `$tasks_file` in `first_task()`** — replace the hard-coded `tasks.md`:

```bash
first_task() {
  grep -m1 '^- \[ \] ' "$tasks_file" 2>/dev/null \
    | sed -E 's/^- \[ \] *//; s/⛔ MILESTONE GATE.*/[milestone gate]/; s/⛔ TRIBE GATE.*/[tribe gate]/'
}
```

- [ ] **Step 3: Use `$state_dir` for log/turn/heartbeat paths.** Replace the literals: `mkdir -p .ralph/log` → `mkdir -p "$state_dir/log"`; `turn_file=.ralph/turn` → `turn_file="$state_dir/turn"`; in `run_turn` `local log=".ralph/log/turn-${turn}.txt"` → `local log="$state_dir/log/turn-${turn}.txt"`; in `emit_status` the `.ralph/current.json` and `.ralph/status.jsonl` paths → `$state_dir/...` (pass `state_dir` into the python heredoc via an env var `RJ_STATE_DIR="$state_dir"` and read `os.environ["RJ_STATE_DIR"]`). In the loop, `last_log=".ralph/log/turn-${turn}.txt"` → `last_log="$state_dir/log/turn-${turn}.txt"`.

- [ ] **Step 4: Verify syntax**

Run: `bash -n scripts/ralph.sh`
Expected: no output (exit 0).

- [ ] **Step 5: Verify task selection honours `RALPH_TASKS`** (without burning a turn) by extracting `first_task` in a subshell:

```bash
printf '%s\n' '## X' '- [ ] FIRST scoped task' '- [ ] second' > /tmp/scoped-tasks.md
RALPH_TASKS=/tmp/scoped-tasks.md bash -c '
  tasks_file=${RALPH_TASKS:-tasks.md}
  grep -m1 "^- \[ \] " "$tasks_file" | sed -E "s/^- \[ \] *//"'
```
Expected: `FIRST scoped task`. Then confirm the default still resolves: `bash -c 'tasks_file=${RALPH_TASKS:-tasks.md}; echo $tasks_file'` → `tasks.md`.

- [ ] **Step 6: Commit**

```bash
git add scripts/ralph.sh
git commit -m "ralph: parameterise task file + state dir (RALPH_TASKS/RALPH_STATE_DIR)

Defaults preserve single-loop behaviour; lets a fan-out instance point at a
tribe-scoped task list and its own .ralph so parallel loops don't collide."
```

---

## Task 2: Extract `caves/_hub.py` (shared ravine spine)

**Files:**
- Create: `mudgame/world/zones/caves/_hub.py`
- Reference: `mudgame/world/zones/caves/rooms.py`, `exits.py`, `build.py`

The hub owns the 4 `ravine*` rooms, the exits among them, and the wilderness
link. Tribes attach to it by tag, never edit it.

- [ ] **Step 1: Create `_hub.py`** with the hub data moved verbatim from the current files and the wilderness-link logic moved from `build.py`:

```python
"""Caves of Chaos — the shared ravine hub (the spine every lair opens off).

Pure data + an Evennia-deferred build(). Tribe subpackages attach their entrance
exits to these rooms by tag (caves spec); they never edit this module, which is
what keeps parallel tribe work conflict-free (docs/specs/fanout-harness.md §3.3).
"""
from __future__ import annotations

from world.zones.records import ExitRecord, RoomRecord

ZONE = "caves"

# Move the 4 ravine* entries here verbatim from caves/rooms.py:ROOMS
HUB_ROOMS: list[RoomRecord] = [
    # "ravine", "ravine_mid", "ravine_north", "ravine_south"
]

# Move the ravine-spine links + the caves→wilderness return exit here verbatim
# from caves/exits.py (the _LINKS among ravine* rooms, expanded via REVERSE, and
# the asymmetric return exit). Keep the REVERSE/expansion helper with it.
HUB_EXITS: list[ExitRecord] = []

_ENTER_EXIT_ID = "wilderness:ravine_mouth:enter"
_RAVINE_MOUTH_ALIAS = "caves:ravine_mouth"


def build() -> None:
    """Build the hub rooms/exits and wire the Wilderness↔caves crossing."""
    from world.zones import builder  # noqa: PLC0415

    builder.build_zone(ZONE, HUB_ROOMS, HUB_EXITS)
    _link_to_wilderness()


def _link_to_wilderness() -> None:
    # Move verbatim from the current caves/build.py::_link_to_wilderness
    ...
```

When moving, copy the exact `RoomRecord`/`ExitRecord` dict literals and the
`REVERSE` map + link-expansion code from the originals — do not retype the data.

- [ ] **Step 2: Verify it imports Evennia-free**

Run: `uv run python -c "from world.zones.caves import _hub; print(len(_hub.HUB_ROOMS))"`
Expected: `4`

- [ ] **Step 3: Commit**

```bash
git add mudgame/world/zones/caves/_hub.py
git commit -m "caves: extract shared ravine hub into _hub.py (M10 prep)"
```

---

## Task 3: Add `caves/_tribe.py` (shared per-tribe build helper)

**Files:**
- Create: `mudgame/world/zones/caves/_tribe.py`
- Reference: `caves/build.py::_register_spawns`, `world/zones/builder.py`

Keeps each tribe's `build()` tiny and identical in shape (DRY); imported, never edited.

- [ ] **Step 1: Create `_tribe.py`:**

```python
"""Shared build helper for a single cave tribe (docs/specs/fanout-harness.md §3).

A tribe subpackage's build() is `build_tribe(<its data>)`. This module is shared
infrastructure tribes import; they never edit it, so it introduces no merge
contention between parallel tribe branches.
"""
from __future__ import annotations

from world.zones.records import ExitRecord, MobRecord, NpcRecord, RoomRecord

ZONE = "caves"


def build_tribe(
    rooms: list[RoomRecord],
    exits: list[ExitRecord],
    spawns: list[dict],
    mob_templates: list[MobRecord],
    npcs: list[NpcRecord] | None = None,
    placement: dict[str, str] | None = None,
) -> None:
    """Build one tribe's rooms/exits, place its NPCs, register its spawns.

    The hub is already built (caves.build() runs _hub.build() first), so a
    tribe's entrance exit resolves its hub-side room by tag.
    """
    from evennia.utils.search import search_script  # noqa: PLC0415

    from world.zones import builder  # noqa: PLC0415

    builder.build_zone(ZONE, rooms, exits)
    if npcs:
        builder.build_npcs(ZONE, npcs, placement or {})
    managers = search_script("repop_manager")
    if managers:
        managers[0].register_zone(ZONE, spawns, mob_templates)
```

Check `builder` for the exact NPC-build entry point (`grep -n "def build_npcs\|def build_zone" mudgame/world/zones/builder.py`) and match its signature; if NPC placement is folded into `build_zone`, drop the `build_npcs` call and pass npcs through `build_zone` instead.

- [ ] **Step 2: Verify import**

Run: `uv run python -c "from world.zones.caves import _tribe; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add mudgame/world/zones/caves/_tribe.py
git commit -m "caves: add shared build_tribe() helper (M10 prep)"
```

---

## Task 4: Migrate M9 kobold content into `caves/kobold/`

**Files:**
- Create: `caves/kobold/__init__.py` `rooms.py` `exits.py` `mobs.py` `spawns.py` `npcs.py`
- Delete: `caves/rooms.py` `exits.py` `mobs.py` `spawns.py` `npcs.py` (after content moves)

- [ ] **Step 1: Create the subpackage dir and move the data files:**

```bash
mkdir mudgame/world/zones/caves/kobold
git mv mudgame/world/zones/caves/mobs.py   mudgame/world/zones/caves/kobold/mobs.py
git mv mudgame/world/zones/caves/spawns.py mudgame/world/zones/caves/kobold/spawns.py
git mv mudgame/world/zones/caves/npcs.py   mudgame/world/zones/caves/kobold/npcs.py
```

- [ ] **Step 2: Create `kobold/rooms.py`** = the 6 `kobold*` `RoomRecord` entries moved verbatim from the old `caves/rooms.py` (leave `ZONE` import from `world.zones.records`; set `ZONE = "caves"` locally or import from `.._hub`). Then delete the old `caves/rooms.py`.

- [ ] **Step 3: Create `kobold/exits.py`** = the kobold-only `_LINKS` (kobold-room interlinks **plus** the entrance link from the hub room `ravine_north` → `kobold_mouth`) moved from the old `caves/exits.py`, expanded to `EXITS` via the `REVERSE` helper (import the helper from `.._hub` if you kept it there, else duplicate the tiny map). Delete the old `caves/exits.py`.

- [ ] **Step 4: Fix import paths** in the moved `mobs.py`/`spawns.py`/`npcs.py` if any referenced sibling modules (they import only `world.zones.records` — verify with `grep -n "import" mudgame/world/zones/caves/kobold/*.py`; fix any `from world.zones.caves.X` to `from world.zones.caves.kobold.X`).

- [ ] **Step 5: Create `kobold/__init__.py`:**

```python
"""Cave A — the kobold lair (M9 vertical slice, migrated to a tribe subpackage)."""
from __future__ import annotations

from world.zones.caves._tribe import build_tribe
from world.zones.caves.kobold.exits import EXITS
from world.zones.caves.kobold.mobs import MOB_TEMPLATES
from world.zones.caves.kobold.npcs import NPCS, PLACEMENT
from world.zones.caves.kobold.rooms import ROOMS
from world.zones.caves.kobold.spawns import SPAWNS

__all__ = ["EXITS", "MOB_TEMPLATES", "NPCS", "PLACEMENT", "ROOMS", "SPAWNS", "build"]


def build() -> None:
    build_tribe(ROOMS, EXITS, SPAWNS, MOB_TEMPLATES, NPCS, PLACEMENT)
```

- [ ] **Step 6: Verify the subpackage imports Evennia-free**

Run: `uv run python -c "from world.zones.caves import kobold; print(len(kobold.ROOMS), len(kobold.MOB_TEMPLATES))"`
Expected: `6 <n>` (n = kobold mob template count).

- [ ] **Step 7: Commit**

```bash
git add -A mudgame/world/zones/caves/
git commit -m "caves: migrate kobold content into caves/kobold/ subpackage (M10 prep)"
```

---

## Task 5: Discovery aggregator + rewire `build()`/`__init__.py`

**Files:**
- Create: `caves/discovery.py`
- Modify: `caves/build.py`, `caves/__init__.py`
- Test: `tests/zones/test_caves.py`

- [ ] **Step 1: Write the failing test** (append to `tests/zones/test_caves.py`):

```python
def test_discovery_finds_kobold_tribe() -> None:
    from world.zones.caves import discovery
    names = [m.__name__.rsplit(".", 1)[-1] for m in discovery.tribes()]
    assert "kobold" in names
    assert all(hasattr(m, "build") for m in discovery.tribes())

def test_discovery_skips_private_and_dunder() -> None:
    from world.zones.caves import discovery
    names = [m.__name__.rsplit(".", 1)[-1] for m in discovery.tribes()]
    assert not any(n.startswith("_") for n in names)
    assert "__pycache__" not in names
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `uv run pytest tests/zones/test_caves.py::test_discovery_finds_kobold_tribe -v`
Expected: FAIL (`No module named 'world.zones.caves.discovery'`).

- [ ] **Step 3: Create `discovery.py`:**

```python
"""Discover cave-tribe subpackages by filesystem enumeration.

A tribe is any importable subpackage of ``world.zones.caves`` whose name does
not start with ``_`` (``_hub``, ``_tribe`` are shared infra). Adding a tribe is
adding a subdir — no shared file changes — which is what makes parallel tribe
work conflict-free (docs/specs/fanout-harness.md §3.2).
"""
from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType

import world.zones.caves as _caves_pkg


def tribes() -> list[ModuleType]:
    """Return imported tribe modules, sorted by name for deterministic builds."""
    found: list[ModuleType] = []
    for info in pkgutil.iter_modules(_caves_pkg.__path__):
        if not info.ispkg or info.name.startswith("_"):
            continue
        found.append(importlib.import_module(f"world.zones.caves.{info.name}"))
    return sorted(found, key=lambda m: m.__name__)
```

- [ ] **Step 4: Run the discovery tests to confirm they pass**

Run: `uv run pytest tests/zones/test_caves.py::test_discovery_finds_kobold_tribe tests/zones/test_caves.py::test_discovery_skips_private_and_dunder -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Rewrite `caves/build.py`:**

```python
"""Caves of Chaos build() — shared hub + every discovered tribe (idempotent)."""
from __future__ import annotations


def build() -> None:
    """Build the ravine hub, then each tribe subpackage (sorted, idempotent)."""
    from world.zones.caves import _hub, discovery  # noqa: PLC0415

    _hub.build()
    for tribe in discovery.tribes():
        tribe.build()
```

- [ ] **Step 6: Rewrite `caves/__init__.py`** to re-export `build` and aggregate data (hub + all tribes) for the validation suites:

```python
"""The Caves of Chaos zone — shared ravine hub + per-tribe lair subpackages."""
from __future__ import annotations

from world.zones.caves import _hub, discovery
from world.zones.caves.build import build

ZONE = _hub.ZONE


def _aggregate(attr: str) -> list:
    out = list(getattr(_hub, "HUB_" + attr, []))
    for tribe in discovery.tribes():
        out.extend(getattr(tribe, attr, []))
    return out


ROOMS = _aggregate("ROOMS")
EXITS = _aggregate("EXITS")
MOB_TEMPLATES = _aggregate("MOB_TEMPLATES")
SPAWNS = _aggregate("SPAWNS")

__all__ = ["EXITS", "MOB_TEMPLATES", "ROOMS", "SPAWNS", "ZONE", "build"]
```

If `tests/zones/test_caves.py` imported `ROOMS, ZONE` from `caves.rooms`, repoint those imports to `from world.zones import caves` and use `caves.ROOMS` / `caves.ZONE`; repoint any `caves.mobs`/`caves.spawns` imports likewise.

- [ ] **Step 7: Run the full caves + vertical-slice suites**

Run: `uv run pytest tests/zones/test_caves.py tests/zones/test_m9_vertical_slice.py -v`
Expected: PASS (all green — same room/mob/exit assertions, now via hub+discovery).

- [ ] **Step 8: Full gate**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest -q`
Expected: ruff clean, mypy clean, `426 passed, 40 skipped` (unchanged count — refactor is behaviour-preserving).

- [ ] **Step 9: Commit**

```bash
git add -A mudgame/world/zones/caves/ tests/zones/test_caves.py
git commit -m "caves: discovery-based build() over per-tribe subpackages (M10 prep)

build() = _hub.build() then each discovered tribe; adding caves/<tribe>/ needs
no shared-file edit. Behaviour-preserving: full suite stays at 426 passed."
```

---

## Task 6: Tribe manifest + per-tribe task template

**Files:**
- Create: `scripts/m10-tribes.txt`

- [ ] **Step 1: Write the manifest** (one tribe unit per line; `#` comments ignored):

```
orc
goblin
hobgoblin
bugbear
gnoll
```

- [ ] **Step 2: Commit**

```bash
git add scripts/m10-tribes.txt
git commit -m "fanout: M10 tribe manifest (orc rivalry as one unit)"
```

The scoped task template is emitted by `fanout.sh` (Task 7), not stored as a file.

---

## Task 7: `scripts/fanout.sh` orchestrator

**Files:**
- Create: `scripts/fanout.sh`

- [ ] **Step 1: Write `fanout.sh`** (host-side; `--dry-run` prints the plan and launches nothing):

```bash
#!/usr/bin/env bash
# Fan-out harness: run M10 cave tribes as parallel Ralph Loops, one clone +
# container each, pooled, auto-PR'd on each tribe's gate.
# See docs/specs/fanout-harness.md.
#
#   fanout.sh [--dry-run]
#
# Env: FANOUT_CONCURRENCY (default 2), RALPH_MODEL (default claude-sonnet-4-6),
#      GH_REMOTE (default origin's URL), IMAGE (default kotb-ralph).
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

dry=0; [ "${1:-}" = "--dry-run" ] && dry=1
concurrency=${FANOUT_CONCURRENCY:-2}
model=${RALPH_MODEL:-claude-sonnet-4-6}
image=${IMAGE:-kotb-ralph}
repo=$(pwd)
remote=${GH_REMOTE:-$(git remote get-url origin)}
claude_dir="$repo/.ralph/claude-home"
wt_root="$repo/../kotb-wt"
manifest=scripts/m10-tribes.txt

tribes=$(grep -vE '^\s*#|^\s*$' "$manifest")

scoped_tasks() {  # $1 = tribe name -> stdout: the scoped task list
  local t=$1
  cat <<EOF
# M10 tribe: $t (scoped task list — canonical tasks.md untouched)
- [ ] world/zones/caves/$t/ lair rooms + $t mobs (pure data + builder; mirror caves/kobold/)
- [ ] $t leaders wired to the M6 leadership-halt + rival scouting (repop.md §3-4)
- [ ] Faction standing shifts observable in $t behavior (M4 ↔ zone)
- [ ] tests/zones/test_$t.py green (rooms/mobs/leaders/faction)
- [ ] ⛔ TRIBE GATE — write "$t complete — paused for review." to STATUS.md and stop. Make no code changes and do not check this box.
EOF
}

prepare() {  # $1 = tribe -> clone, branch, scoped tasks
  local t=$1 dest="$wt_root/m10-$t"
  if [ "$dry" = 1 ]; then
    echo "DRY: git clone $repo $dest; set origin=$remote; checkout -b tribe/m10-$t"
    echo "DRY: write $dest/.ralph/tribe-tasks.md:"; scoped_tasks "$t" | sed 's/^/DRY:   /'
    return
  fi
  rm -rf "$dest"
  git clone --quiet "$repo" "$dest"
  git -C "$dest" remote set-url origin "$remote"
  git -C "$dest" fetch --quiet origin
  git -C "$dest" checkout -q -b "tribe/m10-$t"
  mkdir -p "$dest/.ralph"
  scoped_tasks "$t" > "$dest/.ralph/tribe-tasks.md"
}

launch() {  # $1 = tribe -> start its container
  local t=$1 dest="$wt_root/m10-$t"
  local cmd=(podman run -d --name "kotb-ralph-m10-$t" --userns=keep-id
    -e "RALPH_MODEL=$model" -e "RALPH_TASKS=.ralph/tribe-tasks.md"
    -v "$dest:/workspace" -v "$claude_dir:/home/claude/.claude"
    "$image" ./scripts/ralph.sh)
  if [ "$dry" = 1 ]; then echo "DRY: ${cmd[*]}"; return; fi
  "${cmd[@]}"
}

# Pool scheduler: keep <=concurrency containers; on each tribe's gate push+PR.
echo "fanout: ${concurrency}x  model=$model  tribes: $(echo $tribes | tr '\n' ' ')"
for t in $tribes; do
  prepare "$t"
done
[ "$dry" = 1 ] && { echo "fanout: dry-run complete (nothing launched)"; exit 0; }

# (live pool loop) launch up to N, then poll STATUS.md of each clone; on
# "<t> complete" -> push branch, gh pr create, request copilot, auto-merge if
# clean, remove clone, free slot; on stall halt -> surface, no PR, free slot.
# Implemented with a simple running-set + sleep poll (mirrors ralph.sh's loop).
source scripts/fanout-pool.sh   # the pool/gate/PR logic (Task 7b)
run_pool "$concurrency" "$tribes"
```

Split the live pool/gate/PR logic into `scripts/fanout-pool.sh` (`run_pool`) so `fanout.sh` stays readable; `run_pool` launches up to N via `launch`, polls each `$wt_root/m10-<t>/STATUS.md`, and on a gate runs `git -C <dest> push -u origin tribe/m10-<t>`, `gh pr create`, `gh api .../requested_reviewers` for copilot, then auto-merges when `gh pr checks` is green and Copilot review has zero comments.

- [ ] **Step 2: `bash -n` both scripts**

Run: `bash -n scripts/fanout.sh && echo ok`
Expected: `ok`

- [ ] **Step 3: Dry-run shows the full plan, launches nothing**

Run: `./scripts/fanout.sh --dry-run`
Expected: prints `DRY: git clone …`, the scoped task list, and `DRY: podman run …` for all five tribes; ends `dry-run complete (nothing launched)`. Confirm no container started: `podman ps -a --format '{{.Names}}' | grep m10 || echo none` → `none`.

- [ ] **Step 4: Commit**

```bash
git add scripts/fanout.sh scripts/fanout-pool.sh
git commit -m "fanout: host orchestrator (clone/branch/scope/pool-launch) + dry-run"
```

---

## Task 8: `scripts/fanout-status.sh` aggregate view

**Files:**
- Create: `scripts/fanout-status.sh`

- [ ] **Step 1: Write it:**

```bash
#!/usr/bin/env bash
# Aggregate Ralph status across all active fan-out clones.
set -uo pipefail
wt_root="$(git rev-parse --show-toplevel)/../kotb-wt"
printf '%-12s %-5s %-9s %s\n' TRIBE TURN STATE "LAST COMMIT"
for d in "$wt_root"/m10-*/; do
  [ -d "$d" ] || continue
  t=$(basename "$d" | sed 's/^m10-//')
  turn=$(cat "$d/.ralph/turn" 2>/dev/null || echo -)
  if grep -q '[^[:space:]]' "$d/STATUS.md" 2>/dev/null; then state=gated; else state=running; fi
  last=$(git -C "$d" log -1 --format='%h %s' 2>/dev/null || echo -)
  printf '%-12s %-5s %-9s %s\n' "$t" "$turn" "$state" "$last"
done
```

- [ ] **Step 2: Verify**

Run: `bash -n scripts/fanout-status.sh && ./scripts/fanout-status.sh`
Expected: header row prints; no tribes yet (no `../kotb-wt/m10-*` clones) → just the header. Exit 0.

- [ ] **Step 3: Commit**

```bash
git add scripts/fanout-status.sh
git commit -m "fanout: aggregate status across active tribe clones"
```

---

## Task 9: Makefile + docs wiring

**Files:**
- Modify: `Makefile`, `docs/ralph-loop.md`

- [ ] **Step 1: Add Make targets** after `status:`:

```makefile
fanout:
	@./scripts/fanout.sh

fanout-dry:
	@./scripts/fanout.sh --dry-run

fanout-status:
	@./scripts/fanout-status.sh
```
Add `fanout fanout-dry fanout-status` to the `.PHONY` line and a `help` line each.

- [ ] **Step 2: Document** the harness in `docs/ralph-loop.md` §7 (a short "Fan-out for the content layer" subsection pointing at `docs/specs/fanout-harness.md` and the `make fanout*` targets).

- [ ] **Step 3: Verify Makefile parses**

Run: `make help | grep fanout`
Expected: the three fanout help lines.

- [ ] **Step 4: Commit**

```bash
git add Makefile docs/ralph-loop.md
git commit -m "fanout: make targets + docs wiring"
```

---

## Self-Review

- **Spec coverage:** §3 caves restructure → Tasks 2–5; §4 ralph.sh → Task 1; §5 fanout.sh → Task 7; §6 template → Task 7 `scoped_tasks`; §7 status → Task 8; manifest → Task 6; Make/docs → Task 9. §8 integration task (F) is downstream operation, not built here (noted in plan scope). ✅
- **Placeholders:** the verbatim data moves (Tasks 2,4) are mechanical `git mv` + copy of existing literals, with exact verification commands — not "implement later." The only deferred detail is `fanout-pool.sh`'s live merge logic, called out explicitly as Task 7b with its responsibilities enumerated; expand it inline when implementing Task 7.
- **Type/name consistency:** `build_tribe(rooms, exits, spawns, mob_templates, npcs, placement)` (Task 3) matches the kobold `build()` call (Task 4 Step 5) and the data names re-exported in `__init__` (Task 5 Step 6: `ROOMS/EXITS/MOB_TEMPLATES/SPAWNS`). `tribes()` returns modules with `.build()` (Task 5 Step 3) consumed by `caves.build()` (Step 5). ✅

---

## Notes for the implementer
- Run every caves task's verification before committing; the refactor must keep `pytest -q` at **426 passed, 40 skipped** (Task 5 Step 8) — a changed count means content was lost or double-counted in aggregation.
- `caves/_hub.py` and `caves/_tribe.py` are the only shared caves files; tribe work must never edit them (that is the conflict-free guarantee).
- Confirm `builder.build_npcs` exists/signature before Task 3 Step 1; kobold `NPCS` is empty so the npc path is exercised first by a later tribe.
