## ADDED Requirements

### Requirement: Season cadence
The system SHALL run seasons of a configurable length defaulting to 6 weeks,
tracking a season number and start time.

#### Scenario: Season length is configurable
- **WHEN** the configured season length is changed
- **THEN** the next season boundary is computed from the new length

### Requirement: Persist vs reset boundary
The system SHALL preserve all player-attached data (character, level, XP, gear,
bank, hardcore flag, leaderboard) and reset all world-manager and zone-built state
at a season boundary.

#### Scenario: Player data survives reset
- **WHEN** a season reset occurs
- **THEN** each character's level, XP, gear, and bank balance are unchanged

#### Scenario: World state is reset
- **WHEN** a season reset occurs
- **THEN** faction states, repop timers, the disguised-priest assignment, and Shrine state are reset

### Requirement: Reset orchestration
The system SHALL run a deterministic reset sequence that invokes each world
manager's reset hook, reverts season-global quest effects, rebuilds zone
instances, advances the season number, and broadcasts.

#### Scenario: Reset invokes every manager hook
- **WHEN** the reset sequence runs
- **THEN** the faction, repop, and priest managers and the Shrine each reset

#### Scenario: Faction tension reseeds to the matrix
- **WHEN** the reset sequence runs
- **THEN** tribe-pair tension is restored to the initial B2 matrix and standings clear

#### Scenario: Season number advances
- **WHEN** the reset sequence completes
- **THEN** the season number increments and a new-season broadcast fires

### Requirement: Leaderboard with both scopes
The system SHALL maintain an append-only leaderboard exposing a per-season view
and an all-time view, recording hardcore deaths immediately and survivors at the
reset snapshot.

#### Scenario: Reset snapshots survivors
- **WHEN** a season reset occurs
- **THEN** surviving characters' standings are snapshotted to the closing season's board

#### Scenario: Hardcore death records immediately
- **WHEN** a hardcore character dies mid-season
- **THEN** a `fell` entry with its final level is appended at once

### Requirement: Warning broadcasts
The system SHALL broadcast season-end warnings ahead of the boundary.

#### Scenario: Warnings precede reset
- **WHEN** the season approaches its boundary
- **THEN** warning broadcasts fire at T−24h and T−1h

### Requirement: Early end
The system SHALL allow a season-global quest to end the season early via an
`end_season` trigger that runs the full reset sequence immediately.

#### Scenario: Destroying the Shrine ends the season
- **WHEN** the Shrine-destruction quest fires `end_season`
- **THEN** the reset sequence runs immediately with a bespoke broadcast
