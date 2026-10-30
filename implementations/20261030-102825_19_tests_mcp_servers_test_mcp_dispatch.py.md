# Implementation Procedure: tests/mcp_servers/test_mcp_dispatch.py

## Goal

Replace the in-process `_duplicate_cache` fixture assumptions with durable-store
integration cases: completed-hit after simulated reopen, replay refuse/allow per
retry_class and snapshot equality, while keeping the existing duplicate-path
assertions as characterization locks (REQ-003, REQ-005), test-first for row 04.

## Scope

**In scope:**
- `tests/mcp_servers/test_mcp_dispatch.py`: adapt fixtures + add durable-dedup
  integration cases.

**Out of scope:**
- Store unit semantics (row 17); transport key determinism (row 15).

## Assumptions

- Verified HEAD anchors: `from mcp_servers.dispatch import ... _duplicate_cache` at
  `:14`; autouse fixture that clears the cache at `:101-108`; duplicate-path
  assertions at `:136`, `:155`, `:254`, `:273`. Plan row 19's `:125-128` region note
  and the `file/write_server.py:209` server call-site note are the plan's evidence
  for the shared-entry architecture.
- The fixture at `:101-108` must gain a second duty: point the store at a tmp
  `mcp_dedup.sqlite` per test (via the row 02 store's injectable path / row 10
  config override). Existing cache-clearing behavior stays (the overlay still exists
  per row 04).
- Red state: new durable cases fail until rows 02/04 land; adapted existing tests
  must stay green throughout (behavior of the same-process duplicate path is
  preserved per the plan's Risks section: `dispatch.py:190-201` path preserved).

## Design decisions

- Simulated reopen = close store + reopen same tmp file between two `dispatch_tool`
  calls in one test (no subprocess): completed row found via store, not overlay;
  assert handler executed exactly once across the pair and the second response is
  the stored result.
- Replay refuse: `retry_class` (new) = non_retryable + pending-interrupted → error
  surfaced, handler not executed; replay allow: retry_class = retryable → re-execution
  allowed with audit-visible state (REQ-005 table semantics exercised at
  integration level).
- Snapshot equality axis: same completed call, perturbed config fixture → replay
  still returns stored result (mismatch only changes the lifecycle choice for
  pending rows; per plan Risks, "mismatch only changes replay choice, never blocks
  execution") — pin both directions.
- Keep every pre-existing assertion byte-identical (characterization): only the
  fixture body and new classes change.

## Alternatives considered

- Subprocess reopen test — rejected: row 17 already proves cross-process store
  sharing at the store layer; dispatch tests stay fast TestClient-style.
- Deleting the overlay fixture (`:101-108`) — rejected: row 04 keeps a bounded
  overlay; its clearing behavior is still part of the contract.

## Implementation
### Target file
`tests/mcp_servers/test_mcp_dispatch.py`

### Procedure
1. Extend the autouse fixture (`:101-108`): tmp store wiring per test, teardown
  closes the store.
2. New class `TestDurableDedup` (new): reopen hit, refuse/allow matrix over retry_class ×
  snapshot-equality, store-error fail-closed for non_retryable tools (plan Risks
  mitigation: `dedup_store_error` (new) audited marker for retryable read tools).
3. Leave `:136/:155/:254/:273` assertion bodies untouched.

### Method
Test-first for the new class; characterization for the rest.

### Details
- Tests import `shared.mcp_dedup` for store construction — server-side tests may
  import shared layer (import contract allows servers → shared).

## Compatibility considerations

- Existing duplicate-detection tests encode current replay shape; if row 04's stored
  result differs in any field (e.g. audit region annotations at `dispatch.py:227-240`
  region), the fixture adjusts, not the assertions.

## Security considerations

- Synthetic tool names/payloads only; `retry_class` (new) unknown-tool default
  (`non_retryable` (new)) asserted in the refuse matrix.

## Rollback considerations

- Fixture change is additive; revert commit restores old fixture + no new class.

## Validation plan

- `uv run pytest tests/mcp_servers/test_mcp_dispatch.py` (new class red before
  rows 02/04, green after; old classes green throughout);
  `uv run mypy --no-namespace-packages tests/mcp_servers`; `uv run lint-imports`.

## Completion criteria

- Completed-hit-after-reopen, refuse/allow matrix, and fail-closed store-error
  behavior proven; all pre-existing assertions unmodified and green.

## Out of Scope

- Agent-side audit fields (rows 05/14); turn-entry pending detection (rows 07-08,
  tested in row 20).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend autouse fixture with tmp store wiring | Pending | — | — | Existing assertions untouched |
| 2 | Add TestDurableDedup (reopen, refuse/allow, store-error) | Pending | — | — | Red until rows 02/04 land |
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
- **Requirement ID**: `REQ-003` (durable dedup at dispatcher), `REQ-005` (replay
  policy)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: tests/mcp_servers/test_mcp_dispatch.py
