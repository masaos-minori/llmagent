# Detect duplicate canonical document specification in unregistered prose

## Priority
Medium

## Summary
Governance rule GV-009 forbids specifying a canonical document more than once per area. Registered claims are validated by `check_canonical_source_registry.py` (GV-019), but prose in `docs/*.md` that asserts a source is canonical without registering it in `config/documentation_canonical_sources.toml` is not detected. Extend detection to cover unregistered canonical claims and mark GV-009 `Existing`.

## Background
`governance_04_documentation-checks.md` maps GV-009 ("Duplicate canonical document specification") to human review, noting that registered claims are checked by GV-019 while the remainder is manual. Its status is `Partial`. GV-019 enforces single-normative-source-per-claim-type only for entries present in the Canonical Source Registry.

## Problem
An author can state in prose that "X is the canonical source for topic Y" without adding X to the registry. Such unregistered canonical claims bypass GV-019 entirely, so competing or duplicate canonical specifications can coexist undetected.

## Reason for Change
GV-009 is a Warning-level gate; undetected duplicate canonical prose creates ambiguity about which document governs a given claim type. Automating detection of unregistered canonical claims closes the documented `Partial` gap without changing the registration process.

## Implementation Intent
Add a heuristic scan across `docs/*.md` for sentences asserting canonical/normative status (conservative patterns such as "the canonical source for", "is the normative reference for", "authoritative source for") and flag any such claim whose claim type or topic is already covered by a registered source in the Canonical Source Registry or by another prose claim. This complements GV-019; it does not redefine what counts as registered.

## Target Files or Areas
A new or extended checker under `tools/` (e.g. alongside `check_canonical_source_registry.py`); `docs/00_governance/governance_04_documentation-checks.md` (GV-009 row `Partial` → `Existing`); read-only reference to `config/documentation_canonical_sources.toml`.

## Required Changes
- Scan `docs/*.md` for conservative canonical-assertion patterns.
- Flag claims whose topic/claim-type overlaps a registered source or another prose claim.
- Update the GV-009 matrix row to `Existing` and clear its Follow-up note.

## Constraints
- Pattern matching must avoid false positives on incidental uses of the word "canonical".
- Do not change the Canonical Source Registry schema or the behavior of `check_canonical_source_registry.py` (GV-019).
- The check should be warning-level and non-blocking, consistent with GV-009's existing gate.

## Acceptance Criteria
- The tool flags genuine duplicate/unregistered canonical prose claims.
- No false positives on the current `docs/` corpus.
- GV-009 matrix row is marked `Existing`.

## Testing Expectations
Unit tests with duplicate-claim and benign-mention fixtures to bound the false-positive rate; run the checker against the full `docs/` corpus.

## Documentation Impact
`governance_04_documentation-checks.md`: GV-009 row status `Partial` → `Existing`, Follow-up column cleared.

## Out of Scope
Changing the Canonical Source Registry schema or GV-019 behavior. Handling GV-010 (multiple primary sources in the same area) — that is a separate issue.

## Dependencies
`config/documentation_canonical_sources.toml` (the registry GV-019 validates against).

## Unresolved Questions
Which textual patterns reliably signal a canonical claim versus incidental use of "canonical"? Define a conservative, reviewed pattern set before implementing.

## AI Implementation Instruction
Start from a conservative pattern set and tune against the current `docs/` corpus to eliminate false positives. Do not modify the registry schema or `check_canonical_source_registry.py`. Add both positive and negative fixtures.

## Traceability
- Workflow phase: issue-creator
- Source issue: N/A: this document is the issue
- Source requirement: N/A: no standalone requirement document is generated
- Source plan: N/A: not filed from a Plan
- Source implementation procedure: N/A: not filed from an implementation procedure
- Generated at: 2026-10-18
- Related target files: `tools/` (new or extended canonical-claim checker), `docs/00_governance/governance_04_documentation-checks.md`
