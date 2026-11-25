## Goal

Make the dispatcher take an `ExecutionContext`, bypass dedup for a preview, require a key for every side-effecting call, report structured metadata, and delete the output-marker dry-run parsing (REQ-003 to REQ-006).

## Scope
**Release unit**: R1-mode-contract

## Assumptions

- `ExecutionContext` and its builders exist from the `execution_context.py` procedure (earlier `seq`), and `DispatchResult` carries the new fields from the `dedup_gate.py` procedure; this document runs after both within the release unit.
- Verified: `_is_dry_run_output` misses the Git `[DRY RUN]` and file `Dry-run:` formatter outputs, so those previews are currently finalized with `record_completed`; the marker path is deleted, not extended.
- No in-tree production caller of the programmatic `dispatch` exists, so the key rule changes behavior only for tests and out-of-tree callers (Plan Assumptions).
- Code docstrings and comments must not carry REQ markers (the repository checks that); cite behavior, not Plan ids.

## Design decisions

- A preview returns straight after the handler: no `_acquire_dedup`, no heartbeat, no `_finalize_dedup`, no overlay write. This is what makes a later real execution with the same key unblocked.
- no_op marks every outcome where the handler did not run (replay, dedup refusal, key rejection, unknown tool), so an error result never claims `applied`.

## Alternatives considered

Keeping `idempotency_key` as a second keyword next to `context` was rejected: two ways to supply the key would let a caller disagree with itself.

## Implementation
### Target file
`scripts/mcp_servers/dispatch.py`

### Procedure
Rewrite the `dispatch_tool` signature and flow around the context, then remove the marker code and the post-handler dry-run branch.

### Method
- Delete `_IDEMPOTENCY_DRY_RUN_MARKERS`, `_is_dry_run_output`, and the comment block that introduces them; import `ExecutionContext` from `mcp_servers.execution_context`.
- Change `dispatch_tool(table, name, args, idempotency_key=None)` to `dispatch_tool(table, name, args, context=None)`; when `context` is `None` use `ExecutionContext.for_programmatic_call(name, args)`.
- After the unknown-tool check, if the tool is side-effecting and the context key is blank, return an error `DispatchResult` with `error_type="idempotency_key_required"` and `execution_mode="no_op"`; read-only tools skip this check.
- If the context mode is `preview`, run `handler(args)` and return `DispatchResult(output, False, execution_mode="preview", side_effect_applied=False)`; a `ValueError` still becomes the existing validation-error result (mode `preview`); other exceptions propagate unchanged.
- On the applied path keep `_acquire_dedup`, the heartbeat, and the exception handling, taking the key from the context; an `early` result is returned through `dataclasses.replace(..., execution_mode="no_op", side_effect_applied=False)`.
- Remove the `dry_run` parameter and the `store.clear` branch from `_finalize_dedup`; drop `not dry_run` from the overlay-cache condition.
- Set `execution_mode="applied"` and `side_effect_applied` to the side-effecting flag on the success result; map the two new fields in `_to_call_tool_response`.
- Rewrite the `dispatch_tool` docstring: the key requirement, the modes, and that previews are neither cached nor recorded.

### Details
- `configure_dedup`, `configure_tool_retry_policies`, `_store_op`, `_overlay_lookup`, and `_degraded_decision` keep their behavior.
- Keep the module re-exports from `mcp_servers.dedup_gate` intact so existing importers do not change.

## Compatibility considerations

Breaking for any caller passing `idempotency_key=`; every in-tree caller is updated by the server procedures of the same release unit, and tests by the dispatch test document.

## Security considerations

A keyless side-effecting call is now rejected before the handler runs, closing the programmatic bypass of the key contract; error text names the tool only.

## Rollback considerations

Revert the release unit together; the dispatcher alone cannot be reverted while servers pass a context.

## Validation plan

- `uv run pytest tests/mcp_servers/test_mcp_dispatch.py tests/mcp_servers/test_mcp_dispatch_concurrency.py tests/mcp_servers/test_dry_run_contract.py`
- `uv run mypy scripts/mcp_servers/dispatch.py`
- `uv run ruff check`, `uv run ruff format`, `uv run bandit scripts/mcp_servers/dispatch.py -c pyproject.toml`

## Completion criteria

- No output-marker dry-run code remains (`rg _is_dry_run_output scripts` is empty).
- A preview with a durable store leaves the ledger and the overlay empty.
- A keyless side-effecting call returns idempotency_key_required; a read-only keyless call executes.

## Out of Scope

- Dedup storage state machine and key generation.
- Server entry points and tests (separate documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Add or update tests per Validation plan | Pending | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: REQ-003, REQ-004, REQ-005, REQ-006
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `scripts/mcp_servers/dispatch.py`
