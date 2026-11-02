## Goal
- Register `tools/close_procedures_batch.py` in `tools/TOOL_DESCRIPTIONS.md` (`REQ-006`: the tool is registered; AC-6).

## Scope
- In scope: one new row in the Index table. Out of scope: other rows, the other tools' descriptions, and the Index module count.

## Assumptions
- Plan A7, A9 apply. Step 3a verified (2026-11-02): the Index table (`| File | Category | Purpose |`) lists work-item tools with Category `Work item` (for example `set_execution_status.py`, `close_wflease001_procedures.py`); `check_tool_descriptions_sync.py` cross-checks `tools/*.py` against backticked `*.py` names in the file and does not check the "Index (61 modules)" count, which is already stale (69 tool files exist), so it is left alone (AGENTS.md Global Rule 5).
- Overlap (Step 2, Plan A7 and A9): this file is also targeted by the Plans filed from flowimp010, flowimp011, and others; each adds its own row, so they are compatible and only adjacent-line rebases can occur.
- The tool file exists when this row executes (row 01 procedure).

## Design decisions
- Place the row after `set_execution_status.py` in the Index table, Category `Work item`, to keep the work-item tools together.
- The Purpose text states the options and the safety properties: verify before change, dry run, explicit `--complete-rows` with `--note`, staged-only renames, step marking only for named steps whose cited files are all archived.

## Alternatives considered
- N/A: one-row docs change.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
- Add one Index row for `close_procedures_batch.py` with the usage line `close_procedures_batch.py <procedure-doc>... [--plan P] [--plan-steps N,M] [--complete-rows --note T] [--dry-run]`.

### Method
- Match the neighboring rows' format (three cells, backticked file name, one-line Purpose).

### Details
- Mention that `close-batch`, `set_execution_status.py`, and `close_procedure.sh` are unchanged, so a reader picks the right tool.

## Compatibility considerations
- N/A: documentation row.

## Security considerations
- N/A: documentation row.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` passes with the tool file present and registered.

## Completion criteria
- `tools/TOOL_DESCRIPTIONS.md` has a row for `close_procedures_batch.py` and `check_tool_descriptions_sync.py` passes.

## Out of Scope
- Updating the Index module count or any other row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the Index row per Implementation > Procedure | Completed | 20261102-132658 | 20261102-132658 | Changed: tools/TOOL_DESCRIPTIONS.md (one Index row after set_execution_status.py, Category Work item, with usage line and note that close-batch, set_execution_status.py, close_procedure.sh are unchanged). The row was added earlier in this plan batch (during the procedure 01 cycle, so the tool was registered before its archive); verified present and unchanged here. Index module count left alone per procedure. |
| 2 | Run `check_tool_descriptions_sync.py` (`routing.md` Tools "When to run which tool") | Completed | 20261102-132658 | 20261102-132658 | check_tool_descriptions_sync.py: No issues found. No code change; docs: N/A. Full suite deferred to plan end. |

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
- **Requirement ID**: `REQ-006` (register the tool in `tools/TOOL_DESCRIPTIONS.md`)
- **Source issue**: issues/20261030-191530_flowimp008_workitem-bulk-close.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080631_flowimp008_workitem-bulk-close.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085613
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
