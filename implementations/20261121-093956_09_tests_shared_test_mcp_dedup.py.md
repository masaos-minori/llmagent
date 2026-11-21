## Goal

Rewrite `tests/shared/test_mcp_dedup.py` for the new lease/identity contract: acquisition/finalization matrix, attempt history, updated fingerprint gate, TTL purge scope, and lease-expiry reconciliation classification (REQ-001..REQ-005; AC-1..AC-5).

## Scope
**Release unit**: dedup-lease-identity-rollover

## Assumptions
- Phase 1 documents (rows 10/11) land first and carry the concurrency/identity matrices; this file keeps the single-process state machine and config coverage.
- Row 01 provides the new store API (`try_acquire_execution`, `renew_lease`, owner-conditional finalization, identity/marker creation, operator resolution).

## Design decisions
- Update the `TestFingerprintGate` pin from `PRAGMA user_version == 0` to the stamped identity (`== 1` plus a `store_meta` row), matching Plan Design finding "the test pins `user_version == 0` while docs claim 1".
- `TestLostOrRecreatedDetection` and `resolve_lost_store` usages are replaced by the start-state classification matrix exercised through `DedupStore` open; `TestTtlPurge` is rewritten for terminal-rows-only purge including `call_attempt_history` retention.
- Owner-conditional finalization tests assert the typed `DedupLeaseConflict` on non-owner and stale-owner updates (exactly-one-row rule).

## Alternatives considered
- Keeping the old tests with `xfail` until Phase 3: rejected — the suite must express the new contract as passing regression coverage (repository test policy: no xfail-expiry pattern).

## Implementation
### Target file
`tests/shared/test_mcp_dedup.py`
### Procedure
Rewrite the store-level suites in place; keep the `store(tmp_path)` fixture idiom, switching fixture setup to the new creation path.
### Method
1. State machine (`TestStateMachine`): acquisition result matrix (`acquired`/`replay_completed`/`in_progress`/`contract_mismatch`), owner vs non-owner heartbeat/finalization, terminal immutability (no `force`, no terminal reset), attempt-history append on repeat attempts.
2. `TestFingerprintGate`: stamped identity assertions (`user_version == 1`, `store_meta` presence, fingerprint drift -> typed mismatch).
3. `TestReopenDurability`, `TestCrossProcessSharing`: re-open against an existing healthy identity; remove `resolve_lost_store` usage.
4. `TestTtlPurge`: terminal rows and history purged by `retention_days`; pending rows never purged.
5. `TestInterruptedClassification`: lease-state-driven classification; expiry yields `reconciliation_required`, never re-authorization.
6. `TestConfigValidation` / `TestConfigResolutionAndCache`: add `lease_seconds`/`max_attempts` validation cases (row 04 keys; AC-8).
### Details
- Current class set (verified 2026-11-21): `TestStateMachine`, `TestReopenDurability`, `TestFingerprintGate`, `TestCrossProcessSharing`, `TestTtlPurge`, `TestInterruptedClassification`, `TestConfigValidation`, `TestConfigResolutionAndCache`, `TestLostOrRecreatedDetection`.
- The current file imports `resolve_lost_store` and pins `user_version == 0`; both usages disappear with this rewrite.

## Compatibility considerations
- This is the regression anchor for the store contract; downstream suites (rows 12/13 companions, row 15) depend on the store API this file pins.

## Security considerations
- N/A: test suite.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- `uv run pytest tests/shared/test_mcp_dedup.py` green after rows 01/02/04 land (Phase 3); must be red against the pre-change store where the contract differs (confirms the tests encode the new behavior).

## Completion criteria
- AC-1..AC-5 single-process guarantees green; fingerprint gate matches the stamped identity; no removed-API usage remains in the file.

## Out of Scope
- Multi-caller concurrency (row 10), identity/loss matrix (row 11), dispatcher fixtures (row 02 companions).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the suites per Implementation > Method | Pending | — | — | Lands in Phase 3 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001..REQ-005
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-083728_mcpdl002_store-identity-continuity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-093956
- **Related target files**: `tests/shared/test_mcp_dedup.py`
