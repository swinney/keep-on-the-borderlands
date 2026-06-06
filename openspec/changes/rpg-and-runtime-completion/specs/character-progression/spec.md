## ADDED Requirements

### Requirement: XP-threshold advancement

A character SHALL advance one level in-game when its experience points reach or
exceed the next level's class XP threshold. Advancement SHALL be capped at level 10
(the B2-scaled range) and SHALL NOT de-level. Multiple levels' worth of XP gained
at once SHALL resolve to the correct final level.

#### Scenario: Crossing a threshold advances a level
- **WHEN** a character at level N gains XP that reaches the level N+1 threshold for its class
- **THEN** the character's level becomes N+1
- **AND** the character does not exceed level 10

#### Scenario: XP below the threshold does not advance
- **WHEN** a character gains XP that stays below the next threshold
- **THEN** the character's level is unchanged

### Requirement: Level-up applies HP and table-derived stats

On gaining a level, the character SHALL roll new hit points (`class HD + CON mod`,
minimum 1, via the existing `roll_hit_points`) added to its maximum, and SHALL
update its attack bonus and saving throws from the class+level tables.

#### Scenario: Level-up increases max HP and updates combat stats
- **WHEN** a character advances from level N to N+1
- **THEN** its maximum HP increases by `max(1, HD_roll + CON_mod)`
- **AND** its attack bonus and saves match the class+level table for N+1

### Requirement: Advancement is announced

The character SHALL be notified in-game when it gains a level.

#### Scenario: Player sees the level-up
- **WHEN** a character advances a level
- **THEN** a message announcing the new level is sent to the character
