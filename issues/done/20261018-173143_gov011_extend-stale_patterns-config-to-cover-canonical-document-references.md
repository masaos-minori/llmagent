# Extend stale_patterns to detect references to non-existent canonical documents

## Priority
Low

## Summary
Governance rule GV-011 requires that document references resolve to existing canonical documents. `check_docs_quality.py`'s `stale_patterns` custom rule and `check_docs_structure.py` currently miss references to non-existent canonical documents. Extend the `stale_patterns` configuration to detect these and mark GV-011 `Existing`.

## Background
`governance_04_documentation-checks.md` maps GV-011 ("References to non-existent canonical documents") to `check_docs_structure.py` + `check_docs_quality.py`, gate `Warning`, status `Partial`, with the follow-up "Extend `stale_patterns` custom rule config". The `stale_patterns` custom rule in `check_docs_quality.py` covers several staleness cases but not references to canonical documents that do not exist in the corpus.

## Problem
A document can reference a canonical document path that was never created, removed, or renamed without being flagged, because `stale_patterns` does not cover this case and link-reachability alone may not distinguish canonical-document references from other internal links.

## Reason for Change
Dangling canonical references mislead readers and weaken the cross-reference graph. Extending `stale_patterns` closes the documented `Partial` gap at the existing `Warning` severity.

## Implementation Intent
Add a `stale_patterns` entry to `check_docs_quality.py` that flags references whose target canonical document is absent from the corpus (or points to a removed/renamed path). Coordinate with `check_docs_structure.py` link-reachability so the two checks do not duplicate each other.

## Target Files or Areas
`tools/check_docs_quality.py` and its `stale_patterns` custom-rule config; `docs/00_governance/governance_04_documentation-checks.md` (GV-011 row `Partial` → `Existing`).

## Required Changes
- Add a `stale_patterns` rule detecting references to non-existent canonical documents.
- Avoid duplicating `check_docs_structure.py` link-reachability.
- Update the GV-011 matrix row to `Existing` and clear its Follow-up note.

## Constraints
- Must not produce false positives on legitimate cross-domain links or templated/placeholder references.
- Keep the gate at `Warning` severity (GV-011 is non-blocking).

## Acceptance Criteria
- The tool flags dangling canonical-document references.
- No false positives on the current `docs/` corpus.
- GV-011 matrix row is marked `Existing`.

## Testing Expectations
Unit tests with dangling and valid-reference fixtures; run `check_docs_quality.py` against the full `docs/` corpus.

## Documentation Impact
`governance_04_documentation-checks.md`: GV-011 row status `Partial` → `Existing`, Follow-up column cleared.

## Out of Scope
Changing link-reachability behavior in `check_docs_structure.py`. Handling other `stale_patterns` gaps beyond canonical-document references.

## Dependencies
Current `stale_patterns` configuration and extension mechanism in `tools/check_docs_quality.py`.

## Unresolved Questions
Which references count as "canonical document references" versus general internal links? Define the precise scope before implementing.

## AI Implementation Instruction
Add the detection to the `stale_patterns` config in `check_docs_quality.py`; do not rewrite `check_docs_structure.py`. Add both dangling and valid fixtures. Confirm no new false positives across the corpus.

## Traceability
- Workflow phase: issue-creator
- Source issue: N/A: this document is the issue
- Source requirement: N/A: no standalone requirement document is generated
- Source plan: N/A: not filed from a Plan
- Source implementation procedure: N/A: not filed from an implementation procedure
- Generated at: 2026-10-18
- Related target files: `tools/check_docs_quality.py`, `docs/00_governance/governance_04_documentation-checks.md`
