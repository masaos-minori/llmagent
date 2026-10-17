## Goal

Remove the MCP-006 entry from the Known Issue inventory in
`docs/00_governance/governance_03_issue-and-uncertainty-management.md` once every high-risk tool category
either implements or explicitly documents each layer of the Layered protection model (REQ-011, AC-011).

## Scope

- Delete the `#### MCP-006` entry and all of its fields.
- Confirm no other document under `docs/` cites MCP-006 before deleting the entry.
- Leave the ordering convention, Part 2, and every other entry unchanged.

## Assumptions

- This row runs last in the documentation phase, after Plan rows 12-18 have landed and after the
  completion criteria of rows 1-11 are met, because the entry exists only while the gap is open.
- MCP-006 is the only entry in the MCP group, so removing it leaves the group empty rather than creating
  an ordering gap.
- `docs/91_security/security_02_high-risk-tool-common-policy.md` is the only file outside this ledger that
  cites MCP-006, and Plan row 18 removes that citation.

## Design decisions

- Delete the entry rather than mark it resolved: the Current-Specification-Only Policy keeps no resolved
  items in active documents, and a lingering entry would keep asserting a gap that the tool documents now
  contradict.
- Verify the citation sweep with a search rather than with the memory of which files were edited, because
  `check_known_deviation_sync.py` reports a citation to a removed ID as an error in any document under
  `docs/`.

## Alternatives considered

- Move the entry to a resolved section: rejected — the canonical document has no resolved section for
  Part 1 entries, and the checker treats a resolved bullet in an ADR as an error.
- Keep the entry until the next quarterly review: rejected — AC-011 requires the ledger to stop recording
  the gap in this Plan.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Search `docs/` for `MCP-006` and confirm the only remaining hits are this entry's own heading and ID
   field.
2. Delete the `#### MCP-006` heading and every field bullet through the end of its `Resolution Target`
   field.
3. Re-run the search and confirm zero hits.
4. Run the governance and docs checkers.

### Method

Delete the block; do not renumber or retitle any other entry, and do not reorder the remaining groups.

### Details

- The entry is `docs/00_governance/governance_03_issue-and-uncertainty-management.md:94-120`, from its
  heading through its `Resolution Target` field.
- The `### Active Items` heading and the ordering-convention paragraph above the entry stay unchanged.
- The Part 1 entry field set is unchanged for every remaining entry.

## Compatibility considerations

- Any ADR or document that cites MCP-006 must have had its citation removed by an earlier row; a remaining
  citation is a dangling reference and fails `check_known_deviation_sync.py`.
- The Plan and issue records keep their own MCP-006 references, which live outside `docs/` and are not
  scanned by that checker.

## Security considerations

N/A: documentation-only row; removing the entry does not remove any enforcement.

## Rollback considerations

N/A: revert the commit. If any implementation row is later reverted, this entry must be re-added, because
the ledger is the place that records an open coverage gap.

## Validation plan

- `uv run python tools/check_known_deviation_sync.py`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_workitem_traceability.py --active-only`
- `uv run python tools/check_workitem_structure.py --file implementations/20261017-162434_19_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md`

## Completion criteria

- The file contains no `MCP-006` heading or field, and no document under `docs/` cites MCP-006 (AC-011).
- `check_known_deviation_sync.py` reports no dangling-reference findings.
- AC-009 and AC-011 are satisfied by the preceding rows before this row is committed.

## Out of scope

- Editing any other Part 1 entry.
- Editing the Part 2 Needs Confirmation inventory.
- Archiving the Plan, which the workflow moves to `plans/done/` outside the target-file rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm no remaining MCP-006 citation outside the entry | Completed | — | 2026-10-17 | Gate for deletion |
| 2 | Delete the MCP-006 entry | Completed | — | 2026-10-17 | REQ-011 |
| 3 | Run the governance and docs checkers | Completed | — | 2026-10-17 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

## Work Items Created

- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-011
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-160222_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162434
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`