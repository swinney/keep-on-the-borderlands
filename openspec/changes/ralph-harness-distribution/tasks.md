## 1. Stand up `swinney/keep-on-ralphing` (new repo)

- [ ] 1.1 Create the repo `swinney/keep-on-ralphing` (private or team-visible) and
  the directory skeleton from design D1 (`.claude-plugin/`, `skills/`, `base/`,
  `templates/`, `example/`, `extras/`, `docs/`, `README.md`).
- [ ] 1.2 Move the runner machinery in: `base/scripts/ralph.sh` and
  `base/scripts/until_reset.py` (from the kit copies — already generalized + bash
  3.2-safe + 3.7-safe). Bring the kit's tests (`test_until_reset.py`,
  `test_ralph_runner.sh`, `run.sh`, `pytest.ini`) under `base/tests/` (or `tests/`)
  and confirm green in the new repo.
- [ ] 1.3 Move fan-out into `extras/` (`fanout*.sh`, `m10-tribes.txt`) with a README
  note marking it unsupported/experimental; bring `fanout-harness.md` along.

## 2. Base image (ralph-base-image)

- [ ] 2.1 Author `base/Containerfile`: generic layer (OS tools, Node, Claude Code,
  UID/GID-matched user) + `COPY base/scripts/* /usr/local/bin/` so the machinery is
  on PATH. Single-arch Linux; no multi-arch.
- [ ] 2.2 Add `make build-base` (registry-free local build, UID/GID build args).
  Verify it produces a usable image on a Linux/podman host.
- [ ] 2.3 Author the thin consumer `Containerfile` template (`FROM <base>` + one
  `{{TOOLCHAIN_INSTALL}}` block) and confirm a consumer image builds from it.
- [ ] 2.4 README: state Linux + podman + single-arch scope explicitly; document the
  optional GHCR path as additive (not required).

## 3. Plugin + scaffolder (ralph-plugin-scaffolder)

- [ ] 3.1 Author `.claude-plugin/plugin.json` (name `ralph-harness` / your choice)
  and `.claude-plugin/marketplace.json` so `/plugin marketplace add
  swinney/keep-on-ralphing` + `/plugin install` works (no directory submission).
- [ ] 3.2 Bundle the config templates under `templates/` (from the kit:
  `ralph.conf.example`, `PROMPT.md.template`, `Containerfile.template`,
  `Makefile.template`).
- [ ] 3.3 Author `skills/ralph-init/SKILL.md`: read the target repo (project name,
  specs/tests dirs, gate command from CI), fill the templates, write `ralph.conf`,
  `PROMPT.md`, `tasks.md` starter, thin `Containerfile`/`Makefile`, gitignore the
  state dir; report inferred-vs-asked; offer to `make build-base`.
- [ ] 3.4 Add the fully-resolved worked example under `example/` (golden reference;
  consistent image/workspace/gate).
- [ ] 3.5 Verify install + scaffold end-to-end in a throwaway repo: plugin installs,
  `/ralph-init` produces runnable headless config.

## 4. Status skill (ralph-status-skill)

- [ ] 4.1 Author `skills/ralph-status/SKILL.md`: read `.ralph/current.json`,
  `status.jsonl`, `STATUS.md`, and `git`; report running state, current/last turns
  with commit+exit, stop signal (non-whitespace only), recent commits — with no
  active loop required.
- [ ] 4.2 Confirm it surfaces the same facts the old `ralph-status.sh` did, and that
  no status shell script ships to a consumer.

## 5. ⛔ PROOF GATE: KOTB consumes the new harness (before any deletion)

- [ ] 5.1 In KOTB: `/plugin marketplace add swinney/keep-on-ralphing` + install.
- [ ] 5.2 In KOTB: run `/ralph-init` to generate KOTB's thin consumer config
  (`ralph.conf`, filled `PROMPT.md` preserving KOTB's contract, `Containerfile`
  FROM base + Evennia toolchain, thin `Makefile`); keep existing `tasks.md`.
- [ ] 5.3 `make build-base` then run KOTB's loop for ≥1 turn GREEN on the new path
  (commit produced, gate passes). ⛔ Do not proceed to deletion until this passes.

## 6. Remove harness from KOTB (only after the proof gate)

- [ ] 6.1 Delete machinery: `scripts/ralph.sh`, `scripts/ralph-status.sh`,
  `scripts/until_reset.py`, `scripts/fanout*.sh`, `scripts/m10-tribes.txt`,
  `ralph-harness/`, and the generic root `Containerfile`/`Makefile`/`PROMPT.md`
  superseded by the `/ralph-init`-generated thin copies. (Separate reviewable commit.)
- [ ] 6.2 Move methodology docs to `keep-on-ralphing/docs/`: `docs/ralph-loop.md`,
  `docs/framework/`, `docs/ralph-loop-evaluation.md`, the harness decision records
  (`0001-container-runtime.md`, `0002-claude-auth.md`); resolve the field-log
  question per design (default: move `docs/ralph-loop-experiment.md`, leave a KOTB
  pointer).
- [ ] 6.3 Rewrite CLAUDE.md §5/§6/§7 + the cold-start map to describe consuming
  `keep-on-ralphing` (install plugin → `/ralph-init` → `make build-base`) instead
  of in-repo harness; fix dangling links.
- [ ] 6.4 Update auto-memories that reference moved paths (`experiment-log-upkeep`,
  framework/ralph-loop pointers) to the new repo.

## 7. Gate

- [ ] 7.1 ⛔ MILESTONE GATE: `keep-on-ralphing` green on its own tests; KOTB loop
  runs on the new path (proof gate §5 passed); KOTB harness removed and CLAUDE.md +
  memories updated; KOTB game/tests/CI quality gate still green. Human review.
