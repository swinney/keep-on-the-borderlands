# 0005 — Load-harness transport for the M14 latency measurement

Date: 2026-06-04
Status: Accepted

## Context

World-build spec §11 calls for a load-harness *sketch* that drives N synthetic
sessions through a built world while recording per-command latency, so the
deferred M14 criterion ("50 players, <100 ms server-side") becomes measurable.
The spec (§15) deliberately deferred the **transport** choice to this slice
(M15 slice 6), to be decided against the installed Evennia version. Two options:

1. **In-process synthetic characters** driven via `Object.execute_cmd`, the same
   cmdhandler entry point the engine uses for a live session's input.
2. **External telnet driver** — a script opening N real TCP sessions to a
   running server (portal + telnet protocol), as a player client would.

## Decision

**The harness drives in-process synthetic `PlayerCharacter`s through
`execute_cmd`** (`world/build/loadharness.py`). Rationale:

- It runs in the same process as `build_all()`, so the headless population check
  and the load run share one bootstrap — no live portal, no network, no port
  juggling in CI.
- `execute_cmd` enters the full command handler, so a sample times the real
  server-side parse→dispatch→`func()` work — exactly the quantity the M14
  criterion bounds. The portal/telnet round-trip the external driver adds is
  *network* latency, which the <100 ms target is not about.
- The latency statistics (`summarize`) are a pure, Django-free function, so the
  arithmetic is unit-tested without booting Evennia; only `run_load` touches the
  engine.

The harness **reports the population it actually drove** (`LoadReport`'s
`requested_sessions` vs `driven_sessions`) and never silently caps the load —
the spec §11 anti-silent-truncation rule.

M15 ships this sketch and the populated, bootable target. Running it at 50
sessions and asserting <100 ms is the **M14** task that consumes it; that task
also picks the concrete command mix and session count to model.

## Consequences

- CI can exercise the harness at a small N (a few bots, the default mix) purely
  in-process, proving it drives the world and reports honestly — without a
  flaky network dependency.
- Server-side timing is isolated from transport noise, which is the right signal
  for the <100 ms budget but means the harness does **not** measure end-to-end
  client-perceived latency.
- The harness is a *sketch*: it does not yet model think-time, concurrency, or a
  realistic session lifecycle. The M14 measurement task extends it as needed.

## Considered alternatives

- **External telnet driver.** Rejected as the default: needs a live portal and
  network setup that complicates CI, and folds transport latency into the sample
  the <100 ms target is not about. Kept as a documented fallback for a future
  true end-to-end (client-perceived) measurement.
- **Evennia session/portal fake-session utilities.** A middle path (in-process
  but through the session layer). Rejected for the sketch: more moving parts than
  `execute_cmd` for no extra signal on *command* latency; revisit if the M14 task
  needs to measure session-layer overhead specifically.
