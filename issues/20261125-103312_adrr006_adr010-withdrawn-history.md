# Convert the withdrawn ADR-010 text to non-normative history

## Priority
Medium

## Summary
ADR-010 is `Withdrawn` but still carries present-tense Summary, Decision, Invariants, and Failure Policy text, which the documentation policy says must be tracked as a Canonical Source Conflict; the inventory is empty and the withdrawal reference points to a non-repository file.

## Background
Verified against master on 2026-11-25 (source: local note `memo-issue.md`, issue 007):
- Confirmed: `docs/10_adr/adr_02_06_010_rag-fallback.md` keeps `## Summary` ("Canonicalizes the automatic fallback..."), `## Decision` (Decision Details 1-5 in present tense), `## Invariants` (INV-01 to INV-06), and `## Failure Policy`. Its `## Status` says the text remains as the record of the withdrawn decision.
- Confirmed: `governance_01_documentation-policy.md:273-275` says present-tense decision wording that survives in a Withdrawn ADR "is tracked as a Canonical Source Conflict", and Part 3 of `governance_03` reports "No active Canonical Source Conflict items remain".
- Confirmed: the `Withdrawal Reference` cites "Task `memo-issue.md` (Part 1, AAL-013)" (`adr_02_06_010_rag-fallback.md:290`); `memo-issue.md` is gitignored and untracked, so the reference is not durable.
- Confirmed: the ADR states it owns no authority target or edge in `config/adr_authority.toml`.

## Problem
A reader or parser can take the withdrawn fallback rules as current requirements, and the policy-required tracking and a durable withdrawal reference are missing.

## Reason for Change
The file contradicts ADR-004 Decision Group 10 (no fallback) if read as authoritative.

## Implementation Intent
Preserve history while removing active-looking authority: rewrite the withdrawn content as historical, past-tense material under a `Withdrawn Decision History` heading, register and then close a Canonical Source Conflict, and replace the weak reference with durable repository evidence.

## Target Files or Areas
- `docs/10_adr/adr_02_06_010_rag-fallback.md`
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- `config/adr_authority.toml` (verify only; no active edge is expected)

## Required Changes
- Rewrite the Summary, Decision, Invariants, and Failure Policy as historical text and remove current `MUST` wording.
- Register a Canonical Source Conflict entry while the text is being converted, and remove it with validation evidence when closed.
- Replace the `memo-issue.md` withdrawal reference with a durable repository reference supplied by the maintainer.

## Constraints
- Do not alter the Withdrawal Approval Record's approver, date, or approval sentence; do not invent a reference.
- Keep the ADR's identity and file name; keep the Status section as the first-line contract requires.

## Acceptance Criteria
- ADR-010 cannot be read as current fallback authority; the authority model has no active ADR-010 edge.
- The conflict inventory records and then closes the item; `check_adr_structure.py`, `check_adr_reference.py`, `check_adr_preservation.py`, and `check_adr_authority.py` pass.

## Testing Expectations
Run the four ADR checkers and `check_canonical_source_conflicts.py`.

## Documentation Impact
ADR-010 and the governance conflict inventory.

## Out of Scope
- Reinstating or amending any fallback decision.

## Dependencies
- N/A: none (may run in parallel with other ADR work; coordinate on `governance_03` edits).

## Unresolved Questions
- `不明`: the durable repository evidence for the withdrawal (the maintainer must provide it; the current reference is a local task file).

## AI Implementation Instruction
Do not write approval text or invent a reference; stop and ask for the durable reference.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-103312
- **Related target files**: `docs/10_adr/adr_02_06_010_rag-fallback.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
