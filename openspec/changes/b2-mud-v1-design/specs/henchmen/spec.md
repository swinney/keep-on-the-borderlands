## ADDED Requirements

### Requirement: Hiring from the tavern roster
The system SHALL let a player hire henchmen from a Keep-tavern roster, resolving
acceptance with an OSE reaction roll (`2d6 + CHA reaction`) and deducting the
hire fee on acceptance.

#### Scenario: Successful hire joins the party
- **WHEN** a player hires a recruit and the reaction roll accepts
- **THEN** the hire fee is deducted and the henchman joins the player's party

#### Scenario: Refused hire costs nothing
- **WHEN** the reaction roll refuses
- **THEN** no fee is charged and no henchman joins

### Requirement: Retainer cap
The system SHALL cap a player's henchmen at the OSE Charisma maximum-retainers
value, never exceeding a hard ceiling of 7.

#### Scenario: Cannot exceed the Charisma cap
- **WHEN** a player at their CHA-derived cap attempts another hire
- **THEN** the hire is refused

### Requirement: Following and orders
The system SHALL move a `follow`ing henchman with its employer and obey the order
set (follow, attack, guard, wait, retreat, dismiss).

#### Scenario: Henchman follows between rooms
- **WHEN** the employer moves to an adjacent room and the henchman is following
- **THEN** the henchman moves to the same room

### Requirement: Combat participation
The system SHALL have a henchman act on its own initiative each round, attacking
the employer's target by default.

#### Scenario: Henchman engages the employer's target
- **WHEN** combat is underway and the henchman has no overriding order
- **THEN** the henchman attacks the employer's current target

### Requirement: XP and treasure share
The system SHALL award participating henchmen a half share of XP (reducing the
employer's share) and let the player pay a negotiated treasure share, with payment
affecting loyalty.

#### Scenario: Half XP share reduces the employer's gain
- **WHEN** a kill grants XP with a henchman participating
- **THEN** the henchman receives a half share and the employer's share is reduced

#### Scenario: Shorting the share costs loyalty
- **WHEN** the player denies or underpays a henchman's treasure share
- **THEN** that henchman's loyalty decreases

### Requirement: Loyalty and morale
The system SHALL track loyalty on the OSE scale, adjust it per the event table,
and resolve morale as `2d6` against loyalty on triggers, with failure causing
flight or refusal.

#### Scenario: Failed morale routs the henchman
- **WHEN** a morale trigger fires and `2d6` exceeds loyalty
- **THEN** the henchman flees

#### Scenario: Low loyalty refuses a suicidal order
- **WHEN** a low-loyalty henchman is given an obviously suicidal order
- **THEN** the henchman refuses

### Requirement: Permadeath and re-hire
The system SHALL permanently remove a henchman that reaches 0 HP, drop its gear to
a corpse, free the party slot, and require re-hiring; henchmen do not persist
across a season reset.

#### Scenario: Dead henchman does not return
- **WHEN** a henchman reaches 0 HP
- **THEN** it is permanently removed and its party slot frees for a new hire

#### Scenario: Roster refreshes each season
- **WHEN** a season resets
- **THEN** the tavern roster refreshes and no prior henchmen persist
