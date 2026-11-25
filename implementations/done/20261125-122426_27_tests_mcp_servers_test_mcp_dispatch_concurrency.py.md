## Goal

Move the concurrency and lease pins to the context-based dispatcher signature (REQ-002, REQ-010).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The file has six call sites (`idempotency_key=` and `dispatch_tool(`); behavior pinned (one execution under 100 callers, lease heartbeat) is unchanged.

## Design decisions

- Reuse the same `ExecutionContext` construction as the dispatch test, defined locally to keep the files independent.

## Alternatives considered

N/A: mechanical signature change.

## Implementation
### Target file
`tests/mcp_servers/test_mcp_dispatch_concurrency.py`

### Procedure
Replace the keyword with a locally built `ExecutionContext`.

### Method
- Add a local `_ctx` (new) helper returning an applied `ExecutionContext` for a key.
- Replace each `idempotency_key=X` with `context=_ctx(X)`.

### Details
- `_wire_store` and the lease fixtures stay unchanged.

## Compatibility considerations

Test-only.

## Security considerations

N/A: test code.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/test_mcp_dispatch_concurrency.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- The concurrency pins pass unchanged in meaning.

## Out of Scope

- Any new behavior tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the test file described in Implementation > Procedure/Method/Details | Completed | 20261125-175307 | 20261125-175307 | changed; local _ctx helper, 3 call sites converted; fixtures untouched; stale check clean |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-180342 | 20261125-180342 | — plan batch: end-of-batch full-suite run pending; targeted run 3 passed, ruff clean. Pre-existing mypy findings remain in this file (5: fixture generator return types and dict[str, Any] arithmetic) and are out of this procedure scope per Details. This procedure has 2 rows (test-only), so the validation row is Step 2, not Step 3 end-of-batch full-suite run: 14369 passed, 4 skipped; diff-cover 92% (>=90) on changed lines; run_validation_gates.py passes |

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
- **Requirement ID**: REQ-002, REQ-010
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `tests/mcp_servers/test_mcp_dispatch_concurrency.py`