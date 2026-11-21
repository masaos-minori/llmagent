## Goal

Adopt the new acquisition API in `scripts/mcp_servers/dispatch.py`: remove the `lookup` + pending-write + `force` pattern, map the new start states onto the existing audited `store_error` taxonomy, and keep the overlay cache and per-key `args_hash` reuse rejection (REQ-001, REQ-002, REQ-006).

## Scope
**Release unit**: dedup-lease-identity-rollover

## Assumptions
- Row 01 (`scripts/shared/mcp_dedup.py`) lands in the same release unit and provides `try_acquire_execution` (new), the acquisition vocabulary (Plan D-5), and the typed identity/lease errors.
- ADR-004 MCP-001 (retryable overlay-only `store_error`) and MCP-002 (write-failure warning-only) governance is unchanged (Plan Design verification findings).
- The dedup decision is extracted into a module-level helper to keep `dispatch_tool` cyclomatic complexity from growing (Plan Risks; currently F(44)).

## Design decisions
- Start-state mapping (D-7): `lost` / `replaced` / `legacy_or_unverified` / `schema_mismatch` (new) refuse non-retryable tools with `dedup_store_error`; retryable tools degrade overlay-only with the audited `store_error` marker.
- `_dedup_context` catches the typed identity/shape errors explicitly so the current broad `except Exception` masking (shape mismatch collapsing into the generic disabled fallback) is replaced by typed handling.
- MCP-002 warning-only behavior switches from `RuntimeWarning` to structured `logger.warning`.
- Acquisition results map: `acquired` -> dispatch; `replay_completed` (new) -> cached replay; `in_progress` -> refusal as in progress; `reconciliation_required`/`outcome_unknown` -> non-retryable refusal, retryable degraded per classification; `contract_mismatch` (new) -> `idempotency_key_reused`-style rejection; `replay_unavailable` (new) -> refusal (Plan D-5 vocabulary).

## Alternatives considered
- Keeping `lookup` + `record_pending` as a compatibility shim inside the dispatcher: rejected — AC-6 forbids lookup-plus-record patterns in production callers, and the shim would preserve the force-reset evidence-loss path.

## Implementation
### Target file
`scripts/mcp_servers/dispatch.py`
### Procedure
Replace the durable-dedup block in `dispatch_tool` with a single acquisition call plus an owner-scoped finalization path, and route every store-open start state through the existing refusal/degradation taxonomy.
### Method
1. Replace the `lookup` -> `record_pending(force=...)` sequence (and the lost-store pre-check) with `store.try_acquire_execution(key, name, args_hash, snapshot_json, owner_id)`; generate a per-call `owner_id` nonce.
2. Dispatch only on `acquired`; wrap the handler call so finalization (`record_completed`/`record_failed`/`mark_interrupted`) is owner-conditional and a heartbeat (`renew_lease`) runs for long handlers; on `DedupLeaseConflict` log and surface the state without re-dispatching.
3. Extend `_dedup_context` (and the init-failure path) to classify typed store-open errors (identity/shape/lost/replaced/legacy) and set the degraded-vs-refused decision from the start state, keeping the existing retryable/non-retryable asymmetry.
4. Keep `_duplicate_cache`, the `args_hash` comparison, and the `idempotency_key_reused` rejection unchanged (overlay contract preserved).
5. Extract the dedup decision into a module-level helper (e.g. `_dedup_decision` (new)) so `dispatch_tool` F(44) does not grow.
### Details
- Current regions being replaced: the lost-store refusal block after `store, config = _dedup_context()`, the `lookup` failure fallback, and the init-failure `store_error` asymmetry; `_dedup_context`'s current `except Exception` fail-open remains the process-level fallback but must carry a typed reason into the decision helper.
- `error_type="dedup_store_error"` and `dedup_state="store_error"` payload names stay identical for downstream consumers (`tool_audit`).
- Structured warnings for lease conflicts / reconciliation states provide the observability hooks documented in row 23.

### Companion test files
- `tests/mcp_servers/test_mcp_dispatch.py`
  - Procedure: Adapt `test_store_error_retryable_proceeds_non_retryable_fails_closed` and `test_lost_store_non_retryable_refused_retryable_proceeds` to the acquisition API; add replaced-state and legacy-state refusal cases; assert no `lookup`/`force` pattern remains in fixtures.
  - Validation: `uv run pytest tests/mcp_servers/` passes with the new start-state matrix.
- `tests/mcp_servers/conftest.py`
  - Procedure: Build store fixtures through the new initialization path (identity row + marker via the store API) instead of raw table seeding.
  - Validation: the whole `tests/mcp_servers` suite passes with fixtures exercising first-initialization classification.

## Compatibility considerations
- The overlay-only behavior (no durable store) is unchanged, so non-dedup callers see no difference.
- `dedup_state`/`error_type` payload vocabulary stays stable; new states surface through existing fields plus new WARNING log lines (row 23 documents them).

## Security considerations
- Fail-closed for non-retryable tools in every unsafe start state (no tolerant start, Plan Constraints); the typed-error routing closes the masking gap where a drifted store silently degraded the whole process.

## Rollback considerations
- Revert the commit within the release unit; the file is self-contained and the old store API remains available until row 01's revert lands in the same unit.

## Validation plan
- `uv run pytest tests/mcp_servers/` passes (companion files).
- `rg -n "record_pending|force=True" scripts/mcp_servers/` returns nothing.
- radon: `dispatch_tool` complexity must not worsen (Plan Risks gate).
- Full static gate per `rules/toolchain.md`.

## Completion criteria
- AC-1/AC-5/AC-6 dispatcher-side guarantees: refusal/degradation matrix per start state passes; no lookup-plus-record call site remains; lease-conflict handling is observable.

## Out of Scope
- Store internals (row 01), fixture files outside `tests/mcp_servers/conftest.py`, observability docs (row 23).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261121-113427 | Co-lands with row 01 (release unit) Acquisition API landed: single try_acquire_execution + _dedup_decision helper (D-5 mapping: acquired/replay_completed/in_progress/reconciliation_required/outcome_unknown/contract_mismatch/replay_unavailable). Owner nonce per call; owner-conditional record_completed/record_failed/mark_interrupted (CancelledError path); heartbeat via _renew_lease_if_needed; DedupLeaseConflict logged, never re-dispatched (lease_conflict dedup_state). Lost/recreated pre-check and lookup/record_pending/force removed. Retryable expired-lease replay = reconcile_execution + reacquire (dedup_state=replayed); outcome_unknown retryable degrades audited store_error. Start-state refusals (lost/replaced/legacy_or_unverified/schema_mismatch) captured typed in _dedup_start_state via _dedup_context. |
| 2 | Update companion test files per Validation plan | Completed | — | 20261121-113427 | test_mcp_dispatch.py adapted: snapshot-mismatch test now asserts replay_unavailable refusal; interrupted tests seed via try_acquire_execution with expired now_epoch; new in_progress, outcome_unknown matrix, lease_conflict, replaced-state and legacy-state refusal tests; lookup->get_execution; retention seeds use acquisition+finalize. conftest.py: _dedup_start_state reset added; store fixtures already build through DedupStore init path (identity row + marker). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-113427 | radon F(44) baseline gate uv run pytest tests/mcp_servers/ 2662 passed 3 skipped. rg 'record_pending|force=True' scripts/mcp_servers/ empty. radon: dispatch_tool E(37) vs F(44) baseline (not worse); _dedup_decision B(10). ruff check/format+mypy green. |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-006
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-083728_mcpdl002_store-identity-continuity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-093956
- **Related target files**: `scripts/mcp_servers/dispatch.py`, `tests/mcp_servers/test_mcp_dispatch.py`, `tests/mcp_servers/conftest.py`