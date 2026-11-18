## Goal

Rewrite the docstring of `pending_tool_calls` (`scripts/agent/workflow/tool_call_state_ops.py`, L91-94) so it stops asserting that the turn-entry detection path (or the engine) calls it, and instead describes the function's actual behavior (returns the task's pending tool-call rows oldest-first) and its test-only usage (`REQ-001`).

## Scope
**Release unit**: N/A: not part of a release unit.

## Assumptions

- The edit is confined to the triple-quoted docstring at L91-94; no code body, import, signature, or return-contract line changes.
- The `idx_tool_call_state_task_state` index reference is accurate (`schema_sql.py:225`) and is preserved.
- `pending_tool_calls` remains test-only; the real turn-entry stale-detection entry point is `classify_stale_pending` (`workflow_engine.py:180`).

## Design decisions

- Replace the false second paragraph ("The only method the turn-entry detection path (workflow_engine) calls...") with an accurate description: the function returns the task's pending tool-call rows oldest-first and is exercised by tests; the turn-entry stale-detection entry point is `classify_stale_pending`. Reference `classify_stale_pending` only to correct the record, not to imply `pending_tool_calls` is production-used.
- Keep the `idx_tool_call_state_task_state` index reference unchanged (verified accurate).

## Alternatives considered

- Removing the index reference entirely: rejected — it is accurate and the plan preserves it.
- Wiring `pending_tool_calls` into production: out of scope (a separate test-only-helper cleanup).

## Implementation
### Target file
`scripts/agent/workflow/tool_call_state_ops.py`
### Procedure
Replace only the L91-94 docstring of `pending_tool_calls`; leave the function body, signature, and the index reference untouched.
### Method
1. Edit the docstring triple-quoted string at L91-94. Remove the sentence claiming the turn-entry detection path (or the engine) calls `pending_tool_calls`.
2. Rewrite it to state: the function returns the task's pending tool-call rows oldest-first (already true), and that it is exercised by tests; note that the turn-entry stale-detection entry point is `classify_stale_pending` (`workflow_engine.py:180`).
3. Preserve the `` `idx_tool_call_state_task_state` `` index reference verbatim. Do not rename the function, change its signature, or touch imports.
### Details

- The current docstring text being replaced is exactly:
  ```
  """Return the task's pending tool-call rows, oldest first.

  The only method the turn-entry detection path (workflow_engine) calls; kept cheap
  via the ``idx_tool_call_state_task_state`` index.
  """
  ```
- Verify zero production callers remain after the edit (`rg pending_tool_calls scripts/` shows only the definition), confirming AC-1.

## Compatibility considerations

N/A: a docstring change has no runtime, caller, or API-surface impact.

## Security considerations

N/A: no change to guards, `allowed_tools`, or side-effect semantics.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/workflow/tool_call_state_ops.py` | Static: format, lint, types | `uv run ruff format --check scripts/agent/workflow/tool_call_state_ops.py`; `uv run ruff check scripts/agent/workflow/tool_call_state_ops.py`; `uv run mypy --no-namespace-packages scripts/` | ruff/mypy clean |
| `tests/agent/workflow/test_workflow_state_store.py` | Unit: function still importable and tested after the edit | `uv run pytest tests/agent/workflow/test_workflow_state_store.py -v` | Passes; `pending_tool_calls` still callable |

## Completion criteria

- The docstring no longer states that the turn-entry detection path (or the engine) calls `pending_tool_calls` (AC-2).
- A grep for `pending_tool_calls` in `scripts/` still shows zero production callers (AC-1).
- Existing tests pass; the function remains importable and tested; the `idx_tool_call_state_task_state` reference stays accurate (AC-3).
- ruff format/check and mypy are clean on the touched file.

## Out of Scope

- Removing or wiring `pending_tool_calls` into production.
- Changing the function body, signature, return contract, or imports.
- Touching `classify_stale_pending`, `workflow_engine.py`, or any other function.
- Any test change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the `pending_tool_calls` docstring (`scripts/agent/workflow/tool_call_state_ops.py`, REQ-001) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261118-221536_wfrev002_stale-call-site-docstring.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-233245_wfrev002_stale-call-site-docstring.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-071535
- **Related target files**: `scripts/agent/workflow/tool_call_state_ops.py`
