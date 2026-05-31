## ADDED Requirements

### Requirement: Standing bands derived from reputation
The system SHALL derive a player's standing with a faction from a signed integer
reputation score, banded as kill-on-sight (`≤ −30`), hostile (`−29…−15`), neutral
(`−14…+14`), friendly (`≥ +15`). Reputation MUST start at `0` (neutral) and bands
MUST be computed from a single source of truth.

#### Scenario: Five kills turn a tribe hostile
- **WHEN** a player kills five members of a faction (each `−3` reputation)
- **THEN** the player's standing with that faction is `hostile`

#### Scenario: Ten kills turn a tribe kill-on-sight
- **WHEN** a player kills ten members of a faction (reputation `−30`)
- **THEN** the player's standing with that faction is `kill-on-sight`

#### Scenario: Boundary values band correctly
- **WHEN** reputation is exactly `+15`, `+14`, `−15`, or `−30`
- **THEN** the bands are `friendly`, `neutral`, `hostile`, `kill-on-sight` respectively

### Requirement: Reputation events
The system SHALL adjust reputation only via named events (kill member `−3`, kill
leader `−8`, quest-aid `+10`, quest-harm `−10`, bribe `+5`). A bribe MUST NOT
raise standing above `neutral`.

#### Scenario: Killing a leader costs more than a grunt
- **WHEN** a player kills a faction chief or shaman
- **THEN** reputation with that faction decreases by `8`

#### Scenario: Bribe is capped at neutral
- **WHEN** a hostile player bribes a faction enough to exceed `+15`
- **THEN** standing rises no higher than `neutral`

### Requirement: Tribe-pair relations derived from tension
The system SHALL store one symmetric tension integer per unordered faction pair,
banded as allied (`≤ −10`), peaceful (`−9…+4`), tense (`+5…+19`), war (`≥ +20`),
seeded from the B2 initial matrix with unlisted tribe pairs defaulting to `tense`.

#### Scenario: Initial matrix is honored
- **WHEN** a season begins
- **THEN** orc_vol–orc_dec is `war`, goblin–ogre is `allied`, goblin–gnoll is `war`
- **AND** any tribe pair absent from the matrix is `tense`

### Requirement: Shared-enemy thaw
The system SHALL reduce tension by `1` between a faction and each rival currently
`tense` or `war` with it whenever the player kills a member of that faction.

#### Scenario: Killing kobolds thaws kobold–goblin
- **WHEN** a player kills enough kobolds to drive kobold–goblin tension below `+5`
- **THEN** the kobold–goblin relation becomes `peaceful`
- **AND** the player's standing with kobolds has moved toward hostile

### Requirement: Escalation and collapse
The system SHALL raise tension by `8` between `A` and `B` when the player
completes a quest aiding `A` against `B`, and raise tension by `6` between a
faction and each rival when that faction's leadership is broken (chief AND shaman
slain, per repop).

#### Scenario: Broken leadership invites rivals
- **WHEN** a tribe's chief and shaman are both killed
- **THEN** tension between that tribe and each rival increases by `6`

### Requirement: Single config file
The system SHALL read every threshold, event delta, and initial value from one
configuration module, with no behavioral constant hardcoded elsewhere.

#### Scenario: Tuning without code change
- **WHEN** a threshold value is changed in the config module
- **THEN** banding behavior changes accordingly with no other code edit

### Requirement: Reset and decay
The system SHALL reset all standings and re-seed all tension to initial values at
each season boundary, and MAY drift values toward their initial values over real
time when decay is enabled, never crossing the initial value.

#### Scenario: Season reset clears player standing
- **WHEN** a season reset occurs
- **THEN** every player's faction standings return to `neutral`
- **AND** every tribe-pair tension returns to its initial matrix value

#### Scenario: Decay never overshoots
- **WHEN** decay is enabled and time passes with no events
- **THEN** reputation drifts toward `0` but never past it

### Requirement: NPC behavior reflects relationships
The system SHALL make NPC aggression a function of standing, and inter-faction
engagement a function of pair relation.

#### Scenario: Kill-on-sight always attacks
- **WHEN** a player at `kill-on-sight` standing enters a room with that faction's mob
- **THEN** the mob initiates combat

#### Scenario: Friendly never attacks unprovoked
- **WHEN** a player at `friendly` standing enters a room with that faction's mob
- **THEN** the mob does not initiate combat
