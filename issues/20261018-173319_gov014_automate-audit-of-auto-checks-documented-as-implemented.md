# Automate audit of auto-checks documented as implemented

## Priority
Medium

## Summary
Governance rule GV-014 ("No unimplemented auto-checks documented as implemented") is currently enforced by manual periodic review. Automate an audit that cross-references every check documented as "Auto"/automatic against an actual runnable tool or script under `tools/` or `scripts/`, flagging any documented-but-absent implementation, and mark GV-014 `Existing`.

## Background
`governance_04_documentation-checks.md` maps GV-014 to human review on a periodic basis, status `Partial`, with the follow-up "Automate auto-check implementation audit (currently manual)". Auto-checks are recorded as `Method = Auto` in the Governance Verification Matrix and listed as automated in `routing.md`'s tool table.

## Problem
A checker can be documented as "Auto" while no corresponding runnable script exists, or its documented name has drifted from the actual tool filename. Implementers then believe enforcement exists when it does not, and manual review only catches this between sweeps.

## Reason for Change
GV-014 is a periodic `Warning` gate. Automating the audit keeps documentation honest about what is actually enforced and removes reliance on periodic manual sweeps.

## Implementation Intent
Build a checker that parses documents enumerating auto-checks (the GV matrix `Method = Auto` cells, `routing.md` tool entries) and verifies each referenced tool resolves to an existing, runnable script under `tools/` or `scripts/`. Flag documented-but-absent or name-drifted entries. Keep the check non-blocking and `Warning`-level.

## Target Files or Areas
A new checker under `tools/`; `docs/00_governance/governance_04_documentation-checks.md` (GV-014 row `Partial` → `Existing`); `routing.md` (read-only documented source of auto-checks).

## Required Changes
- Parse documented auto-check references from the authoritative documents.
- Verify each resolves to a runnable tool/script.
- Flag documented-but-absent or drifted entries.
- Update the GV-014 matrix row to `Existing` and clear its Follow-up note.

## Constraints
- Discover tools dynamically (list `tools/`/`scripts/`) rather than hardcoding names.
- Avoid false positives for checks invoked via mechanisms with different names (e.g. pre-commit hook names).
- Non-blocking, `Warning`-level gate.

## Acceptance Criteria
- The tool flags documented auto-checks with no runnable implementation.
- No false positives on the current corpus.
- GV-014 matrix row is marked `Existing`.

## Testing Expectations
Unit tests with documented-but-missing and valid entries; run against the current governance and routing documents.

## Documentation Impact
`governance_04_documentation-checks.md`: GV-014 row status `Partial` → `Existing`, Follow-up column cleared.

## Out of Scope
Changing which documents are considered authoritative sources of auto-check claims. Adding new auto-checks.

## Dependencies
The set of documents that enumerate auto-checks (`governance_04_documentation-checks.md`, `routing.md`).

## Unresolved Questions
Which documents are authoritative sources of "auto-check" claims, and how to disambiguate a genuinely absent check from a correctly-named-but-differently-invoked one? Define the parser's input set before implementing.

## AI Implementation Instruction
Identify the documents enumerating auto-checks, verify each reference resolves to a runnable script, and add both missing and valid fixtures. Keep the check non-blocking. Do not alter how checks are invoked.

## Traceability
- Workflow phase: issue-creator
- Source issue: N/A: this document is the issue
- Source requirement: N/A: no standalone requirement document is generated
- Source plan: N/A: not filed from a Plan
- Source implementation procedure: N/A: not filed from an implementation procedure
- Generated at: 2026-10-18
- Related target files: `tools/` (new checker), `docs/00_governance/governance_04_documentation-checks.md`
