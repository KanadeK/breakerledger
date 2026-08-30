# BreakerLedger prior-art scan

Date: 2026-08-30

## Question

Is there room for a small open-source tool that compiles already-collected
breaker test observations into an evidence-backed panel directory, detects
contradictory mappings, and produces a targeted retest queue?

## Local-project exclusion

The workspace inventory was checked before selecting this idea. Existing
projects cover power-strip placement, USB-C capability paths, standby-load
analysis, battery rotation, appliance manuals, household inventory, labels,
and many unrelated specialist workflows. None found in the workspace compiles
breaker-to-endpoint field observations or diagnoses contradictory circuit
mappings.

## Public alternatives sampled

| Project or product | What it does | Why BreakerLedger is materially different |
| --- | --- | --- |
| [Electrical-Panel-Label-Generator](https://github.com/SenMorgan/Electrical-Panel-Label-Generator) | Designs printable DIN-rail breaker labels. | Starts from a directory the user already trusts; it does not reconcile test evidence or prescribe retests. |
| [energy-monitor](https://github.com/MCheli/energy-monitor) | Maps CT channels to breakers for one ESP32/ATM90E32 energy-monitor stack and prints a wall reference. | Hardware-specific calibration and visualization; BreakerLedger is hardware-independent and consumes human field observations. |
| [ha-electric-panel-card](https://github.com/quky/ha-electric-panel-card) | Visualizes compatible power sensors in Home Assistant. | Live smart-panel display rather than offline evidence compilation. |
| [hearth](https://github.com/R055LE/hearth) | Tracks floorplans, circuits, maintenance, and vendors in a self-hosted home database. | Broad home-information system; no observation-level contradiction model or deterministic retest artifact was found in the sampled description. |
| [Breaker Box](https://play.google.com/store/apps/details?id=net.bpi.breakerbox) | Commercial mobile directory with rooms, fixtures, panel layouts, and PDF legends. | Validates demand for a panel directory, but its public feature set centers on data entry, sync, and printing rather than evidence conflicts and CI-friendly failure exits. |

GitHub's `breaker-panel` topic listed only three public repositories in the
sampled page. Searches for CSV observation reconciliation, contradiction
detection, and retest planning did not surface a highly similar repository.
This is a bounded search, not proof that no private or unindexed project exists.

## Recommended direction

Build `BreakerLedger` as a dependency-free Python CLI. Users maintain three
plain CSV files: breakers, endpoints, and observations made while one breaker
was known to be off. The compiler preserves counts instead of inventing a
probability, assigns explicit statuses, and emits machine-readable and
printable artifacts.

The useful wedge is not “another panel-label app.” It is the shortest path
from messy notebook observations to an auditable answer to:

1. Which mappings have repeated supporting observations?
2. Which endpoint is claimed by more than one breaker?
3. Which breaker/endpoint pair has directly contradictory results?
4. What should be retested next?

## Assumptions and validation

- People will accept CSV when the output and error messages are strong. The
  committed examples and one-command demo test this assumption.
- Two supporting observations are useful as a default “confirmed” threshold.
  The count remains visible and the threshold is configurable.
- Deterministic offline reports are more valuable here than accounts or cloud
  sync. The release intentionally contains no network code.

## Not doing

- Electrical design, code compliance, load calculations, or wire sizing.
- Instructions for opening panels or working on energized equipment.
- Smart-breaker control, Home Assistant integration, or CT calibration.
- OCR, photo recognition, mobile UI, cloud sync, or collaboration accounts.
- A confidence percentage that would imply statistical certainty not present
  in simple field observations.

