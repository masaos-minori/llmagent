## Goal
Update `NC-038`'s `Status` field from `open` to `resolved` in
`docs/00_governance_03_issue-and-uncertainty-management.md`, per `REQ-005` (Plan
`plans/20260920-161148_plan.md`), per
`tools/check_needs_confirmation_inventory.py`'s inventory convention, once `REQ-004`
(the archived Plan's Step 4 update) has landed.

## Scope
In scope: the `NC-038` entry's `Status` field (line 856: `- **Status**: open`) only.
Out of scope: every other field of the `NC-038` entry (`Source File`, `Section`, `Line
Number`, `Question`, `Evidence`, `Impact`, `Required Action`, `Assigned To`, `Last
Reviewed`, `Priority`); every other NC entry in this file; any other section of this
file.

## Assumptions
`NC-038`'s `Status` field still reads `open` — re-confirmed via Read during this
document's creation (line 856, `docs/00_governance_03_issue-and-uncertainty-management.md`
is not an archive-directory file, so a fresh read is unrestricted here, unlike Row 3's
`plans/done/` target).

## Design decisions
Per `tools/check_needs_confirmation_inventory.py`'s inventory convention (cited
directly by `REQ-005`), update only the `Status` field value; also update `Last
Reviewed` to today's date, consistent with the entry's own existing field for tracking
when its state last changed (the entry already carries a `Last Reviewed` field for
exactly this purpose — updating it here is applying the entry's own established
convention, not introducing a new field). Do not remove the entry or its other
fields — resolved NC entries in this file are retained with `Status: resolved`, not
deleted (consistent with how other resolved NC entries in the same document are
handled, per general practice of an audit-trail inventory).

## Alternatives considered
- Delete the `NC-038` entry entirely once resolved: rejected — no evidence in this file
  that resolved entries are removed rather than marked `resolved`; deleting would lose
  the audit trail of what was asked and how it was resolved, which is exactly the
  historical record a Needs-Confirmation inventory exists to preserve.
- Also update `Evidence`/`Impact`/`Required Action` to describe the resolution:
  rejected as exceeding this row's scope — `REQ-005` names only the `Status` field
  update; substantively rewriting the entry's narrative fields is a separate editorial
  decision this Requirement does not authorize.

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Confirm `REQ-004` (Row 3: `plans/done/20260919-105034_plan.md`'s Step 4 marked
   `Completed`) has landed — this row's edit is explicitly gated on that per `REQ-005`'s
   own wording ("once REQ-004 lands").
2. Read the `#### NC-038` entry (lines 847-859) to confirm current content matches the
   Plan's recorded evidence, in particular that `Status` still reads `open`.
3. Edit line 856 from `- **Status**: open` to `- **Status**: resolved`.
4. Edit line 858 (`- **Last Reviewed**: 2026-09-19`) to today's date.
5. Leave every other field of the `NC-038` entry, and every other entry/section of
   this file, unchanged.

### Method
Two single-line `Edit` calls (steps 3 and 4) scoped to the `NC-038` entry only. Do not
touch any other `#### NC-` entry in this file.

### Details
`tools/check_needs_confirmation_inventory.py`'s inventory convention is the canonical
reference for what "resolved" means and how it is recorded — confirm this edit matches
that convention's expected format for a resolved entry (re-read the tool's help/source
if the exact expected format is unclear at implementation time; do not guess a format
inconsistent with what the checker validates).

## Compatibility considerations
`N/A: this is a governance tracking metadata update; no code, public interface, or data
format is affected`.

## Security considerations
`N/A: no security-relevant content is touched`.

## Rollback considerations
Revert via `git checkout` on this one file, restoring `NC-038`'s `Status` to `open`.
This edit is independently revertable from the other three Plan rows.

## Validation plan
- `uv run python tools/check_needs_confirmation_inventory.py` — confirm `NC-038` is
  recognized as resolved and no new inventory-consistency finding is introduced (Plan
  `AC-5`).
- `uv run python tools/check_docs_content_policy.py` and `uv run python
  tools/check_docs_structure.py` scoped to this file — confirm no new finding is
  introduced by this two-line edit.

## Completion criteria
`NC-038`'s `Status` field reads `resolved`; its `Last Reviewed` field reflects the date
of this edit; every other field of the entry and every other entry in this file is
unchanged; `tools/check_needs_confirmation_inventory.py` recognizes the entry as
resolved.

## Out of scope
- Every other field of the `NC-038` entry (see Scope) — not part of `REQ-005`.
- Every other `#### NC-` entry in this file.
- Any other section of `docs/00_governance_03_issue-and-uncertainty-management.md`.
- This step MUST NOT run before `REQ-004` lands (see Assumptions/Procedure step 1) —
  do not mark `NC-038` resolved before the archived Plan's Step 4 is confirmed
  `Completed`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-172437 | 20260920-172437 | Gated on REQ-004 completing first |
| 2 | Add or update tests per Validation plan | Completed | 20260920-172437 | 20260920-172437 | N/A: documentation-only, no automated test beyond `check_needs_confirmation_inventory.py` already listed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-172437 | 20260920-172437 | Scoped to the doc/inventory checkers in Validation plan, not the full Python toolchain (no `scripts/` change) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-172437 | 20260920-172437 | N/A: this document IS the documentation change |

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
- **Requirement ID**: `REQ-005` — update NC-038's Status field to resolved
- **Source issue**: issues/20260920-154806_memref01_resolve-nc-038-memory-reference-class-migration-target-and-wiring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-161148_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-164038
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md