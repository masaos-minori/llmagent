# docs/adr-index.md still describes ADR-004's pre-revision title, status, and Local-mode invariants

## Priority
Medium

## Summary
`docs/adr/ADR-004-environment-profile-fail-fast-fail-open.md` was renamed to "ADR-004:
Production Failure-Handling Policy", changed from Proposed to Accepted, and redefined as a
Production-only model with no Local mode. `docs/adr-index.md`'s ADR List entry and several
Invariant Verification Matrix rows still describe the pre-revision title, status, and
Local-mode concepts.

## Background
Discovered while confirming ADR-004's revision did not leave any related document
inconsistent. `docs/adr-index.md` is explicitly out of scope for direct editing during that
revision (only ADR-004 itself was in scope), with a note to report required follow-ups
instead — this issue is that follow-up.

## Problem
`docs/adr-index.md`'s ADR List table (Evidence: Explicit in code) still shows:
- Title: "Environment Profile別障害方針 — Fail-Fast/Fail-Open" (the pre-revision title)
- Status: "Proposed" (the pre-revision status; ADR-004 is now Accepted)

The ADR Invariant Verification Matrix contains four rows referencing ADR-004 that describe
concepts the revision removed:
- INV-011: "Local safety-related checks fail closed despite general fail-open" — assumes a
  "general fail-open" mode that no longer exists.
- INV-019: "Missing config fails close in all modes" — "in all modes" implies multiple modes exist.
- INV-020: "Local safety checks fail close" — describes a "local mode" that ADR-004 no longer supports.
- INV-010: "Production mode fails fast on health-check failure" — this one remains broadly
  consistent with the revision but should be re-checked against the revised Invariant numbering
  (ADR-004's own Invariants are now INV-01 through INV-10 within the ADR document itself,
  distinct from this cross-ADR matrix's INV-010/011/019/020 numbering — Evidence: Needs
  confirmation whether this numbering collision is intentional or should be clarified).

## Reason for Change
An ADR index that shows the wrong title and status for an Accepted ADR misleads anyone using
`docs/adr-index.md` as the canonical list (per its own Purpose statement) to look up current
ADR status. Invariant rows describing a removed Local mode are actively misleading about what
the current architecture requires.

## Implementation Intent
Update the ADR List row for ADR-004 to the current title and Accepted status. Rewrite
INV-011, INV-019, and INV-020 to describe the current Production-only, single-Fail-Fast model
(or fold them into INV-010 / a smaller set of rows if the revision reduced the number of
distinct invariants worth tracking at this cross-ADR granularity). Re-verify each row's
"Verification Status" column against current code, since the underlying claim changed.

## Target Files or Areas
- `docs/adr-index.md` — primary target (ADR List row, Invariant Verification Matrix rows INV-010, INV-011, INV-019, INV-020)
- `docs/adr/ADR-004-environment-profile-fail-fast-fail-open.md` — read-only reference for the current title, status, and Invariants (INV-01 through INV-10)

## Required Changes
- Update the ADR List table's ADR-004 row: Title → "Production Failure-Handling Policy", Status → "Accepted".
- Rewrite INV-011, INV-019, and INV-020 to state the current invariant content without Local-mode language, referencing the corresponding ADR-004 INV-XX identifier from the ADR document itself where a direct mapping exists.
- Re-verify INV-010's "Verification Status" column text against current code, since it was written under the pre-revision model.
- Decide whether the four rows should be consolidated (since ADR-004 no longer distinguishes production/local, some of the four may now describe the same invariant) or kept separate with corrected wording — record the decision made.

## Constraints
- Do not change the Invariant Verification Matrix's column structure or the matrix's format for other ADRs' rows.
- Do not renumber unrelated INV IDs; only correct the four ADR-004 rows' content (per this repository's established practice of preserving existing IDs rather than renumbering — see the governance-policy precedent for GV rule IDs).
- Do not modify ADR-004 itself in this issue — it is already updated; this issue only aligns the index.

## Acceptance Criteria
- The ADR List's ADR-004 row shows "Production Failure-Handling Policy" and "Accepted".
- No Invariant Verification Matrix row for ADR-004 contains "local mode", "general fail-open", "in all modes", or other Local-mode language.
- Each remaining ADR-004 invariant row's Verification Status accurately reflects current code (re-verified, not carried over unchanged).
- `uv run python tools/check_docs_quality.py docs/adr-index.md` and `uv run python tools/check_docs_structure.py docs/adr-index.md` show no new issues introduced by this change.

## Testing Expectations
Documentation-only change; not required beyond the validation commands listed above.

## Documentation Impact
This issue is itself the documentation-accuracy fix for `docs/adr-index.md`.

## Out of Scope
- Modifying ADR-004 or any other ADR file.
- Changing the Invariant Verification Matrix's structure for ADRs other than ADR-004.
- Resolving the ADR Dependency Graph's circular-dependency notes (`CDR-1`/`CDR-2`/`CDR-3`), which are unrelated to this revision.

## Dependencies
Follows the ADR-004 revision to "Production Failure-Handling Policy" (Accepted status, Production-only model).

## Unresolved Questions
- Whether the cross-ADR Invariant Verification Matrix's `INV-010`/`INV-011`/`INV-019`/`INV-020` numbering is meant to correspond one-to-one with ADR-004's own `INV-01`–`INV-10` numbering, or is an independent numbering space — needs confirmation before deciding whether to consolidate rows or map them explicitly.

## AI Implementation Instruction
- Read the current `docs/adr/ADR-004-environment-profile-fail-fast-fail-open.md` in full before rewriting any index row — do not paraphrase from memory of the prior revision task.
- Re-verify each Verification Status cell against actual current code rather than copying the existing cell text forward.
- Do not touch index rows or matrix rows for any ADR other than ADR-004.
- If the INV numbering question cannot be resolved with reasonable confidence, record it under Unresolved Questions rather than guessing at a mapping.
