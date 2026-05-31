## ADDED Requirements

### Requirement: Death dispatch by mode
The system SHALL route a player reaching 0 HP to default death or hardcore death
based on the character's irrevocable hardcore flag.

#### Scenario: Default character takes the corpse-run path
- **WHEN** a non-hardcore character reaches 0 HP
- **THEN** the default-death flow runs (XP loss + corpse + revive)

#### Scenario: Hardcore character takes the permadeath path
- **WHEN** a hardcore character reaches 0 HP
- **THEN** the hardcore-death flow runs (corpse + leaderboard + deletion)

### Requirement: Default death XP loss
The system SHALL set a defaulted character's XP to the start-of-level threshold
without de-leveling, flooring at that threshold.

#### Scenario: In-level progress is lost
- **WHEN** a character with mid-level XP dies by default
- **THEN** its XP is set to the current level's start threshold and its level is unchanged

#### Scenario: No progress means no loss
- **WHEN** a character at exactly the level threshold dies by default
- **THEN** its XP is unchanged

### Requirement: Corpse and recovery
The system SHALL create a corpse at the death room holding all gear and carried
coin, move the character to the Inner Bailey at 1 HP, and allow recovery by
looting the corpse. Banked wealth SHALL never be placed in the corpse.

#### Scenario: Gear goes to the corpse
- **WHEN** a default death occurs
- **THEN** a corpse in the death room holds the character's equipped items, inventory, and carried coin

#### Scenario: Revive at the recall point
- **WHEN** a default death occurs
- **THEN** the character is at the Inner Bailey with 1 HP and no memorized spells

#### Scenario: Bank is safe
- **WHEN** a default death occurs
- **THEN** the character's bank balance is unchanged and absent from the corpse

#### Scenario: Looting restores gear
- **WHEN** the player returns and loots the corpse
- **THEN** the gear and coin return to the player

### Requirement: Hardcore permadeath
The system SHALL, on hardcore death, drop a lootable corpse, append a `fell`
leaderboard entry with the final level and season, broadcast, and delete the
character.

#### Scenario: Hardcore death deletes the character
- **WHEN** a hardcore character dies
- **THEN** the character is deleted and does not return

#### Scenario: Hardcore death records the fall
- **WHEN** a hardcore character dies
- **THEN** a `fell` leaderboard entry with its final level and season is appended

### Requirement: Hardcore flag and marker
The system SHALL set the hardcore flag irrevocably at creation and display a
who-list marker for hardcore characters.

#### Scenario: Flag cannot be cleared
- **WHEN** any command attempts to clear the hardcore flag after creation
- **THEN** the flag remains set

#### Scenario: Hardcore shows on the who list
- **WHEN** a hardcore character appears on the who list
- **THEN** a hardcore marker is shown
