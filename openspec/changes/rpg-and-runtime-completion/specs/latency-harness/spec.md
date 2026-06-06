## ADDED Requirements

### Requirement: Wire-level concurrent latency harness

A load harness SHALL measure end-to-end command latency over the actual network
transport with 50 concurrent telnet clients connected to a running server,
replacing M16's in-process measurement (the ADR-0005 fallback). It SHALL report a
percentile summary (p50/p95) and SHALL be runnable on demand, not in the default
unit gate.

#### Scenario: 50-socket wire measurement
- **WHEN** the harness runs against a running server
- **THEN** it opens 50 concurrent telnet connections and drives commands over the wire
- **AND** it reports p50/p95 latency for the round trip

#### Scenario: Gated off the unit job
- **WHEN** the default unit test suite runs
- **THEN** the wire harness does not run (it requires a live server; opt-in like the deployment smoke tier)

### Requirement: Latency record updated

The acceptance latency record (ADR-0005 / acceptance spec) SHALL be updated to
reflect wire-level measurement rather than the in-process proxy once the wire
harness lands.

#### Scenario: ADR/spec reflects the real measurement
- **WHEN** the wire harness is the latency check
- **THEN** ADR-0005 and the acceptance spec note wire-level measurement as the realized approach
