# Layer 3 — Operator Discipline

**Protects:** process integrity · **Enforceable:** **no** — structural blind spot ·
**Kind: methodology (portable) — copy this layer verbatim.**

The [convergence machine](layer-1-convergence-machine.md) gates the *artifact*. But
someone launches the turns, kills them, triages failures, theorizes about external
systems, and merges — **the operator**. The operator is the one role with **no
gate**: operator actions are not commits, so the commit-graph instrument is blind to
them. This is the framework's structural blind spot, and naming it is the point.

> Spec contract: `openspec/changes/ralph-framework-v1/specs/operator-discipline/spec.md`.

---

## Unenforceable, but mandatory — *methodology*

Layer 3 is a **first-class, mandatory layer — not an appendix** — *and* the one layer
the gate cannot reach. The critical corollary:

> **Output quality is NOT evidence of operator discipline. The two are decoupled.**
> A session can ship zero red commits and lose no work *while* running runaway
> processes, brute-forcing flaky tests, and chasing wrong theories. The clean commit
> graph must **not** be read as a well-run session — that's the **"resilience masks
> sloppiness"** trap (field log §5.13–5.16, M10). Discipline needs its *own* signal.

Everything below is **methodology** — portable to any project. Only the concrete
commands are toolchain-specific.

---

## Epistemic discipline — don't act on unverified belief

**Do cheap analysis before expensive action; don't build causal narratives about
systems you don't control from indirect signals.**

### Triage before brute force
For an **intermittent failure**, ask three questions *before* any reproduction loop:

1. **Is it even possible from the code?** Read the implementation. (Provably
   idempotent code can't under-produce — ruling out a whole class in minutes.)
2. **Is it a test-infra artifact?** Check the harness — concurrent runs? shared vs.
   isolated DB?
3. **Does it matter enough to chase now?** A rare flake in a *test* rarely justifies
   blocking on hours of reproduction.

Only then reproduce — and make it *deterministic* so a hit is permanently
reproducible. (Field log §5.14 — ~15 brute-force reproductions preceded the 10-minute
analysis that should have come first.)

### Defer to ground truth
When explaining *why* an external/third-party system behaved a certain way (CI, the
review bot, an API), **do not assert a tidy causal story from timestamps or partial
output.** State what's verified, flag what's inferred, and **defer to the user's
direct knowledge of their own config/actions.** One verified fact beats a tidy story.
Beware over-generalizing a single anecdote over the user's general statement of how
their system is configured (field log §5.16 — four successive wrong theories for a
review-bot's timing, each asserted from indirect signals; the user knew the answer).

## Procedural discipline — manage the environment cleanly

- **No bare-`&` long jobs.** Run long-lived work only through **tracked, named,
  killable-by-id** mechanisms. An auto-named detached job that slips a name-prefix
  grep is a known failure — it "survives" every cleanup invisibly (field log §5.15).
- **Verify cleanup with a broad check**, not a narrow name-prefix match.
- **Constraints in the prompt, not the filesystem.** When parallel units get their
  own directories, the scope constraint must *also* be in each unit's prompt —
  **infrastructure isolation is not intent isolation.** An agent reads the whole repo
  and over-delivers if only the filesystem fences it (field log §5.13 — a scoped
  worker built the entire milestone).
- **One orchestrator at a time.** Don't spawn competing loops; killing a child
  doesn't kill the parent that respawns it.

---

## Teeth-substitutes for the missing gate — *methodology*

Because no gate can block operator failures, Layer 3 ships **two substitutes**:

### (a) Instrument the operator
Surface non-commit state so thrash becomes *visible*: running processes, resource
use, a per-turn heartbeat/log, and the operator's **stated reasoning**. The commit
graph can't show thrash; instrumentation can.

### (b) Pre-action checklists at the three high-risk moments
The only substitute for a gate the harness can't provide. Apply the matching
checklist **before**:

1. **Backgrounding a job** — see [quickstart](quickstart.md#checklist-1).
2. **Reproducing a failure** — see [quickstart](quickstart.md#checklist-2).
3. **Asserting a causal "why"** about an external system — see
   [quickstart](quickstart.md#checklist-3).

(The full copy-pasteable checklists live in the [quickstart](quickstart.md).)

### When the operator is itself an agent
If the operator role is automated (supervised-direct or higher autonomy), the
discipline **must be encoded as explicit constraints + instrumentation**, not left to
a human to remember — an agent-operator has the **same failure modes with less
self-awareness.** This is why Layer 3 is mandatory even in a fully-agentic setup.

---

## The two faces, at a glance

| Face | Rules | Failure it prevents |
|---|---|---|
| **Epistemic** | triage-before-brute-force · defer-to-ground-truth | burning compute on unfounded belief; eroding trust with wrong theories |
| **Procedural** | no bare-`&` · broad-check cleanup · constraints-in-prompt · one-orchestrator | environment thrash that corrupts results invisibly |

Layer 3 is Layer 1's shadow: the operator the commit-graph instrument cannot measure.
A framework that named the convergence machine but left this toothless would degrade
*silently* — the exact failure this layer exists to prevent.
