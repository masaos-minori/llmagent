# Implementation: shared/events.py — ArtifactEvent data-only clarification (req 74)

## Goal

Remove ambiguity from `ArtifactEvent` by replacing the vague "no event bus yet"
phrase with explicit documentation that the type is data-only with no delivery system.

## Changes

### `scripts/shared/events.py`
- Replaced module docstring: "no event bus yet" → explicit statement that ArtifactEvent
  has no delivery system, no event bus, no consumers, and is a type annotation only

### `docs/06_shared_90_inconsistencies_and_known_issues.md`
- Updated UNIMPL-01 from "Unimplemented" to "RESOLVED (Option A — documented as data-only)"
- Added resolution text; changed recommended action to "None"
