## Goal

Replace the `lookup` + `record_pending(force=True)` pattern in `scripts/shared/mcp_dedup.py` with a lease-based atomic acquisition API, immutable terminal rows with append-only attempt history, and store identity with start-state classification and operator resolution (REQ-001..REQ-007, REQ-010).

## Scope
**Release unit**: dedup-lease-identity-rollover

## Assumptions
- Plan Design D-1..D-4, D-5, D-6 govern this file; UNK-02 is resolved by D-3 (attempt history lives in the same disposable store).
- Production currently has no dedup store file (Plan Rollout note, confirmed 2026-11-21), so rollout is a clean first initialization; no live database must survive this change.
- Phase 1 test documents (`20261121-093956_10_...`, `20261121-093956_11_...`) land before this document's code (Plan Phase 1 is test-first).
- The store remains a disposable cache per ADR-008 (no backup, no migration).

## Design decisions
- Acquisition is one `BEGIN IMMEDIATE` transaction (read, classify, insert-with-owner-or-deny); handler execution never holds the write lock (D-1).
- Lease expiry alone yields `reconciliation_required` and never re-authorizes execution; a further attempt requires the reconciliation path gated by `max_attempts` (D-2, REQ-003).
- Terminal rows are write-once: finalization is `UPDATE ... WHERE status='pending' AND owner_id=?` with a typed `DedupLeaseConflict` (new) raised on 0-row results; repeats append to `call_attempt_history` (new) instead of touching the ledger (D-3, REQ-004).
- Identity is a single-row `store_meta` (new) (store UUID, generation, schema fingerprint, config fingerprint, created_epoch) plus `PRAGMA user_version = 1` plus an external installation marker `.mcp_dedup_installed` (new) written atomically at creation (D-4, REQ-005).
- Ledger table renamed `dedup_call_state` (new) to remove the cross-database name collision with the workflow database's `tool_call_state` (D-6).
- Acquisition vocabulary `acquired | replay_completed | in_progress | reconciliation_required | outcome_unknown | contract_mismatch | replay_unavailable`; ledger states unchanged; `review_required` (new) not adopted (D-5).

## Alternatives considered
- Keeping `tool_call_state` as the dedup table name: rejected by D-6 (ownership-name collision in `tools/check_db_separation.py`).
- `touch()`-style empty-file recovery: rejected by REQ-007 (creating an empty file alone must never resolve).
- In-DB installation marker instead of an external file: rejected by D-4 (marker presence must survive DB deletion to distinguish `lost` from `first_initialization` (new)).

## Implementation
### Target file
`scripts/shared/mcp_dedup.py`
### Procedure
Rewrite the store module in five coherent blocks: canonical schema, acquisition API, lease/finalization API, identity/start-state layer with operator resolution, and config-loader keys. Delete the removed APIs in the same commit so no caller can silently keep using them.
### Method
1. Schema: replace `_SCHEMA`/`_INDEXES`/`_CANONICAL_DDL` with `dedup_call_state` (new) (adds `owner_id`, `lease_expires_epoch` (new), `attempt_number`), `store_meta` (new), `call_attempt_history` (new); stamp `PRAGMA user_version = 1` at creation.
2. Acquisition: add `try_acquire_execution(key, tool_name, args_hash, snapshot_json, owner_id)` (new) implementing D-1; remove `lookup`, `record_pending`, and the `force=True` parameter.
3. Lease/finalization: add `renew_lease` (new); keep `record_completed`/`record_failed`/`mark_interrupted` but make them owner-conditional with exact 1-row assertions raising `DedupLeaseConflict` (new); reclassify `classify_interrupted` on lease state, not only `created_epoch`.
4. History: append-only `call_attempt_history` (new) writes (key, attempt_number, owner, outcome, detail, recorded_epoch); terminal `snapshot_json` never rewritten; `purge_expired` deletes only terminal rows and history older than `retention_days`.
5. Identity: at creation write `store_meta` (new) + `user_version` stamp + marker `.mcp_dedup_installed` atomically; at open classify `first_initialization | healthy | lost | replaced | legacy_or_unverified | schema_mismatch` (REQ-006); replace `resolve_lost_store`/`touch()` with an operator resolution operation that validates the state, archives the old file (`<path>.corrupt-<ts>`, ADR-008 Decision 22 style), creates a new generation, and logs the decision durably; surface shape-mismatch failures as the typed `store_error` taxonomy instead of a raw `RuntimeError` (REQ-006).
6. Config: loader validation for `lease_seconds` (new) and `max_attempts` with defaults and rejection of out-of-range/unknown values (REQ-010); file edit itself is row 04.
7. Keep `DEDUP_SENTINEL_NAME`/`.mcp_dedup_resolved` only if the operator-resolution flow still needs an explicit resolution handshake; the installation marker is the new primary marker. Record the final decision in this document's Blocker Log if resolution is simplified.
### Details
- Removed today (verified 2026-11-21): `lookup`, `record_pending(..., force=True)` force-reset path, single-table `_SCHEMA` (`tool_call_state`), `resolve_lost_store()` + `touch()`, unstamped `PRAGMA user_version` (tests pin `== 0`).
- `lost_or_recreated` detection and the `.mcp_dedup_resolved` sentinel in `__init__` are replaced by the start-state classification; the current `classify_interrupted`/`mark_interrupted` are currently unused outside tests (vulture baseline) and gain real callers here.
- `load_dedup_config` is at radon C(18): new key validation must not push it further; extract a per-key validator helper if needed.
- Connect with explicit `timeout` (busy_timeout) so cross-process `BEGIN IMMEDIATE` behavior is deterministic (Plan Risks).

## Compatibility considerations
- Breaking change to the store API: `scripts/mcp_servers/dispatch.py` adopts the new API in the same release unit (row 02 document); `scripts/agent/tool_runner.py` and `scripts/agent/workflow/tool_call_state_ops.py` use the workflow database's distinct `tool_call_state` table and state-key path and are confirmed unaffected (Plan Consumer-scan dispositions).
- Existing pre-change databases are refused as `legacy_or_unverified` (new) and archived-and-recreated by the operator (no migration, ADR-008 Decision 22).
- `execution_snapshot` consumes the identity component in row 03.

## Security considerations
- Terminal evidence immutability (REQ-004) is the anti-tampering property: no code path may rewrite a terminal row's `snapshot_json`.
- Typed start-state errors close the current masking gap where a shape mismatch collapses into the generic disabled-store fallback (Plan Design verification finding).

## Rollback considerations
- Rollback is revert-the-commit inside the release unit. A store file created by the new code carries `user_version = 1` and `dedup_call_state` (new); old code refuses it, so rollback also requires deleting (or archiving) the new-format file — acceptable because the store is a disposable cache and production has no store file today.

## Validation plan
- `uv run pytest tests/shared/test_mcp_dedup.py tests/shared/test_mcp_dedup_concurrency.py tests/shared/test_mcp_dedup_identity.py` (row 09/10/11 documents).
- `rg -n "record_pending|force=True" scripts/` shows no store-side hits after Phase 3.
- Full static gate per `rules/toolchain.md`; radon must not worsen `load_dedup_config`.

## Completion criteria
- AC-1..AC-6 store-side guarantees hold under the Phase 1/3 test suites; no `force` parameter exists; every finalization asserts exactly one updated row; all six start states classify correctly; operator resolution records the decision and rolls the generation.

## Out of Scope
- Caller adoption (`scripts/mcp_servers/dispatch.py`, row 02), the config file edit (row 04), snapshot component (row 03), deploy initialization (row 08), docs (rows 17-23).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261121-105116 | 20261121-110918 | Lands after Phase 1 test documents show confirmed failures Rewrite landed in five blocks: dedup_call_state+store_meta+call_attempt_history DDL with user_version=1 stamp; try_acquire_execution (BEGIN IMMEDIATE, D-1 vocabulary); owner-conditional renew_lease/record_completed/record_failed/mark_interrupted + DedupLeaseConflict on 0-row; identity/start-state layer + resolve_store operator resolution (archive .corrupt-<ts>, generation rollover, healthy refused); per-key config validators. Sentinel .mcp_dedup_resolved and resolve_lost_store/touch() removed entirely (Method item 7 decision: marker+generation is the only resolution handshake; recorded here per instruction). |
| 2 | Coordinate with row 09/10/11 test documents until all three suites pass | Completed | 20261121-110930 | 20261121-113448 | Test files are separate target rows, not companions Rows 10/11 suites now green (22/22) against the new store; row 09 rewrite is the Phase 3 anchor. Coordinated to green: rows 10/11 suites 22/22; row 02 dispatch rewrite landed against this API (tests/mcp_servers 2662 passed). Kill-during-dispatch probe fixed with flush=True before os._exit(0). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-123817 | radon gate on `load_dedup_config` Static gates green: ruff check/format, mypy clean. radon: load_dedup_config B(10) vs C(18) baseline (improved); resolve_store C(17), _acquire_locked C(15) carry the new acquire/state machine. Size-gate follow-up (2026-11-21): the rewritten module reached 46876 B, above the 24576 B gate, so it was split into the shared/mcp_dedup* family: mcp_dedup.py (facade, lifecycle/identity/resolution, all sqlite3.connect), mcp_dedup_config.py (REQ-010 config), mcp_dedup_schema.py (DDL + state vocabularies), mcp_dedup_rows.py (records + typed errors), mcp_dedup_ledger.py (DedupLedger base of DedupStore). The public import path 'from shared.mcp_dedup import ...' is unchanged; every member is under the gate. Follow-up fix 2026-11-21 (found by row 08 sandbox test): DedupStore.__init__ moved PRAGMA journal_mode=WAL after _classify_or_create; WAL conversion rewrites the DB header, so a refused (legacy/mismatch) open must never execute it. Refused opens are now strictly read-only. |

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
- **Requirement ID**: REQ-001..REQ-007, REQ-010
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-083728_mcpdl002_store-identity-continuity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-093956
- **Related target files**: `scripts/shared/mcp_dedup.py`