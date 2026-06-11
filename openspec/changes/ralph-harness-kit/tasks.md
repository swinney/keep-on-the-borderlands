## 1. Kit scaffold

- [x] 1.1 Create the self-contained `ralph-harness/` directory with subdirs for
  scripts, templates, the worked example, and tests.
- [x] 1.2 Add `ralph-harness/.gitignore` (and the snippet the README tells adopters
  to copy) covering the configurable state dir (`.ralph/` by default: auth home,
  logs, turn counter, status feed).

## 2. Loop runner (harness-loop-runner)

- [x] 2.1 Copy `until_reset.py` verbatim into the kit with its unit tests; confirm
  the tests pass unchanged (confident-parse → seconds+exit 0; ambiguous → exit 1;
  clamped range). (No prior tests existed; authored 8 in `tests/test_until_reset.py`.)
- [x] 2.2 Write the runner test scaffold (bash, git-fixture based) for: timeout
  kills a hung turn; commit advances/stall increments; max-stalls halt writes a
  one-line non-empty STATUS.md and exits non-zero; pre-existing breadcrumb does
  not stop a fresh loop; new non-whitespace STATUS.md stops; whitespace-only write
  is ignored; usage-limit turn pauses+replays same turn number and is not a stall;
  `--once` runs one turn and exits with its code. (12 checks, all green.)
- [x] 2.3 Generalize `ralph.sh` into the kit: source `ralph.conf` then apply
  `${VAR:-default}` (env > conf > default); replace hardcoded `cd /workspace` with
  `cd "${RALPH_WORKSPACE:-$PWD}"`; remove project-name literals from logic; refuse
  to start if `PROMPT.md` is missing. Pass 2.2. (Also lifted `sleep 30` →
  `RALPH_POLL_INTERVAL`, and resolve `until_reset.py` relative to the script.)
- [x] 2.4 Generalize `ralph-status.sh` into the kit: container-name filter and
  state-dir from config; digest works with no loop running (heartbeat, last turns,
  STATUS.md state, recent commits).

## 3. Config + templates (harness-config-templates)

- [x] 3.1 Author `ralph.conf.example`: every `RALPH_*` key the runner/digest read,
  each with an inline comment and a safe default/placeholder (workspace, tasks
  file, state dir, container image, model, turn timeout, max-stalls, limit poll).
  (11 keys incl. the added `RALPH_POLL_INTERVAL` + meta `RALPH_CONF`.)
- [x] 3.2 Author `PROMPT.md.template`: portable contract (one task/invocation;
  spec→test→implement; full gate in CI order; never commit red; documented stop
  conditions; no-`Co-Authored-By` rule) with only the closed placeholder set
  (`{{PROJECT_NAME}}`, `{{SPECS_DIR}}`, `{{GATE_COMMAND}}`, …) for project bits.
- [x] 3.3 Author `Containerfile.template`: generic base (OS tools, Node, Claude
  Code install, UID/GID-matched non-root user) intact, with a single clearly
  marked `{{TOOLCHAIN_INSTALL}}` block for the adopter's deps.
- [x] 3.4 Author `Makefile.template`: driver targets (`build`, `login`, `loop`,
  `loop-once`, `shell`, `status`, `clean`) with image name + workspace sourced
  from config, not hardcoded in recipes.
- [x] 3.5 Add the fully-resolved worked example (populated `ralph.conf` + resolved
  templates for a sample project) with mutually consistent image/workspace/gate
  values. (example/ "Acme Widgets"; consistency verified — no leftover placeholders.)

## 4. Packaging + docs (harness-kit-packaging)

- [x] 4.1 Verify self-containment: nothing under `ralph-harness/` references a path
  outside it (script grep + manual check); folder copy is sufficient. (Functional
  files clean; all `../` refs stay intra-kit; only the README's prose link to
  `docs/framework/` points out, by design.)
- [x] 4.2 Write the kit `README.md`: ordered adoption flow (copy dir → copy/edit
  `ralph.conf` → fill template placeholders → gitignore state dir → build → login →
  loop), each step naming the exact file/command. (8-step flow.)
- [x] 4.3 Add the complete parameter-reference table (every `ralph.conf` key + every
  template placeholder; name, meaning, default/example); verify completeness against
  the shipped config example and templates (no missing, no extra). (11 keys + 9
  placeholders; verified by grep against the shipped files.)
- [x] 4.4 Document the drift relationship: kit is a generalized copy of the live
  `scripts/`/`PROMPT.md`/`Containerfile`/`Makefile`, can drift, kit is canonical for
  adopters; include a "synced from commit `<sha>`" line. (Synced from `47d4145`.)
- [x] 4.5 Add the methodology cross-links: kit README → `docs/framework/` for the
  why; add a pointer in `docs/framework/` (README) to `ralph-harness/` as the
  runnable Layer-2 autonomy wrapper.

## 5. Gate

- [x] 5.1 ⛔ MILESTONE GATE: full kit present and green (until_reset 8 + runner 12
  checks pass), parameter reference complete + exact, cross-links in place, live
  runtime files untouched. Project gate green: ruff format/check clean, mypy 196
  files clean, pytest 830 passed / 18 skipped. Awaiting human review before archive.
