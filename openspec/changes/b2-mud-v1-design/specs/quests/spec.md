## ADDED Requirements

### Requirement: Quest lifecycle and state
The system SHALL track quest state per character through `available → active →
complete` (and `failed`), with repeatable bounties returning to `available` after
a cooldown and story quests remaining complete.

#### Scenario: A quest advances through its steps
- **WHEN** a player meets each step of an active quest
- **THEN** the quest becomes complete and rewards are granted

#### Scenario: Repeatable bounty resets after cooldown
- **WHEN** a repeatable bounty completes and its cooldown elapses
- **THEN** it returns to `available`

### Requirement: Prerequisite gating
The system SHALL gate quest availability on level, prior-quest completion, and
faction standing prerequisites.

#### Scenario: Unmet prerequisite hides the quest
- **WHEN** a player does not meet a quest's prereqs
- **THEN** the quest is not available

#### Scenario: Tribe quests require non-hostile standing
- **WHEN** a player at hostile standing approaches a tribe chief
- **THEN** the chief's quest is unavailable

### Requirement: Rewards and faction effects
The system SHALL grant the listed gp/xp/items on completion and apply the quest's
faction effects (`quest_aid`/`quest_harm` standing, `quest_aid_vs` pair tension).

#### Scenario: Completion applies standing deltas
- **WHEN** a player completes a quest that aids or harms a faction
- **THEN** the player's standing with that faction changes by the configured amount

#### Scenario: Tribe quest escalates a rivalry
- **WHEN** a player completes a tribe quest against a rival
- **THEN** tension between the two tribes increases toward war

### Requirement: The cult-aiding chain
The system SHALL flag the disguised priest's quests as cult-aiding and, on the
third completion, trigger a Caves ambush and raise the player's cult standing.

#### Scenario: Third spy quest springs the trap
- **WHEN** a player completes a third cult-aiding quest
- **THEN** a Caves ambush fires and cult standing rises

### Requirement: Season-global quests
The system SHALL make exposing the priest fire the global exposed event (on valid
evidence) and destroying the Shrine fire `end_season`.

#### Scenario: Exposing the priest is evidence-gated
- **WHEN** a player completes the expose-priest quest with valid evidence
- **THEN** the server-global exposed event fires

#### Scenario: Destroying the Shrine ends the season
- **WHEN** a player completes the destroy-Shrine quest
- **THEN** `end_season` fires and the reward is granted

### Requirement: Reset behavior
The system SHALL reset active quest progress tied to world state at a season
boundary while preserving quest completion history.

#### Scenario: Progress resets, history persists
- **WHEN** a season resets
- **THEN** world-tied active progress clears and completion history is retained
