M13 COMPLETE & MERGED (PR #20, merge commit 19c73f5). Next milestone: M14
(polish & scale). Nothing in progress.

The quest catalog (R9) is built and on main: all 26 enumerated quests across
every giver, prereq gating (level/prior-quest/standing/evidence) with
per-character repeatable/story state, faction completion effects
(harm/aid/tension/break-alliance) fired on turn-in, the cult-aiding spy chain
(3rd → ambush brand), per-quest evidence thresholds (Curate ≥2 sightings vs
report-grade), item rewards, and the deed-completion gate that closes the
turn-in exploit. The two season-global effects: c_expose_priest trips the
server-global exposure on report; c_destroy_shrine's season-end is fired by the
canonical Altar.at_destruction hook (the quest grants only its reward). 711
tests passing, ruff + mypy --strict clean.

Built free-run by the Ralph loop (turns 57–64, Opus) across two rounds: the
initial M13 build, then a review-driven gap-closure round after independent
review + Copilot caught that the loop had (a) wired faction effects but not
fired aid/tension/alliance/cult on turn-in, and (b) shipped a deed-quest turn-in
exploit, an item-reward omission, and a single-threshold evidence gate.

Deferred to the spawner/world-build layer (tasks.md "Deferred follow-ups"), not
silently skipped: quest-giver resolution by an explicit giver-key (only
Guildmaster/Castellan resolve today; spy/hermit/provisioner/tribe-chief givers
don't), and the world-event hooks that SET deed-completion flags. The completion
effects are wired + tested at the wiring level meanwhile.

Next: M14 — polish & scale (economy/XP-pacing balance, 50-player <100ms latency,
web-client theming + MOTD, encounter-table tuning). Build per docs/specs via the
loop on an m14 branch.
