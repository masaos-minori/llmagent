## Goal
Add a Temporary Exception Process (reason, owner, expiration date) to
`docs/00_governance_03_issue-and-uncertainty-management.md`, and record the
Blocking-vs-Warning classification decision for the `GV-020` removed-name
reintroduction detection rule's findings, since no such exception process exists
in either governance document today.

## Scope
- **In-Scope**: `docs/00_governance_03_issue-and-uncertainty-management.md`
  only — a new top-level section for the Temporary Exception Process.
- **Out-of-Scope**: `docs/00_governance_02_documentation-metadata.md` (seq 01),
  `docs/00_governance_04_documentation-checks.md` (seq 02, which records the
  actual `GV-020` Warning classification value in its own Governance
  Verification Matrix row and Merge Condition Validation section); Part 1 (Known
  Issues) and Part 2 (Needs Confirmation Inventory)'s own existing entries and
  lifecycle rules — unmodified by this row.

## Assumptions
- `docs/00_governance_03_issue-and-uncertainty-management.md` defines the Known
  Issue (Part 1) and Needs Confirmation (Part 2) lifecycles only, with no
  temporary-exception process (reason/owner/expiration-date) anywhere — re-verified
  2026-09-03 by full re-read, matching the Plan's own evidence with no drift.
- `docs/00_governance_04_documentation-checks.md`'s `GV-020` row (seq 02 of this
  Plan) already records the Blocking-vs-Warning decision as `Warning` in its own
  Gate column, and its Merge Condition Validation section already references an
  "approved temporary exception" pointing back to this document — this row
  defines what that exception record actually requires, completing that
  cross-reference.
- The file is 51,181+ bytes as of 2026-09-03 (before this row's edit), already
  exceeding `tools/check_docs_structure.py`'s 24576-byte `MAX_SIZE` — a
  pre-existing, out-of-scope condition tracked in
  `implementations/done/20260903-142052_03_...md`'s Blocker Log (from a separate
  Plan's row). This row's small addition is not the cause of that violation and
  does not attempt to fix it (out of scope for adding an exception process).

## Design decisions
- **New top-level section (`## Temporary Exception Process`), placed after Part 2
  and before `## Non-Goals`**, rather than nested inside Part 1 or Part 2 — the
  process applies to Warning-classified automated-check findings generally (e.g.
  `GV-020`), not specifically to Known Issues or Needs Confirmation items, so it
  is a peer section to both Parts rather than a subsection of either.
- **The exception record format is an inline HTML comment
  (`<!-- exception: {rule-id} — {reason} — {owner} — expires {date} -->`)**,
  matching this repository's existing convention of embedding checkable
  structures directly in the flagged file (the same pattern
  `tools/check_dependency_graph_cycles.py` and `check_needs_confirmation_inventory.py`
  already rely on for markdown-embedded, tool-parseable structures) rather than a
  separate exception-tracking document — this keeps the exception co-located with
  the finding it excepts, so a reader (or a future check script) does not need to
  cross-reference a second file to see why a specific line is excepted.
- **An expired exception is explicitly treated as an unexplained finding**, not
  silently still-covered — this closes the loop with
  `docs/00_governance_04_documentation-checks.md` `### 13. Merge Condition
  Validation`'s "every finding must be resolved or covered by an approved
  temporary exception" language (seq 02), so "approved" cannot be read as
  permanent.

## Alternatives considered
- **Track exceptions in a separate table within this document** (rather than an
  inline comment at the flagged line) — rejected: a separate table requires
  keeping two locations in sync (the flagged line and the tracking table) with no
  automated enforcement that they stay consistent; an inline comment is
  self-locating and cannot drift from the line it excepts.
- **Nest the process under Part 1 (Known Issues)**, since a Warning finding is
  conceptually similar to a Known Issue — rejected (see Design decisions): the
  process is scoped to any Warning-classified GV-matrix rule's findings, a
  broader category than Known Issues specifically, and nesting it under one Part
  would misleadingly suggest it does not apply to a future Warning-classified
  rule unrelated to Known Issues.

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Re-read the region around `## Non-Goals` (currently line 894, immediately
   preceded by Part 2's closing "No other active items..." sentence at line 892)
   immediately before editing to reconfirm no drift (done above; confirmed
   identical to the Plan's citation after re-verification, accounting for this
   session's separate NC-022–025 addition to Part 2 that shifted line numbers
   before this row was written).
2. Insert the new `## Temporary Exception Process` section between Part 2's
   closing sentence and `## Non-Goals`.

### Method
Direct text edit (e.g. via the `Edit` tool) inserting the new section at the
anchor point in Details below.

### Details

Before:
```
No other active items beyond NC-021 through NC-029 above.

## Non-Goals
```

After:
```
No other active items beyond NC-021 through NC-029 above.

## Temporary Exception Process

Applies to any automated check finding classified `Warning` (not `Blocking`) in
`docs/00_governance_04_documentation-checks.md`'s Governance Verification Matrix
— for example, `GV-020`'s removed-name reintroduction findings. A `Warning`
finding does not block merge by itself, but leaving it neither fixed nor formally
excepted is not a complete review (see `docs/00_governance_04_documentation-checks.md`
`### 13. Merge Condition Validation`).

### Exception Record Fields

A temporary exception must record all three of:
- **Reason**: why the finding is not being fixed now (e.g. the flagged usage is
  intentional and pending a separate follow-up issue).
- **Owner**: who accepted the exception — a specific person, not `Team` or
  `Unassigned`.
- **Expiration Date**: the date by which the exception must be re-reviewed or the
  underlying finding fixed. An exception with no expiration date is not valid.

### Recording an Exception

Record the exception inline, next to the flagged line, as:

`<!-- exception: {rule-id} — {reason} — {owner} — expires {YYYY-MM-DD} -->`

For example: `<!-- exception: GV-020 — read_json_file mention is a historical
comparison, not a current-spec claim — @agent-lead — expires 2026-12-01 -->`

An exception past its expiration date is treated as an unexplained finding (see
`docs/00_governance_04_documentation-checks.md` `### 13. Merge Condition
Validation`) — not as still-covered.

## Non-Goals
```

## Compatibility considerations
No other document links to `## Non-Goals` or the Part 2 closing sentence by
anchor in a way this insertion would disturb (the new section is inserted
between them, not replacing either). Depends conceptually on
`docs/00_governance_04_documentation-checks.md`'s `GV-020` row and Merge
Condition Validation addition (seq 02) for its cross-references to make sense in
context, but this row's own edit is syntactically valid whether applied before or
after seq 02.

## Security considerations
None — documentation-only addition of a governance process description; no code,
credentials, or access-control content is affected.

## Rollback considerations
Single-file, single-insertion change to a Markdown document under version
control; revert via `git revert`. No other file references this new section yet
(seq 02's cross-references point at it by name, not by a link that would break),
so rollback carries no cross-file follow-up beyond seq 02's prose becoming a
dangling reference until also reverted.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_03_issue-and-uncertainty-management.md | Automated doc quality check | `uv run python tools/check_docs_quality.py` | No new errors |
| docs/00_governance_03_issue-and-uncertainty-management.md | Manual cross-check | Re-read the new section | The exception process requires and documents a reason, an owner, and an expiration date (AC-7) |

## Completion criteria
- `docs/00_governance_03_issue-and-uncertainty-management.md` contains a
  Temporary Exception Process section requiring and documenting a reason, an
  owner, and an expiration date (AC-7, REQ-005).
- `uv run python tools/check_docs_quality.py` reports no new errors.

## Out of scope
`docs/00_governance_02_documentation-metadata.md` (seq 01),
`docs/00_governance_04_documentation-checks.md` (seq 02) — each has its own
implementation-procedure document per this Plan's Implementation Target Files
table. Fixing this file's own pre-existing 24576-byte size-limit violation — a
separate, already-tracked condition not caused by or in scope for this row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005
- **Source issue**: issues/done/20260902-143332_compatterms_standardize_compat_terminology_and_regression_checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-090945_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-152026
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
