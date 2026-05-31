# 0002 — Claude Code authentication: Pro/Max subscription via persisted login

Date: 2026-05-30
Status: Accepted

## Context

Claude Code inside the Ralph Loop container needs to authenticate to
Anthropic. Two options:

1. **API key** via `ANTHROPIC_API_KEY` env var. Bills the Anthropic API
   directly, per-token. Stateless — works on a fresh container with no
   setup.
2. **Pro/Max subscription** via `claude login`. Consumes subscription
   quota (no marginal per-turn charge once you're in). Requires an
   interactive OAuth login that writes credentials to `~/.claude/`,
   which must then persist across container runs.

## Decision

Use the **Pro/Max subscription**. Persist auth by bind-mounting a
project-local `.ralph/claude-home/` directory to `/home/claude/.claude`
inside the container, and use rootless Podman's `--userns=keep-id` so
ownership stays sane on both sides.

## Rationale

- Predictable cost: the loop can run for many hours without surprise
  bills. API-key cost on an unattended `--dangerously-skip-permissions`
  loop is the classic horror story.
- Subscription quota is already paid for; not using it is leaving money
  on the table.
- The bind-mount-plus-`--userns=keep-id` pattern means the auth survives
  container rebuilds without any special volume management — the
  credentials are just files in the project working tree (gitignored).

## Consequences

- `.ralph/` is added to `.gitignore` (auth tokens must never be
  committed; `.ralph/log/` may also contain quoted prompt content).
- One-time setup: `make build && make login`. The `login` target runs
  `claude login`, which prints a URL — open it in a host browser,
  approve, paste the returned code back into the terminal.
- Re-login is needed after token rotation/expiry; just rerun `make
  login`. The bind mount means existing state is preserved between
  attempts.
- All `make` targets that invoke the container now include
  `--userns=keep-id` and the auth bind-mount; none pass
  `-e ANTHROPIC_API_KEY`.

## Considered alternatives

- **API key.** Rejected for cost predictability under unattended runs.
  Still trivially supported — set `ANTHROPIC_API_KEY` and Claude Code
  will prefer it; subscription auth is just the default path.
- **Named Podman volume instead of bind mount.** Equivalent in
  function, worse in ergonomics — harder to inspect, harder to nuke,
  invisible from the IDE. Bind mount wins for a single-developer
  workflow.
- **Bind-mount the host's `~/.claude`.** Rejected: would entangle
  container Claude Code state with the host's Claude Code state
  (project history, MCP servers, settings). Project-local mount keeps
  them cleanly separate.
