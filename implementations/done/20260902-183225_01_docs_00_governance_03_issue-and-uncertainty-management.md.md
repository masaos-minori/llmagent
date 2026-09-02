## Goal

Remove the stale `NC-019` entry (Requirement REQ-001) from
`docs/00_governance_03_issue-and-uncertainty-management.md`'s Active Items, since its
underlying gap is already fixed, and correct the section's trailing item-count sentence
to match.

## Scope

Modify exactly `docs/00_governance_03_issue-and-uncertainty-management.md`: delete the
`#### NC-019` entry block (all fields) from Part 2 Active Items, and update the trailing
"No other active items beyond NC-019 through NC-021 above." sentence to name only the
items that remain. No other file is touched.

## Assumptions

- Re-verified 2026-09-02: `#### NC-019` entry exists at line 96 with all fields (Source
  File, Section, Line Number, Question, Evidence, Impact, Required Action, Status: open,
  Assigned To, Last Reviewed, Priority, Related NC, Resolution Target, Blocking) through
  line 111; the trailing summary sentence "No other active items beyond NC-019 through
  NC-021 above." is present. No drift from the Plan's evidence.
- Per the governance document's own Needs-Confirmation lifecycle rule (full removal on
  resolution, not a `resolved` status value — that value does not exist in this
  document's Status Values list), `NC-019` must be deleted entirely, not marked
  resolved.

## Design decisions

Delete the entire `#### NC-019` block rather than converting it to a resolved-status
entry, per the Plan's `Implementation intent` (applying the governance doc's literal
lifecycle rule) — this was an explicit user decision for the source Issue, not an
assumption made in this document.

## Alternatives considered

Marking `NC-019`'s `Status` field as `resolved` instead of deleting the entry —
rejected: the governance document's own Status Values list does not include a
`resolved` value, and its lifecycle rule requires full removal once an item is
resolved, not a status flip (Plan `Implementation intent`).

## Implementation

### Target file

docs/00_governance_03_issue-and-uncertainty-management.md

### Procedure

Delete the `#### NC-019` entry block in its entirety, and reword the trailing
item-count sentence to name only `NC-020` and `NC-021`.

### Method

1. Delete the block from `#### NC-019` (line 96) through its final field
   (`- **Blocking**: No — tracked in parallel with Known Issue MCP-003`, line 111),
   including the blank line immediately preceding the heading if that would otherwise
   leave two consecutive blank lines.
2. Replace:
   ```
   No other active items beyond NC-019 through NC-021 above.
   ```
   with:
   ```
   No other active items beyond NC-020 and NC-021 above.
   ```

### Details

Only the `NC-019` entry and the one summary sentence are touched — `NC-020`'s own entry
(noted in the Plan's Out-of-Scope as a separate, unaddressed lifecycle question) is not
modified.

## Compatibility considerations

Documentation-only change; no code, schema, or runtime behavior affected.

## Security considerations

N/A: removing a resolved Needs-Confirmation entry has no security-relevant content of
its own — the underlying protected-branch bypass this entry referenced is already fixed
(commit `800aea33e`), verified independently by the sibling procedure document for
`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`.

## Rollback considerations

Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan

- `uv run python tools/check_needs_confirmation_inventory.py` — exits 0 with no
  `ERROR`/`WARNING` referencing this file (AC-004).
- `uv run python tools/check_docs_quality.py` and
  `uv run python tools/check_docs_structure.py` — no new issues for this file (AC-005).

## Completion criteria

`docs/00_governance_03_issue-and-uncertainty-management.md`'s Part 2 Active Items no
longer contains an `#### NC-019` heading or entry, and the trailing summary sentence
names only `NC-020` and `NC-021` (AC-001).

## Out of scope

`NC-020`'s own Active Items entry (`Status: fixed`) — noted during the Plan's inspection
as a separate, arguably-conflicting lifecycle question, but not part of the source
Issue's scope (Plan Out-of-Scope, UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `#### NC-019` entry block and reword item-count sentence per Method | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | Deleted NC-019 block; trailing summary already had NC-020/NC-021 wording |
| 2 | N/A: no test to add (doc-only change) | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | N/A |
| 3 | Run validation sequence (`check_needs_confirmation_inventory.py`, `check_docs_quality.py`, `check_docs_structure.py`) | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | check_needs_confirmation_inventory.py: 1 ERROR on NC-020 (pre-existing); check_docs_quality.py: ✓ No issues; check_docs_structure.py: All checks passed |
| 4 | N/A: no `docs/00_index.md` task-scope mapping row further requires updating beyond this file itself | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | N/A |

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
- **Requirement ID**: REQ-001 (remove stale `NC-019` entry and correct item-count sentence)
- **Source issue**: `issues/20260902-094746_h01_git_mcp_write_protection_status_contradiction.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260902-095910_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-183225
- **Related target files**: `docs/00_governance_03_issue-and-uncertainty-management.md`
