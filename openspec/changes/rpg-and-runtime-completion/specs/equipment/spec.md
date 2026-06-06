## ADDED Requirements

### Requirement: Wield and wear gear

A character SHALL be able to equip carried gear: wield a weapon and wear armor
and a shield (likely via the Evennia `clothing` contrib). Equipping and removing
SHALL be player commands, and equipped state SHALL persist on the character.

#### Scenario: Equip and unequip
- **WHEN** a player wields a carried weapon and wears carried armor
- **THEN** those items are marked equipped on the character
- **AND** removing them clears the equipped state

### Requirement: Worn armor determines AC

A character's ascending armor class SHALL be `10 + DEX_mod + worn_armor_bonus +
shield_bonus`, replacing the current Dexterity-only computation. Unarmored AC SHALL
remain `10 + DEX_mod`.

#### Scenario: Armor raises AC
- **WHEN** a character wears armor (and/or a shield) with a defined AC bonus
- **THEN** its computed AC equals `10 + DEX_mod + armor_bonus + shield_bonus`

#### Scenario: Unarmored baseline
- **WHEN** a character wears no armor
- **THEN** its computed AC equals `10 + DEX_mod`

### Requirement: Equipped weapon determines melee damage

Melee damage SHALL use the equipped weapon's damage die (plus STR modifier,
minimum 1), replacing the `1d6` unarmed placeholder. With no weapon equipped,
damage SHALL fall back to the unarmed die.

#### Scenario: Weapon die drives damage
- **WHEN** a character with an equipped weapon lands a melee hit
- **THEN** damage is `weapon_die + STR_mod` (minimum 1), using that weapon's die

#### Scenario: Unarmed fallback
- **WHEN** a character with no weapon equipped lands a melee hit
- **THEN** damage uses the unarmed fallback die
