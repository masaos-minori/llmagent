## Goal

- Gate the automatic reopening of `interrupted` ledger rows behind a caller-declared recovery permission, so a cancelled non-retryable side effect is refused for reconciliation instead of auto-replayed (REQ-004 refuses recovery outside the retry policy, AC-3 pins both sides).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan validates Phase 2 on its own)

- Modify `scripts/shared/mcp_dedup_ledger.py` only: one keyword-only parameter on `try_acquire_execution()` and `_acquire_locked()`, plus the refusing branch in the `interrupted` case. Companion test file `tests/shared/test_mcp_dedup.py` carries the store-level cases (T-3).

## Assumptions

- This cycle's re-read (20261123) confirmed: `try_acquire_execution()`'s signature is `key, tool_name, args_hash, snapshot, owner_id, *, now_epoch=None` (unchanged by the landed mcpdl004 work), and `_acquire_locked()`'s `interrupted` branch reopens any row below the attempt cap and returns `acquired` — the policy hole REQ-004 closes.
- The mcpdl004 half already landed here (`record_completed()` metadata, `call_state_view()`, DDL pins); the mcpdl005 procedures (generated, not executed) will change `purge_expired()` in this file later. This document touches neither; the implementation phase re-reads the acquisition signature before editing (Plan UNK-06).
- The file measures 23155 B against the 24576 B gate (re-measured this cycle); the parameter and branch add roughly 15 lines, comfortably inside the 1421 B headroom.
- The facade `scripts/shared/mcp_dedup.py` re-exports `DedupStore(DedupLedger)` without re-declaring `try_acquire_execution()`, so no facade edit is needed.
- Refused acquisitions are identified from the row, not from the acquisition result (verification finding, 20261123): `AcquisitionResult` carries no row status, and `AcquisitionResult.lease_expires_epoch` is `None` for every refusal because the contract dataclass pins `owner_id`/`lease_expires_epoch` as set for `acquired` only (`scripts/shared/mcp_dedup_rows.py`, and `tests/shared/test_mcp_dedup.py` asserts `None` on a `replay_completed` refusal). So the sibling gate document (`20261123-205822_02`) tells a recovery-refused `interrupted` row from an expired `pending` row with one read-only `store.get_execution(key)` on the refusal path; no ledger change is needed or wanted here (propagating `stored.lease_expires_epoch` was rejected: it contradicts the contract docstring and this file is out of the gate document's scope).

## Design decisions

- Plan D-4 adopted verbatim: keyword-only `allow_interrupted_recovery` (new) defaulting to `True` (existing callers and store tests keep their behavior); a refused acquisition returns the existing `reconciliation_required` status with `stored=row` and performs no mutation and no history append; no new acquisition status and no row read before the decision (the Plan's rejected alternatives).
- The attempt-cap branch (`outcome_unknown`) stays ahead of the permission check, so a capped `interrupted` row reports `outcome_unknown` exactly as today regardless of permission.

## Alternatives considered

- Teaching the store the tool retry classes: rejected by Plan D-4 — the store stays tool-policy-agnostic; the dispatcher (sibling `20261123-205822_01`) passes its own `_retryable(name)` result through the gate.
- A new recovery_not_permitted status: rejected by Plan D-4 — it would extend the acquisition vocabulary the landed call-state contract must map.

## Implementation
### Target file
`scripts/shared/mcp_dedup_ledger.py`

### Procedure
1. In `try_acquire_execution()`, add keyword-only `allow_interrupted_recovery: bool = True` after `now_epoch`, document it in the docstring (one sentence: recovery of `interrupted` rows requires the caller's permission), and pass it unchanged into `self._acquire_locked(...)`.
2. In `_acquire_locked()`, add the same keyword-only parameter. In the `row.status == "interrupted"` branch, keep the attempt-cap check first, then add: when `allow_interrupted_recovery` is `False`, `return result("reconciliation_required", row.attempt_number, stored=row)` before the `UPDATE ... status='pending'` statement — no mutation, no `_append_history` entry.
3. Leave the `pending`, `completed`, `failed`, and `contract_mismatch` branches, the `_fetch_locked` / `_write_txn` helpers, the DDL, and every other method untouched (the mcpdl005 procedures own `purge_expired()`; the landed mcpdl004 work owns `record_completed()` / `call_state_view()`).

### Method
- Both functions run inside the single `BEGIN IMMEDIATE` transaction `try_acquire_execution()` opens, so the refusal is race-free with concurrent acquirers — the permission branch is a plain early `return` from the same `result()` closure the other refusal branches use.
- Current anchors (re-read before editing): `try_acquire_execution()` at L83 (signature), `_acquire_locked()`'s `if row.status == "interrupted":` branch at L176-195 (`outcome_unknown` cap check at L177, reopen `UPDATE` at L181-190).

### Details
- Refused `reconciliation_required` keeps `attempt_number` at the stored value (not incremented) and `owner_id` at the stored owner, matching the expired-`pending` refusal shape; the terminal snapshot stays untouched, as in today's reopen path (REQ-004 evidence preservation).
- Reopen-with-permission is byte-for-byte today's behavior: `attempt + 1`, `pending`, fresh lease, `post-recovery` history entry — so `tests/shared/test_mcp_dedup.py::test_interrupted_row_survives_reopen` (asserts `acquired` with `attempt_number == 2`) passes unchanged under the default.

### Companion test files
- `tests/shared/test_mcp_dedup.py`
  - Procedure: beside `test_interrupted_row_survives_reopen` (unchanged), add the T-3 refused case: acquire, `mark_interrupted()`, then `try_acquire_execution(..., allow_interrupted_recovery=False)` asserting `status == "reconciliation_required"`, the row still `interrupted` via `get_execution()` with `attempt_number` unchanged and no new `call_attempt_history` row; plus an explicit `allow_interrupted_recovery=True` case asserting the reopen (`acquired`, next attempt number).
  - Validation: `uv run pytest tests/shared/test_mcp_dedup.py tests/shared/test_mcp_dedup_concurrency.py tests/shared/test_mcp_dedup_identity.py -q` green (delete `.testmondata` first).

## Compatibility considerations

- Additive and default-preserving: every existing caller (the dispatcher until sibling seq 01 opts in, the control API, all store tests) keeps the current reopen behavior; the acquisition vocabulary and the `status` CHECK constraint are unchanged (Plan D-6), so no schema bump, version change, or store re-initialization.
- The landed call-state contract's `agent_state_for()` already maps `interrupted -> reconciliation_required`, consistent with the new refusal (Plan UNK-04); no contract-module edit is needed here.

## Security considerations

- The refusal is non-mutating and adds no new write surface; leases, `BEGIN IMMEDIATE`, and the `threading.Lock` discipline are untouched (Plan Risk 1 mitigation).

## Rollback considerations

- The parameter and branch are one commit with no data change (Plan D-4 reversibility: high); reverting restores the unconditional reopen.

## Validation plan

- `uv run pytest tests/shared/ -q` (including the race suite `test_mcp_dedup_concurrency.py` and the identity/fingerprint suite) with `.testmondata` deleted first.
- `uv run python tools/check_module_size.py` — still no violation for this file (23155 B + the small addition, no baseline entry needed).

## Completion criteria

- A recovery-refused acquisition on an `interrupted` row returns `reconciliation_required` with the row unmutated and its history unappended; the permitted path and every pre-existing store test keep their current assertions (T-3 green on both sides).

## Out of Scope

- `scripts/shared/mcp_dedup.py` (facade re-export, unchanged), the gate and dispatcher wiring of the parameter (siblings `20261123-205822_01` and `20261123-205822_02`), and `purge_expired()` retention changes (the mcpdl005 procedures, `implementations/20261123-144326_07_*`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 2: add `allow_interrupted_recovery` (new) to both functions and the refusing branch | Completed | 20261123-221734 | 20261123-222024 | re-read the signature first (UNK-06) ledger recovery gate keyword-only allow_interrupted_recovery added to try_acquire_execution and _acquire_locked |
| 2 | Companion `tests/shared/test_mcp_dedup.py`: add the T-3 permitted/refused reopen cases | Completed | — | 20261123-222024 | Plan Phase 8, validated on its own T-3 permitted/refused/cap cases added to tests/shared/test_mcp_dedup.py |
| 3 | Run the validation sequence (`rules/toolchain.md` + this document's Validation plan) | Completed | — | 20261123-222024 | pytest tests/shared/ 1392 passed; check_module_size clean; ledger 23.6 KB under the gate |

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
- **Requirement ID**: REQ-004 (recovery gated on the declared retry policy), REQ-005 (refusal vocabulary reused unchanged)
- **Source issue**: issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-130937_mcpai001_atomic-dedup-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-205822
- **Related target files**: `scripts/shared/mcp_dedup_ledger.py`, `tests/shared/test_mcp_dedup.py`