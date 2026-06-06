⏸ PAUSED at a clean point (operator requested context-clear). Nothing in
progress. main is green; no open work.

DONE: v1 acceptance-complete (M0–M16, PR #23) + post-v1 polish/runtime —
M17a–c (#24–#26), containerized game runtime + Compose (#28), new characters spawn
at the Inner Bailey recall point (#29 attempt → real fix via
`Account.at_post_create_character`, #31; field log §5.18 + coda, #30/#32), and a
player gameplay guide (#33). The game is built, runnable, container-deployable,
acceptance-verified, and documented for both operators (`docs/installation.md`) and
players (`docs/playing.md`). ruff + mypy --strict clean.

REMAINING — captured as ONE OpenSpec change ready for the loop:
**`openspec/changes/rpg-and-runtime-completion/`** (proposal + design + 5 capability
specs + milestone-gated tasks.md). It covers the post-v1 audit gaps — the
player-facing **character layer** (`combat.md` §3/§6/§7) that the v1 acceptance gate
never checked, plus two deferred runtime seams (supersedes the old M17d/M17e):

1. `character-creation` — in-game chargen (3d6-in-order + swap, prime-req-gated
   class/race, derived L1 stats, starting gold, hardcore opt-in). Today a new
   character is a generic blank (flat 10s, no class).
2. `character-progression` — apply leveling on XP threshold (HP roll + class/level
   attack/saves; rules exist, in-game advancement doesn't).
3. `equipment` — wield/wear so armor→AC and weapon→damage (today placeholders:
   1d6 unarmed, AC from DEX only).
4. `quest-runtime` — reachable givers (explicit `giver_key`) + deed-completion
   world-event hooks + carrier objects + live-spy giver-key (was M17d) + 24→26
   quest-count doc-rot.
5. `latency-harness` — wire-level 50-socket telnet latency harness (was M17e /
   ADR-0005).

Intentional non-scope (locked): Cave of the Unknown (sealed stub), PvP (off), GM
tooling (none).

Operating mode: loop-driven, walk-away (memory: loop-autonomy-mandate). On the next
"continue": drive the captured change — `/opsx:apply rpg-and-runtime-completion`,
working tasks.md group-by-group (each capability is a milestone with a ⛔ gate),
loop→review→merge per the established cadence. Suggested order is the tasks.md
numbering (creation → progression → equipment → quest-runtime → latency).
