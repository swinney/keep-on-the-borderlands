## ADDED Requirements

### Requirement: Modular zone packages
The system SHALL define each zone as a self-contained package exposing a `build()`
hook plus pure-data lists (rooms, exits, mob templates, spawns, NPCs), with static
content free of Evennia imports.

#### Scenario: Zone exposes the standard interface
- **WHEN** a zone package is loaded
- **THEN** it exposes `build()` and the room, exit, mob-template, spawn, and NPC data

### Requirement: Referential integrity of zone data
The system SHALL ensure room keys are unique within a zone and every exit resolves
to a real room.

#### Scenario: No dangling exits
- **WHEN** zone data is validated
- **THEN** every exit's `from` and `to` keys resolve to defined rooms in scope

#### Scenario: Unique room keys
- **WHEN** zone data is validated
- **THEN** no two rooms in a zone share a key

### Requirement: Faction and leader consistency
The system SHALL ensure every mob faction is a valid faction id and that each Caves
tribe has exactly one chief and one shaman spawn.

#### Scenario: Mob factions are valid
- **WHEN** zone data is validated
- **THEN** every mob template's faction is a defined faction id

#### Scenario: Each tribe has one chief and one shaman
- **WHEN** the Caves zone is validated
- **THEN** each tribe defines exactly one chief spawn and one shaman spawn

### Requirement: Idempotent build
The system SHALL build zones idempotently, keyed by a stable `zone:key` identity,
and register spawn points with the repop manager rather than spawning mobs directly.

#### Scenario: Rebuilding does not duplicate
- **WHEN** a zone's `build()` runs twice
- **THEN** the resulting room and exit set is unchanged

### Requirement: Recall and connectivity
The system SHALL make the Inner Bailey the recall target, reject recall from
`no_recall` rooms, and connect the zones Keep↔Wilderness↔Caves↔Shrine.

#### Scenario: Recall returns to the Inner Bailey
- **WHEN** a player recalls from a recall-eligible room
- **THEN** the player arrives at the Inner Bailey of the Keep

#### Scenario: Deep rooms block recall
- **WHEN** a player attempts to recall from a `no_recall` room
- **THEN** the recall is refused

### Requirement: Cave of the Unknown stub
The system SHALL ship the Cave of the Unknown as a sealed stub with an entrance and
no mobs, reserving full content for a later release.

#### Scenario: Unknown builds as a sealed stub
- **WHEN** the Cave of the Unknown is built
- **THEN** it has a sealed entrance, flavor rooms, and no mob spawns
