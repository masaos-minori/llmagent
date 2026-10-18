# Detect multiple primary canonical sources per area in unregistered prose

## Priority
Medium

## Summary
Governance rule GV-010 forbids having multiple primary canonical sources within the same area. Registered claims are validated by `check_canonical_source_registry.py` (GV-019), but prose in `docs/*.md` that designates more than one document as the primary source for an area, without registration, is not detected. Extend detection to cover unregistered prose and mark GV-010 `Existing`.

## Background
`governance_04_documentation-checks.md` maps GV-010 ("Multiple Primary Canonical Sources within the same area") to human review, noting registered claims are checked by GV-019 and the rest is manual. Status is `Partial`. This is distinct from GV-009 (duplicate specification of a single canonical document): GV-010 concerns several *different* documents each claimed as the primary source for one area.

## Problem
Prose can designate multiple documents as the primary/canonical source for the same area or subsystem without registering any of them, so competing primary sources coexist undetected outside the registry's single-normative-source enforcement.

## Reason for Change
GV-010 is a Warning-level gate; undetected multiple primary sources per area create ambiguity about which document governs an area. Automating detection closes the documented `Partial` gap.

## Implementation Intent
Extend the prose-scan infrastructure introduced for GV-009 to group canonical/normative claims by area (subsystem/topic) and flag any area for which more than one document is designated as a primary source. Reuse the GV-009 scanner rather than duplicating it.

## Target Files or Areas
The checker introduced for GV-009 (`tools/`); `docs/00_governance/governance_04_documentation-checks.md` (GV-010 row `Partial` → `Existing`); read-only reference to `config/documentation_canonical_sources.toml`.

## Required Changes
- Group unregistered canonical/normative prose claims by area.
- Flag areas with more than one designated primary source.
- Update the GV-010 matrix row to `Existing` and clear its Follow-up note.

## Constraints
- Must distinguish a "primary canonical source for an area" from secondary or supporting references.
- Avoid false positives on incidental mentions.
- Do not change the Canonical Source Registry schema or GV-019 behavior.
- Non-blocking, warning-level gate.

## Acceptance Criteria
- The tool flags areas with multiple primary-canonical prose designations.
- No false positives on the current `docs/` corpus.
- GV-010 matrix row is marked `Existing`.

## Testing Expectations
Unit tests with single-primary and multi-primary fixtures; run against the full `docs/` corpus.

## Documentation Impact
`governance_04_documentation-checks.md`: GV-010 row status `Partial` → `Existing`, Follow-up column cleared.

## Out of Scope
Changing the registry schema or GV-019. Handling GV-009 (duplicate single-document specification) — that is the sibling issue introducing the shared prose scan.

## Dependencies
GV-009 (`20261018-173010_gov009_...`): this issue reuses the prose-scan infrastructure GV-009 introduces. Implement GV-009 first, then verify GV-010 against the shared scanner.

## Unresolved Questions
How to define an "area" boundary for grouping (directory, subsystem topic, or claim-type)? Define the grouping key before implementing.

## AI Implementation Instruction
Reuse the GV-009 prose scanner; do not fork it. Define a clear area-grouping key and add both single-primary and multi-primary fixtures. Do not modify the registry schema or `check_canonical_source_registry.py`.

## Traceability
- Workflow phase: issue-creator
- Source issue: N/A: this document is the issue
- Source requirement: N/A: no standalone requirement document is generated
- Source plan: N/A: not filed from a Plan
- Source implementation procedure: N/A: not filed from an implementation procedure
- Generated at: 2026-10-18
- Related target files: `tools/` (GV-009 prose-scan checker), `docs/00_governance/governance_04_documentation-checks.md`
