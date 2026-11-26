## Goal
- Update `tools/TOOL_DESCRIPTIONS.md` for the extended normalizer, the new finding, and the new shared module (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the rows of `backtick_plan_related_tests.py`, `check_workitem_structure.py` (Index and the detail table), and one new Index row for `_workitem_citation_check.py`. Out of scope: any other row.

## Assumptions
- Verified in Step 3a: the Index rows of `backtick_plan_related_tests.py` and `check_workitem_structure.py` are in the Work item category; the shared-base rows (`_workitem_length_check.py` and neighbors) are in the Index near the other `_workitem_*` modules; `tools/check_tool_descriptions_sync.py` requires every `tools/*.py` to be listed (procedure 01's module needs a row).
- Procedures 01, 03, and 05 run first, so the rows describe real behavior.

## Design decisions
- The normalizer row states: backticks the `File Path` cells, the `tests/...py` paths of `Related Tests`, and the target paths of `Implementation steps` of one Plan; changes no other text; idempotent; `--dry-run`; run in `issue-to-plan` Step 8a. The checker rows add the `plain-path-citation` finding (active Plans only, exit 1). The new Index row: `| `_workitem_citation_check.py` | Shared base | Plain path citation rule read by `check_workitem_structure.py` and `backtick_plan_related_tests.py` |` (real backticks).

## Alternatives considered
- N/A: documentation only.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Edit the Index row of `backtick_plan_related_tests.py` and the Index and detail rows of `check_workitem_structure.py` as described; keep each row on one line.
2. Insert the new Index row directly after the `_workitem_length_check.py` row.
3. Run the sync check.

### Method
- Rows only; no other line changes. The text is English.

### Details
- Do not claim a hook for the normalizer; the structure checker already runs as the `workitem-structure` hook.

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py`; the pre-commit hook "Check tools/TOOL_DESCRIPTIONS.md sync" on commit.

## Completion criteria
- The sync check passes and the three rows plus the new row describe the final behavior.

## Out of Scope
- The tool, template, and workflow changes (procedures 01 to 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` "When to run which tool" | Pending | — | — | |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/20261126-151438_wfeff003_plan-path-citations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-172913_wfeff003_plan-path-citations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-173805
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
