## Goal
Pass the canonical argument hash to the tool-call state recorder so the persisted row can be matched by a
replay directive.

## Scope
**Release unit**: persisted directive store

## Assumptions
- The hash is already computed at preparation and carried on `ToolExecutionContext.args_hash`; this module
  does not recompute it (Plan Step 3a correction: `tool_runner` does not import `_canonical_args_hash`).

## Design decisions
- Read the hash from the prepared call's execution context instead of adding an import, so the recording
  path uses the same value the preparation phase produced.

## Alternatives considered
- Recomputing the hash in the recorder call site — rejected: two computations of the same value can diverge
  if the arguments are normalized differently, and the context field is already the canonical value.

## Implementation
### Target file
`scripts/agent/tool_runner.py`

### Procedure
Add the hash argument to the `recorder.record_tool_call` call.

### Method
Pass `pc.context.args_hash` as the new argument, after `retry_class`, matching the Protocol order.

### Details
- The call site already guards a missing execution context for side-effecting calls
  (`IntentRecordUnavailableError`); the hash is only readable when the context exists, so the existing guard
  covers it and no new branch is needed.
- `_logical_call_id` is unchanged: a replayed call's context already carries the original id attached during
  preparation, so the recorded key is the original id (AC-001) with no change in this module.

## Compatibility considerations
Recorder fakes in tests must accept the new argument (`tests/agent/test_tool_runner.py`,
`tests/agent/test_mcp_call_recovery.py`).

## Security considerations
N/A: no new trust boundary; the value is an existing hash.

## Rollback considerations
N/A: revert the commit as part of release unit A.

## Validation plan
- `uv run pytest tests/agent/test_tool_runner.py` — a replayed call records the original id and the hash
  (AC-001).
- Full sequence per `rules/toolchain.md`.

## Completion criteria
The state row written for a recorded call carries the same hash the preparation phase computed, and the key
is the call's logical call id.

## Out of Scope
No change to `_logical_call_id`, the DAG ordering, or the audit path.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Pass `args_hash` at the recorder call site | Completed | — | 20261125-124514 | args_hash passed at the recorder call site from pc.context; changed: scripts/agent/tool_runner.py |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-124514 | 2026-11-25 | ruff/mypy/bandit pass; module-size gate resolved by procedure 22 (Path C split, approved 20261125): tool_runner 23736 B; tests/agent/test_tool_runner.py 111 passed; recorder fake still lacks args_hash -> red state resolved by procedure 10 end-of-batch run: full suite 14240 passed, diff-cover 100% on changed lines, pre-commit all hooks pass, cited ADR tests 75 passed |

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
- **Requirement ID**: `REQ-006` (the write path populates the persisted hash)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `scripts/agent/tool_runner.py`