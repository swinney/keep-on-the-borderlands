## ADDED Requirements

### Requirement: Standard respawn
The system SHALL respawn a killed standard mob at its spawn point after the
configured respawn delay (default 15 minutes), reconciled on a manager tick, only
while the mob's tribe is not halted.

#### Scenario: Cleared room refills after the delay
- **WHEN** a standard mob is killed and `STANDARD_RESPAWN` elapses
- **THEN** the mob is re-instantiated at its spawn point

### Requirement: Leadership halt requires both leaders
The system SHALL halt a tribe's repop for `LEADERSHIP_HALT` (60 minutes) only when
the chief and shaman are dead simultaneously; killing one alone has no halting
effect.

#### Scenario: One leader does not halt the tribe
- **WHEN** only the chief is killed
- **THEN** the tribe continues repopping and the chief respawns after the standard delay

#### Scenario: Both leaders dead triggers the halt
- **WHEN** the shaman is killed while the chief is already dead
- **THEN** the tribe's repop is halted for 60 minutes and a zone broadcast fires

#### Scenario: Nothing repops during a halt
- **WHEN** a tribe is within its halt window
- **THEN** no member of that tribe, including its leaders, respawns

#### Scenario: Halt expiry regroups the tribe
- **WHEN** the halt window expires
- **THEN** the full tribe respawns with fresh leaders

### Requirement: Halt drives faction tension
The system SHALL apply the faction `leadership_broken` effect (raising tension
with each rival) when a leadership halt triggers.

#### Scenario: Broken leadership raises rival tension
- **WHEN** a leadership halt triggers
- **THEN** tension between the broken tribe and each rival increases per the faction rules

### Requirement: Rival scouting parties
The system SHALL spawn rival-faction scouting mobs into a halted tribe's lair, and
retreat survivors when the halt expires.

#### Scenario: Rivals occupy the empty lair
- **WHEN** a tribe is halted
- **THEN** `SCOUT_PARTY_SIZE` mobs of the designated rival faction spawn in its lair rooms

#### Scenario: Scouts count as the rival faction
- **WHEN** a player kills a scouting mob
- **THEN** the player's standing changes with the rival faction, not the broken tribe

#### Scenario: Scouts withdraw on regroup
- **WHEN** the halt window expires
- **THEN** surviving scouts despawn as the original tribe regroups

### Requirement: Shrine reset cycle
The system SHALL reset the Shrine zone wholesale every `SHRINE_RESET` (24 hours)
with a server-wide broadcast.

#### Scenario: Daily Shrine reset broadcasts
- **WHEN** 24 hours elapse since the last Shrine reset
- **THEN** all Shrine mobs respawn and a server-wide broadcast fires

### Requirement: Reset on season boundary
The system SHALL clear all respawn timers, halt windows, and scouting parties at a
season reset and re-instantiate spawn points from zone data.

#### Scenario: Season reset clears repop state
- **WHEN** a season reset occurs
- **THEN** all timers and halts are cleared and the world is rebuilt from zone data
