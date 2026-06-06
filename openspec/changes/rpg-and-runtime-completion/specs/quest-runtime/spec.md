## ADDED Requirements

### Requirement: Quest-givers are resolved by an explicit giver key

Quest-givers SHALL be identified by an explicit quest-giver key stored on the NPC,
distinct from the NPC's display `role`. `list`/`accept`/`turnin` SHALL resolve the
giver in the room by that key, so every giver defined in the quest config —
including the Hermit, the disguised Spy, the Provisioner, and tribe-chief givers —
is reachable, not only those whose display role happens to equal a giver key.

#### Scenario: A non-Guildmaster giver is reachable
- **WHEN** a player is in a room with a giver NPC whose display role is not its giver key (e.g. the Hermit or a tribe chief)
- **THEN** that giver's quests can be listed, accepted, and turned in

#### Scenario: Tribe-chief turn-in is defined
- **WHEN** a quest is given by a tribe chief (an NPC a player may also be there to kill)
- **THEN** the turn-in interaction is defined and does not depend on the chief's display role

### Requirement: Deed-completion world-event hooks

World events that complete deed-gated quests SHALL set the corresponding
completion flag when they occur. At minimum: the Shrine altar's destruction sets a
shrine-destroyed marker; delivering rations, escorting a captive home, and dropping
a spy package set their respective markers. These triggers SHALL fire from the
in-world events (not be left to manual flag-setting).

#### Scenario: A world event completes its deed
- **WHEN** the in-world event for a deed-gated quest occurs (e.g. the altar is destroyed, or a delivery carrier reaches its destination)
- **THEN** the matching deed-completion flag is set
- **AND** a quest gated on that deed becomes turn-in-able

### Requirement: Carrier objects for delivery/escort/package deeds

Delivery, escort, and spy-package deeds SHALL have carrier objects (the item to
deliver, the captive to escort, the package to drop) whose handling calls the
existing, tested deed hooks on reaching the destination.

#### Scenario: A delivery carrier completes the deed
- **WHEN** a delivery/escort/package carrier object reaches its destination
- **THEN** it invokes the deed-completion hook for that quest

### Requirement: Live spy giver-key on relocation

The live disguised-priest NPC SHALL carry the spy giver key both when it is
assigned to a chapel NPC each season and when it relocates to the Shrine on
exposure, so its quests remain resolvable through the relocation.

#### Scenario: Spy quests survive relocation
- **WHEN** the seasonal spy is assigned to a chapel NPC, and later when it relocates on exposure
- **THEN** the live spy NPC carries the spy giver key and its quests resolve

### Requirement: Quest count documentation is accurate

Documentation enumerating quests SHALL state the actual wired count (26), not the
stale "24".

#### Scenario: Docs match the wired quests
- **WHEN** `docs/specs/quests.md` and `docs/build-plan.md` state a quest count
- **THEN** the count matches the quests actually wired (26)
