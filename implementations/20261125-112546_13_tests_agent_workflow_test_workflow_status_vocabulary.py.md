## Goal
Update the two recorded-call call sites for the new `args_hash` argument.

## Scope
**Release unit**: persisted directive store

## Assumptions
- The file's `KNOWN_WRITER_STATUSES` comment describes the recorder write path; the vocabulary itself does not
  change.

## Design decisions
N/A: call-site update only.

## Alternatives considered
N/A: test-only change.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_status_vocabulary.py`

### Procedure
Add the hash argument to the two `store.record_tool_call` calls (line 136 and the second in the same test group).

### Method
Pass a fixed canonical hash so the recorded row is complete under the `NOT NULL` column.

### Details
- No new assertion: this file pins the state vocabulary, which is unchanged.

## Compatibility considerations
Depends on the DDL column from sibling procedure seq 01.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_status_vocabulary.py` (REQ-007).

## Completion criteria
The vocabulary tests still pass with the new column populated.

## Out of Scope
No change to the vocabulary mapping itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the two call sites | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (persisted hash), `REQ-007` (call-site update)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `tests/agent/workflow/test_workflow_status_vocabulary.py`
