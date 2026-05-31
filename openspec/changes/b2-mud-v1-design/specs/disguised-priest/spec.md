## ADDED Requirements

### Requirement: Seasonal rotating identity
The system SHALL assign the spy to exactly one chapel NPC at season start, chosen
randomly but never equal to the immediately preceding season's spy.

#### Scenario: Exactly one spy per season
- **WHEN** a season begins
- **THEN** exactly one NPC in the chapel pool is the spy

#### Scenario: No back-to-back repeat
- **WHEN** two consecutive seasons begin
- **THEN** the spy NPC differs between them

### Requirement: Clue assignment
The system SHALL attach a set of `CLUE_COUNT` distinct clues, drawn from the clue
pool, to the spy each season, each backed by an observable in-world tell.

#### Scenario: Clue set is drawn and attached
- **WHEN** a season begins
- **THEN** `CLUE_COUNT` distinct clues are attached to the spy NPC

#### Scenario: Resets re-roll the clue set
- **WHEN** two consecutive seasons begin
- **THEN** the spy identity differs and the clue set is re-drawn

### Requirement: Per-character investigation
The system SHALL track each player's clues and evidence on that player, requiring
one strong proof or three clue sightings before a report is allowed.

#### Scenario: Evidence is private to the player
- **WHEN** one player logs clue sightings
- **THEN** another player's evidence is unaffected

#### Scenario: Curate branch gates on clues
- **WHEN** a player has fewer than two logged clue sightings
- **THEN** the Curate does not share suspicions

### Requirement: Detection paths
The system SHALL provide Detect Evil, the Curate dialogue, witnessing a night act,
and finding a planted object as means of gathering evidence.

#### Scenario: Detect Evil distinguishes the spy
- **WHEN** a cleric of sufficient level casts Detect Evil on the spy versus an innocent NPC
- **THEN** the spy yields a strong proof and the innocent yields nothing

#### Scenario: Witnessing the night act logs a clue
- **WHEN** a player is present as the spy performs a nighttime tell at game-night
- **THEN** a clue sighting is logged for that player

### Requirement: Spy quest chain
The system SHALL let the unexposed spy offer cult-aiding quests; completing three
or more triggers a Caves ambush and raises the player's cult standing.

#### Scenario: Three spy quests spring the trap
- **WHEN** a player completes a third spy quest
- **THEN** a scripted Caves ambush fires and the player's cult standing rises

### Requirement: Global exposure
The system SHALL, on a sufficiently-evidenced report to the Castellan, set a
server-global exposed flag, broadcast, and relocate the spy to the Shrine as a
cult boss; insufficient evidence is rejected.

#### Scenario: Valid report exposes and relocates
- **WHEN** a player reports with one strong proof or three clue sightings
- **THEN** the exposed flag is set, a broadcast fires, and the spy becomes a Shrine boss

#### Scenario: Weak report is rejected
- **WHEN** a player reports without sufficient evidence
- **THEN** the report is rejected and no exposure occurs

### Requirement: Reset behavior
The system SHALL re-roll identity and clues, clear exposure and all per-character
evidence, and restore the chapel at each season boundary.

#### Scenario: Reset clears the plot
- **WHEN** a season resets
- **THEN** the spy is re-rolled, exposure clears, evidence clears, and the chapel is restored
