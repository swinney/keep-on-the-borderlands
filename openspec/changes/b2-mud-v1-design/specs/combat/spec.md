## ADDED Requirements

### Requirement: Ability scores and modifiers
The system SHALL generate six ability scores via 3d6 (in order, one swap allowed)
and map each score to the OSE modifier (`−3` at 3 to `+3` at 18).

#### Scenario: Modifier table is exact
- **WHEN** a score is 3, 9, 13, or 18
- **THEN** its modifier is `−3`, `0`, `+1`, `+3` respectively

### Requirement: Ascending armor class
The system SHALL compute armor class as `10 + DEX modifier + worn armor + shield`,
higher being better.

#### Scenario: AC sums its parts
- **WHEN** a character has DEX modifier `+1`, leather (`+2`), and a shield (`+1`)
- **THEN** the character's AC is `14`

### Requirement: Attack resolution
The system SHALL resolve an attack as `1d20 + attack_bonus + ability_mod +
situational ≥ target_AC`, where a natural 20 always hits and a natural 1 always
misses. Melee uses STR; missile uses DEX.

#### Scenario: Meeting the AC hits
- **WHEN** the modified attack total equals the target's AC
- **THEN** the attack hits

#### Scenario: Natural 1 misses regardless of bonuses
- **WHEN** the d20 rolls a natural 1
- **THEN** the attack misses even if the total would meet the AC

### Requirement: Damage
The system SHALL deal weapon-die damage plus STR modifier for melee (missile adds
no STR), with a minimum of `1`.

#### Scenario: Damage floors at one
- **WHEN** weapon die plus a negative STR modifier would total below `1`
- **THEN** the damage dealt is `1`

### Requirement: Saving throws
The system SHALL resolve a save as `1d20 ≥ target`, with the target read from the
class/level table for the relevant OSE save category.

#### Scenario: Save succeeds at the target
- **WHEN** the d20 result equals the save target
- **THEN** the save succeeds

### Requirement: Hit points by level
The system SHALL grant `max(1, hit_die_roll + CON modifier)` hit points per level,
using the class hit die.

#### Scenario: HP never increases by less than one
- **WHEN** a hit-die roll plus a negative CON modifier is below `1`
- **THEN** the character gains `1` hit point that level

### Requirement: Round structure and initiative
The system SHALL run combat in fixed-length rounds on the ticker, with individual
initiative `1d6 + DEX modifier` rerolled each round, highest acting first.

#### Scenario: Higher initiative acts first
- **WHEN** two combatants roll initiative and one total is higher
- **THEN** the higher total acts before the lower in that round

### Requirement: Death at zero hit points
The system SHALL treat a combatant at 0 hit points as dead and hand player death
to the death-and-hardcore subsystem.

#### Scenario: Reaching zero ends the combatant
- **WHEN** a combatant's hit points reach 0
- **THEN** the combatant is dead and removed from the initiative order

### Requirement: Vancian spellcasting
The system SHALL require casters to memorize spells into per-level slots on rest,
consume a slot on cast, and disrupt a spell (losing the slot) if the caster takes
damage before it resolves.

#### Scenario: Casting consumes a prepared slot
- **WHEN** a caster casts a spell prepared in one slot
- **THEN** that slot is expended and unavailable until the next rest

#### Scenario: Damage disrupts an unresolved cast
- **WHEN** a caster takes damage in the round before the declared spell resolves
- **THEN** the spell fails and its slot is lost

### Requirement: Morale
The system SHALL check NPC/henchman morale as `2d6 ≤ morale_score` at the first
casualty and at ≤50% group strength; failure causes flight.

#### Scenario: Failed morale routs the group
- **WHEN** a morale trigger fires and the `2d6` roll exceeds the morale score
- **THEN** the affected NPCs flee

### Requirement: Character creation
The system SHALL gate class choice by OSE prime-requisite minimums, grant
`3d6 × 10` starting gold, and record an irrevocable hardcore flag when opted in.

#### Scenario: Hardcore opt-in is irrevocable
- **WHEN** a player confirms hardcore at creation
- **THEN** the character is permanently flagged hardcore with no later opt-out
