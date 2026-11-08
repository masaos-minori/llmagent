# Implementation procedure: `scripts/agent/context.py` — drop `snapshot_id` from the `ToolCallRecorder` protocol seam

## Goal
Remove the dead `snapshot_id` parameter from the `ToolCallRecorder` protocol's `record_tool_call` signature so the structural seam matches the retired API (`REQ-002`).

## Scope
**Release unit**: wfaudit010-full

- One signature line deletion in `context.py` (L297).

## Assumptions
- `ToolCallRecorder` is a `typing.Protocol` structural seam (verified at HEAD `367e583d2`, class at L284): it is deliberately not imported by `state_store.py` (import-cycle rule), so mypy structural compatibility is what keeps `StateStore` conformant — the sibling facade change (seq 03) must land in the same batch or mypy flags `StateStore` as over-specific, which is harmless, and any caller supplying `snapshot_id=` would be flagged, which is the desired error.

## Design decisions
- Delete the parameter rather than mark the protocol deprecated: the seam mirrors the only implementation (`StateStore.record_tool_call`), and no caller ever supplied the argument.

## Alternatives considered
- N/A: single-line protocol deletion.

## Implementation
### Target file
`scripts/agent/context.py`

### Procedure
1. Delete `snapshot_id: str | None = None,` from `ToolCallRecorder.record_tool_call` (L297); the surviving parameters (`task_id`, `idempotency_key`, `tool`, `retry_class`) and the rest of the protocol stay unchanged.

### Method
- Deletion only; the protocol docstring and `finalize_tool_call` are untouched.

### Details
- Current state (verified at HEAD `367e583d2`): the parameter is the protocol's fifth, defaulted, and never passed by the sole consumer path (`scripts/agent/tool_runner.py` calls with four positional arguments).

## Compatibility considerations
- Runtime effect: none (Protocol methods are declarations; `...` body). Static effect: mypy enforces conformance once the facade is updated in the same batch.
- No companion test file: no test constructs a `ToolCallRecorder` implementation today (`grep` across `tests/agent/` found no `snapshot_id` references outside `tests/agent/workflow/`, which the sibling seq 02 companion covers).

## Security considerations
- N/A: type-level seam edit.

## Rollback considerations
- Revert the commit restores the declaration; no runtime impact either way.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/context.py` | static | mypy in the `rules/toolchain.md` sequence | no protocol-conformance errors after the batch |
| grep contract | static | `grep -rn "snapshot_id" scripts/agent/` after batch | empty (Acceptance Criteria REQ-002) |

## Completion criteria
- `ToolCallRecorder.record_tool_call` carries four parameters, none named `snapshot_id` (`Acceptance Criteria REQ-002`).

## Out of Scope
- Everything else in `context.py` (session state, workflow state dataclasses).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocks wfaudit003 and wfaudit002: land this plan's batch first |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | No companion test file: validated by mypy + grep contract |

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
- **Requirement ID**: `REQ-002` (protocol-seam parameter removal)
- **Source issue**: `issues/20261107-203223_wfaudit010_snapshots-never-written.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: `plans/20261108-084001_wfaudit010_snapshots-never-written.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-092904
- **Related target files**: `scripts/agent/context.py`
