## Goal

- Create the durable-dedup gate module that owns the acquisition-result mapping, the refusal constructors, the degraded-mode overlay cache, the owner-nonce helper, the lease-renewal heartbeat, and the `DispatchResult`/`ToolArgs` result types, so `scripts/mcp_servers/dispatch.py` and this module both stay under the 24576 B size gate and `dispatch_tool()` drops out of its `E (37)` complexity grade (REQ-008, with the REQ-001/REQ-003/REQ-005 behavior it carries).

## Scope
**Release unit**: dispatcher-decision-change

- Create `scripts/mcp_servers/dedup_gate.py` with the moved logic plus the heartbeat; behavior stays identical through Phase 3 (pure move), then the Phase 5/6 changes land here (contract-mismatch-only reuse rejection wiring, the recovery-permission pass-through, and the `interrupted` refusal tag).

## Assumptions

- The module is created in Plan Phase 3 as a behavior-preserving move of code verified in this cycle's reads of `scripts/mcp_servers/dispatch.py` (`_dedup_decision()`'s branch mapping, the overlay cache helpers, `_new_owner_id()`, `_OWNED_STATES`).
- `allow_interrupted_recovery` (new) is created by the later-seq sibling `20261123-205822_03` (ledger Phase 2); the wiring in `_dedup_decision()` (Phase 6) lands after it, and the Plan's phase order (2 before 6) makes this safe. Stale detection was run with sibling order `any` for this cross-reference.
- Import-linter: this module lives in `scripts/mcp_servers/` and may import only `shared/` and its own definitions (Plan Path B analysis); it must not import `mcp_servers.dispatch` (cycle) and does not need `mcp_servers.models`.
- `DispatchResult` and `ToolArgs` definitions move here from `dispatch.py` (Plan D-1, corrected this cycle); `dispatch.py` re-exports them so consumers keep their import paths.

## Design decisions

- `DispatchResult` lives here so the refusal constructors can build it at runtime; `scripts/mcp_servers/dispatch.py` re-exports it, keeping all 20 importer paths valid (D-1 correction).
- `_dedup_decision()` receives the dispatcher's already-resolved permission as an explicit keyword argument `retryable` instead of importing the tool-policy map — the gate stays policy-agnostic like the store (D-4), and no import cycle exists.
- `_LeaseHeartbeat` (new): an asyncio task renewing every `store.lease_seconds / 2` while the handler runs; `DedupLeaseConflict` or a store error during renewal sets a `renewal_lost` flag (new attribute) read by the dispatcher at finalization (D-3). A `threading.Timer` was rejected by the Plan.
- Refusal constructors keep the exact current payloads: `error_type` strings (`idempotency_key_reused`, `dedup_in_progress`, `dedup_unreplayable`) and `dedup_state` tags stay byte-identical so Phase 3 is verifiably behavior-preserving (REQ-005).

## Alternatives considered

- Gate in `scripts/shared/`: rejected by the Plan — it needs the dispatcher-owned result types, and the `shared-is-leaf` contract forbids importing `mcp_servers` from `shared` (D-1).
- A new acquisition status such as recovery_not_permitted: rejected by the Plan — it extends the acquisition vocabulary the control-API contract must map; `reconciliation_required` already means "needs reconciliation, no owner granted" (D-4).

## Implementation
### Target file
`scripts/mcp_servers/dedup_gate.py` (new)

### Procedure
1. Create the module docstring (one paragraph: the durable-dedup gate extracted from `mcp_servers.dispatch` under plan `plans/20261123-130937_mcpai001_atomic-dedup-state-machine.md`; imports only `shared/` and stdlib; the dispatcher re-exports these names) and the imports: `asyncio`, `secrets`, `time`, `collections.OrderedDict`, `dataclasses`, `typing.Any`, `from shared.mcp_dedup import DedupLeaseConflict, DedupStore, DedupStoreConfig, DedupStoreError`.
2. Move verbatim from `scripts/mcp_servers/dispatch.py`: `ToolArgs`, `DispatchResult` (with its full taxonomy docstring), `_CacheEntry`, `_duplicate_cache`, `_idem_now()`, `_idem_evict()`, `_idem_store()`, `_IDEMPOTENCY_CACHE_TTL_SECONDS`, `_IDEMPOTENCY_CACHE_MAX_ENTRIES`, `_new_owner_id()`, `_dedup_decision()`, `_OWNED_STATES`.
3. Add `_LeaseHeartbeat` (new): `start()` schedules a renewal loop (`asyncio.create_task`) sleeping `store.lease_seconds / 2` between `store.renew_lease(key, owner_id)` calls; `stop()` cancels the task; `renewal_lost` becomes `True` on `DedupLeaseConflict` or `(sqlite3.Error, OSError)`, with the same warning logs the removed `_renew_lease_if_needed()` emitted.
4. Phase 6 wiring (after sibling seq 03 lands): `_dedup_decision(..., *, retryable: bool)` calls `store.try_acquire_execution(..., allow_interrupted_recovery=retryable)`; the refusal constructor for a recovery refused `interrupted` row (new `_refusal_interrupted()`) returns `error_type="dedup_unreplayable"` with `dedup_state="interrupted"` and leaves the row untouched — the store-side refusal is created by seq 03, so here it is only the status-to-result mapping. Expired `pending` keeps today's reconcile-then-reacquire (retryable) or `reconciliation_required` refusal (non-retryable).
5. Keep the `replay_completed` branch's overlay write (`_idem_store()`) only on the degraded path: with the dispatcher no longer calling it on the durable path (seq 01 Phase 5), the cache is fed solely by degraded dispatch (REQ-001).

### Method
- `_dedup_decision()` keeps its `(early_result, dedup_state)` return contract; the branch order and every message string stay as verified in this cycle's read: `acquired` → `(None, "")`, `contract_mismatch` → reuse rejection, `replay_completed` → `duplicate_hit`, `in_progress` → refusal, `reconciliation_required` → reconcile-reacquire (`replayed`) or refusal, `outcome_unknown` → degraded `store_error` (retryable) or refusal, `replay_unavailable` → refusal; append the `interrupted`-tag mapping in step 4.
- `_LeaseHeartbeat` holds `(store, key, owner_id)` and never runs store writes outside the event loop (D-3 mitigation).
- Line-count budget: the moved bodies plus `_LeaseHeartbeat` and the moved type definitions keep this module well under 24576 B; verify with `wc -c` at Phase 3 completion.

### Details
- `reconciliation_required` reconcile path: `store.reconcile_execution(key)` then one `try_acquire_execution()` — unchanged; the `interrupted` row that this path produces reopens only when `allow_interrupted_recovery` (new) is `True` (sibling seq 03), which for the retryable path it is; the non-retryable refusal path never reacquires.
- The heartbeat must not renew after the handler finished: `stop()` cancels the task and awaits its completion so no renewal races the `record_completed()` finalization.
- Module private names remain underscore-prefixed; `dispatch.py` imports them explicitly (no wildcard import).

## Compatibility considerations

- Consumer-visible change is zero: the only importer is `scripts/mcp_servers/dispatch.py`, which re-exports every name (Plan Impact: `dedup_state` has no consumers outside the dispatcher beyond `models.py`/`tool_audit.py`, both unconstrained).
- Existing test seams keep working because the re-exported `_duplicate_cache` is the same object; a test that *replaces* the binding on `dispatch.py` instead of calling `.clear()` would not reach the gate — no fixture does this today (verified: conftest uses `.clear()`, the git-compliance fixture patches `_is_side_effecting`).

## Security considerations

- The heartbeat renews only under the store's owner-conditional `renew_lease()` (zero-row updates raise `DedupLeaseConflict`); a lost lease is surfaced, never silently re-dispatched (REQ-003/AC-4).
- `secrets.token_hex(16)` for the owner nonce moves unchanged; bandit baseline (0 Medium/High) must stay clean.

## Rollback considerations

- Deleting this file and restoring `dispatch.py` from the pre-extraction commit is a complete revert (D-1 reversibility: high); no persisted state is involved.

## Validation plan

- `uv run lint-imports` (6 kept, 0 broken; the new module imports only `shared/` and stdlib).
- `uv run pytest tests/mcp_servers/ -q` green right after the Phase 3 move (the Plan's isolation check).
- `uv run python tools/check_module_size.py` — both `dispatch.py` and this file under the gate, no baseline entry needed.
- `uv run radon cc scripts/mcp_servers/dispatch.py -s` after extraction.

## Completion criteria

- The gate module exists with the listed contents; the dispatcher suite passes against it with no behavior change from Phase 3 alone; after Phase 6 the refused-`interrupted` case maps to `dedup_state="interrupted"` / `error_type="dedup_unreplayable"` with the row unmutated (AC-3).

## Out of Scope

- `scripts/mcp_servers/dispatch.py`'s own edits (sibling `20261123-205822_01`), the store-side `allow_interrupted_recovery` (new) implementation (sibling `20261123-205822_03`), test modules (siblings `20261123-205822_04` and `20261123-205822_05`), and any ADR/design-document change (mcpai012 sweep).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 3: create the module with the verbatim moved contents; size and import-linter checks clean | Pending | — | — | isolation check: dispatcher suite green |
| 2 | Add `_LeaseHeartbeat` (new) per Procedure step 3 | Pending | — | — | Phase 4 |
| 3 | Phase 6: `retryable` keyword and the `interrupted` refusal mapping after sibling seq 03 lands | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md` + this document's Validation plan) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (single durable decision point), REQ-003 (lease renewed during execution), REQ-005 (refusal state tags), REQ-008 (gate extraction under the size gate)
- **Source issue**: issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-130937_mcpai001_atomic-dedup-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-205822
- **Related target files**: `scripts/mcp_servers/dedup_gate.py`
