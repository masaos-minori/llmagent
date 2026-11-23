## Goal

- Update `tests/mcp_servers/test_mcp_dispatch.py` so the durable path is asserted through the store acquisition instead of the in-process overlay, and add the `interrupted`-vs-`failed` policy matrix, the expiry-boundary pairs, and the no-re-execution cases (REQ-001 single decision point, REQ-004 recovery gating, REQ-005 refusal state tags, REQ-006 caller-supplied id, REQ-007 degraded path preserved; AC-1, AC-3, AC-5, AC-6).

## Scope
**Release unit**: dispatcher-decision-change

- Modify `tests/mcp_servers/test_mcp_dispatch.py` only (Plan Phase 7): replace the durable-path overlay assertions and add the T-4 through T-7 cases; the degraded-mode cache class stays as the REQ-007 guard.

## Assumptions

- This cycle's re-read confirmed the Plan's claims: `_duplicate_cache` is imported by this file, 7 `len(_duplicate_cache)` assertions exist (5 of them in `TestDispatchIdempotencyCache`, one in `test_overlay_fast_path_still_hits`, one in `test_dry_run_clears_pending_row`), `test_interrupted_non_retryable_refused` seeds an expired `pending` row (its name notwithstanding), and `test_finalize_lease_conflict_surfaces_without_redispatch` already pins the `lease_conflict` finalization shape.
- The `durable` fixtures (class-local in `TestDurableDedup` and `TestDurableDedupDryRunClear`), `TOOL = "write_file"`, and the `dispatch._tool_retry_policies` injection pattern continue to be the test harness; the mcpdl004 two-column fixture fix already landed in this file.
- The refusal tags the assertions pin are the dispatcher's existing strings plus the new `interrupted` tag wired by sibling `20261123-205822_02`; the `interrupted`-vs-expired-`pending` distinction the new tests rely on is the store's own signal recorded in sibling `20261123-205822_03` (`interrupted` rows carry `lease_expires_epoch=NULL`).
- These assertions fail against the pre-change dispatcher and are updated in Plan Phase 7, after the source phases land (release-unit note). Verified this cycle against `git checkout HEAD -- scripts/mcp_servers/dispatch.py scripts/shared/mcp_dedup_ledger.py` with the gate module removed: the three red cases are `test_completed_replay_served_from_store_without_overlay` (pre-change the overlay served the second call), `test_interrupted_row_non_retryable_refused` (pre-change the ledger reopened the interrupted row and the handler ran), and `test_truncated_completed_result_refuses_replay` (pre-change the truncated payload was replayed). The other new cases — `test_interrupted_row_retryable_recovers_once`, `test_failed_row_never_reattempted`, `test_lease_expiry_boundary_pair` — pass pre-change as well: they pin preserved behavior, not the new branch.

## Design decisions

- `TestDispatchIdempotencyCache` (degraded mode, no `durable` fixture) stays byte-identical: it is the REQ-007 pin that the degraded overlay path survives (T-6 second half, T-7).
- A genuinely `interrupted` row is seeded through the public store API (`try_acquire_execution` then `mark_interrupted`), not by hand-written SQL — the same API the dispatcher's cancel path uses, so the matrix tests the real state.
- `test_interrupted_non_retryable_refused` keeps its assertions (expired `pending` refusal, `dedup_state="reconciliation_required"`) and is renamed to `test_expired_pending_non_retryable_refused` (new) so the name matches the seeded state; the real `interrupted` refusal gets its own new cases (T-4).

## Alternatives considered

- Deleting the overlay fast-path test instead of re-pointing it: rejected — T-6 requires proving the durable replay still serves the second call (via `replay_completed` / `duplicate_hit`) while the overlay stays untouched, which a deletion would not pin.

## Implementation
### Target file
`tests/mcp_servers/test_mcp_dispatch.py`

### Procedure
1. T-6: rewrite `test_overlay_fast_path_still_hits` as the durable-replay case (rename to `test_completed_replay_served_from_store_without_overlay` (new)): the second call is served with `dedup_state == "duplicate_hit"`, the handler ran once, and `len(_duplicate_cache) == 0`; extend `test_first_ever_key_executes_once_on_fresh_store` and `test_dry_run_clears_pending_row` with `len(_duplicate_cache) == 0` after a full acquire/complete cycle so durable calls never populate the cache; the reused-key-with-different-content rejection is asserted through the acquisition's `contract_mismatch` (`test_durable_args_hash_mismatch_rejected` already pins it — extend it to also assert the overlay stayed empty).
2. T-4: in `TestDurableDedup`, add the policy matrix: seed `interrupted` via `try_acquire_execution(..., now_epoch=time.time() - 3600)` + `mark_interrupted()`, then (a) non-retryable tool (`dispatch._tool_retry_policies = {}`): refusal with `error_type == "dedup_unreplayable"`, `dedup_state == "interrupted"`, `len(calls) == 0`, and the row still `interrupted` with unchanged `attempt_number` via `get_execution()`; (b) retryable tool (declared policy injected): the call reacquires once — handler runs exactly once and the row ends `completed`; (c) `failed` row: refusal `dedup_state == "replay_unavailable"`, never re-attempted (matrix completeness, pairing with the existing attempt-cap cases). Rename `test_interrupted_non_retryable_refused` to `test_expired_pending_non_retryable_refused` (new) keeping its body.
3. T-5: add the truncated-result case (seed a `completed` row whose stored result carries the truncation marker; assert refusal `dedup_unreplayable` / `replay_unavailable`, handler not executed, terminal row preserved) beside the existing `test_completed_snapshot_mismatch_refused_replay`, and the expiry-boundary pair: with a short-lease fixture, a call immediately before `lease_expires_epoch` refuses `in_progress`, a call immediately after refuses `reconciliation_required` (non-retryable) — seed with `now_epoch` and shift the store clock through the fixture, asserting both tags.
4. T-7: keep `test_store_error_retryable_proceeds_non_retryable_fails_closed`, `test_not_configured_fails_closed_and_degrades`, and the bootstrap-open refusal tests unchanged; they pin the degraded outcomes under REQ-007.

### Method
- Every new case exercises only `dispatch_tool` and public store methods (`get_execution`, `mark_interrupted`, `reconcile_execution`); no imports from the gate module — the gate is tested through the dispatcher seam (sibling `20261123-205822_02`).
- Anchor list (re-read before editing): `test_overlay_fast_path_still_hits` (L414), `test_interrupted_non_retryable_refused` (L541), `test_attempt_cap_outcome_unknown_matrix` (L575), `test_durable_args_hash_mismatch_rejected` (L640), `test_completed_snapshot_mismatch_refused_replay` (L430), `TestDispatchIdempotencyCache` (L103, untouched).

### Details
- The matrix's row-unchanged assertion reads `row.status == "interrupted"`, `row.attempt_number` equal to the seeded value, and no `post-recovery` history entry — the AC-3 evidence-preservation half.
- `test_dry_run_result_not_cached` and the dry-run clear tests keep their `len(_duplicate_cache) == 0` assertions; on the durable path that value is now guaranteed structurally rather than incidentally (T-6).

## Compatibility considerations

- The `_duplicate_cache` import keeps working through the dispatcher's re-export (sibling `20261123-205822_01`); fixtures that `.clear()` it continue to reach the gate's cache object.
- Renaming `test_interrupted_non_retryable_refused` changes only the test id; its assertion content is preserved, and no other file references the name (verified by grep this cycle).

## Security considerations

- N/A: test-module change only; stores stay under `tmp_path`.

## Rollback considerations

- The assertion updates land as one Phase 7 commit; reverting restores the pre-change assertions (they pass against the pre-change dispatcher).

## Validation plan

- `uv run pytest tests/mcp_servers/ tests/integration/test_production_security_regression.py -m "not production_paths_allowed" -q` (delete `.testmondata` first), green with the matrix, boundary pairs, and no-re-execution cases added (Plan validation table).
- Run only after Plan Phases 1-6 have landed (release-unit constraint).

## Completion criteria

- No durable-path test depends on the overlay: durable replays are pinned through `duplicate_hit` from the store with an empty cache; the policy matrix, boundary pairs, truncation case, and refusal tags are green; the degraded-mode class and store-error cases are unchanged.

## Out of Scope

- `tests/mcp_servers/test_mcp_dispatch_concurrency.py` (sibling `20261123-205822_04`), `tests/shared/test_mcp_dedup.py` (companion of sibling `20261123-205822_03`), and all source-file changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | T-6: re-point the durable fast-path and cache-length assertions to the store acquisition | Completed | — | 20261123-232053 | Plan Phase 7 test_completed_replay_served_from_store_without_overlay replaces the overlay fast-path test; cache-length assertions added to test_first_ever_key_executes_once_on_fresh_store and test_durable_args_hash_mismatch_rejected |
| 2 | T-4: add the `interrupted`-vs-`failed` policy matrix; rename the expired-pending case | Completed | — | 20261123-232053 | T-4 matrix (interrupted refused / interrupted retryable reopens once / failed never re-attempted); test_expired_pending_non_retryable_refused rename |
| 3 | T-5: truncated-result case and lease-expiry boundary pairs | Completed | — | 20261123-232053 | T-5 truncated-completed refusal + test_lease_expiry_boundary_pair with the 1 s short_lease fixture |
| 4 | Run the validation sequence (`rules/toolchain.md` + this document's Validation plan) | Completed | 20261123-232053 | 20261123-233501 | release-unit validation sequence pytest tests/mcp_servers/ tests/integration/test_production_security_regression.py -m 'not production_paths_allowed' -> 2742 passed 4 skipped; TestDispatchIdempotencyCache untouched; diff-cover 100% on dispatch.py |

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
- **Requirement ID**: REQ-001 (single durable decision point), REQ-004 (recovery gating), REQ-005 (refusal state tags), REQ-006 (caller-supplied id contract), REQ-007 (degraded path preserved)
- **Source issue**: issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-130937_mcpai001_atomic-dedup-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-205822
- **Related target files**: `tests/mcp_servers/test_mcp_dispatch.py`