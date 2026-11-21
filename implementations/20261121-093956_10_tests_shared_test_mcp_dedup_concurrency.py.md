## Goal

Create `tests/shared/test_mcp_dedup_concurrency.py` as test-first evidence (Plan Phase 1): one logical key under concurrent callers acquires exactly once, and lease/recovery races behave per the new contract — written and confirmed failing against the current store before row 01 lands (REQ-001..REQ-003; AC-1..AC-3).

## Scope
**Release unit**: N/A: lands alone in Plan Phase 1 (test-first; the rollover units cover Phases 2-4)

## Assumptions
- The file is new; the containing directory `tests/shared/` exists.
- Phase 1 evidence (the specific failing behaviors: double-acquire via `record_pending(force=True)`, force-reset evidence loss, lease-absent recovery) is recorded in this document's Execution Status notes and mirrored into the Plan's Phase 1 notes (UNK-05 answer).
- Determinism policy: fixed seeds, bounded fixed-duration scheduling, one short lease value, no real sleeps beyond it; classified per repository slow-test policy (Plan Risks mitigation).

## Design decisions
- Coverage split: this file owns multi-caller races only (async, multi-connection, multi-process); single-process state machine stays in row 09; loss/identity states stay in row 11.
- Multi-process claim races run via short-lived subprocesses against one DB path (proves `BEGIN IMMEDIATE` + busy_timeout semantics), not threads only.

## Alternatives considered
- Marking the tests `xfail` until Phase 2: rejected — Phase 1 requires executed, confirmed-failing evidence, and the repository skill (`skills/python-test-and-fix/SKILL.md:23`) forbids an expiring-xfail policy.

## Implementation
### Target file
`tests/shared/test_mcp_dedup_concurrency.py` (new)
### Procedure
Write the failing-first concurrency suite against today's `DedupStore`, then keep it as the Phase 3 gate that must pass after row 01/02 land.
### Method
1. 100 concurrent async callers on one key via `asyncio` against one store: exactly one `acquired`, the rest `in_progress`/`replay_completed` per state (AC-1).
2. Multi-connection ownership: separate `sqlite3` connections / `DedupStore` instances in one process — heartbeat/finalization by a non-owner fail with the typed conflict (AC-1/AC-2).
3. Multi-process claim race: two subprocesses attempt acquisition on the same key; exactly one wins (REQ-001 transaction contract).
4. Heartbeat extends the lease and blocks stale recovery; without heartbeat the lease expires to `reconciliation_required` only — never a new acquisition grant (AC-3).
5. Finalization-vs-recovery race: the last heartbeat winner finalizes; the loser's finalization raises the typed conflict; an old owner cannot finalize after recovery (AC-1).
6. Kill-during-dispatch: subprocess killed mid-handler leaves an expired `pending` row that only classifies to `reconciliation_required`/`interrupted` with outcome-unknown semantics (REQ-003, AC-3).
### Details
- Phase 1 run must record the current-code failures (double-acquire and force-reset loss are reachable today through `lookup` + `record_pending(force=True)`); record commands + observed failure names in Execution Status notes.

## Compatibility considerations
- Against current code the suite fails by design in Phase 1; from Phase 2 on it is a passing regression member (slow-test classification applies).

## Security considerations
- N/A: test suite.

## Rollback considerations
- N/A: the file is additive; deleting it (revert) is the rollback.

## Validation plan
- Phase 1: `uv run pytest tests/shared/test_mcp_dedup_concurrency.py` — confirm and record failures.
- Phase 3+: same command green; `uv run pytest tests/shared/` stays green as a whole.

## Completion criteria
- AC-1..AC-3 concurrency guarantees pass after the store rewrite; Phase 1 failure evidence is recorded; no flaky behavior across repeated runs (deterministic scheduling).

## Out of Scope
- Store implementation (row 01), identity/loss matrix (row 11), dispatcher behavior (row 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the suite (new file) against current code | Pending | — | — | |
| 2 | Run Phase 1 evidence pass and record failures (feeds UNK-05 answer) | Pending | — | — | |
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
- **Requirement ID**: REQ-001..REQ-003
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-083728_mcpdl002_store-identity-continuity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-093956
- **Related target files**: `tests/shared/test_mcp_dedup_concurrency.py`
