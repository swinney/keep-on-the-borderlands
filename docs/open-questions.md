# Open Questions — Resolutions

Every open question from `CLAUDE.md` §8 and the OpenSpec prompt, resolved with
reasoning. Items settled in a subsystem spec are restated with a pointer; the two
not covered elsewhere (economy, web-client scope) are resolved in full here. All
numbers are **tunable defaults**, not locked decisions — the user may adjust.

Genuinely unauthorized decisions (none as of Phase 0) would go to
`docs/questions.md` instead.

---

## Already locked (recorded elsewhere)

| Question | Resolution | Where |
|---|---|---|
| License | **MIT** | `LICENSE`, `pyproject.toml` |
| Host Python env | **uv** | ADR `0003` |
| Container runtime | **Podman** | ADR `0001` |
| Claude auth | **Pro/Max subscription** | ADR `0002` |
| AC convention | **Ascending** | `docs/architecture.md` §5.1 |

## Resolved in subsystem specs (restated)

| Question | Resolution | Reasoning / pointer |
|---|---|---|
| Season length & cadence | **6 weeks, configurable** | full arc + fresh competition without staleness — `docs/specs/seasonal-reset.md` §1 |
| Leaderboard scope | **Both per-season and all-time** | fresh per cycle + permanent legends; trivial cost — `seasonal-reset.md` §4 |
| Henchmen cap | **OSE CHA max retainers (4 typical, 7 ceiling)** | rules-grounded — `docs/specs/henchmen.md` §3 |
| Henchmen costs/morale/share | **upfront fee + half-XP + negotiated treasure share; OSE loyalty** | `henchmen.md` §1–§4 |
| Faction transition thresholds | **concrete deltas + bands** | `docs/specs/faction.md` §2, §4 |
| Cave of the Unknown | **v1 sealed stub** | no canonical content; preserves architecture — `docs/specs/zones.md` §5, `zones/unknown.md` |

---

## Economy (resolved here)

### Currency and the treasure→XP link

- OSE coinage: `1 pp = 5 gp`, `1 gp = 2 ep = 10 sp = 100 cp`. Gems/jewelry carry
  gp values.
- **Treasure is the primary XP source (1 gp value = 1 XP)**, per OSE B/X. Kills
  grant modest XP; recovered wealth grants the bulk. This is core to OSE pacing
  and is why gold sinks double as level-pacing knobs.
- **XP-on-secure (MUD adaptation):** treasure grants its XP when **secured at a
  safe location** (banked, or carried back into the Keep), not on pickup.
  Reasoning: it makes the wilderness journey and the corpse-run the real
  risk/reward loop, gives banking a purpose beyond death-safety, and rewards
  extraction over hoarding. (Deliberate divergence from tabletop pickup-timing;
  tunable to on-pickup if it proves unfun.)

### Starting gold

- **`3d6 × 10` gp** (OSE; avg ~105), spent on starting gear at the provisioner
  during creation (`docs/specs/combat.md` §7).

### Shop pricing

- Buy prices follow the **OSE equipment list** (data in `world/rules/` /
  `keep/npcs.py`): e.g. torch/oil cheap, sword ~10 gp, plate ~60 gp, holy water
  ~25 gp.
- The **Trader buys loot at ~50%** of list value; gems at full appraised value.

### Banking

- Deposit/withdraw at the moneychanger; **bank balance is death-safe** (R7) and
  is where XP-on-secure is realized for banked coin.
- No interest in v1; an optional small deposit fee is available as a sink knob
  (default `0`). The death-safety incentive is the point, not yield.

### Gold sinks (level-pacing, since gold≈XP)

Henchmen hire fees + treasure shares (R5), inn rest fees, chapel donations
(`cu_bless_blades`), consumables (torches/oil/rations), armor/weapon upgrades, the
ogre bribe (`t_bribe_ogre`), and repairs. Sinks are tuned so a focused player
reaches ~level 10 within a 6-week season.

---

## Web client customization scope (resolved here)

**v1 uses Evennia's default web client with light theming only.** Concretely:
server name/branding, color palette, and MOTD; the `xyzgrid` map panel for the
Wilderness; no bespoke client build.

Reasoning: the default client already gives telnet parity plus a map panel, so
engineering effort belongs in game systems, not UI. **Telnet remains a
first-class surface** (CLAUDE.md). A themed or custom client is a post-launch
consideration, explicitly out of v1 scope.

---

## Status

No questions remain unresolved or blocked at the end of Phase 0. See
`docs/questions.md` for the live escalation log (empty as of Phase 0).
