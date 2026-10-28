# Procedure: add the two-connection concurrency test and the index-violation mapping test

## Goal

Force the interleaving in which a second connection passes the existence check before the first commits and assert exactly one success and one `already_redelivered` (Plan REQ-005).

## Scope

- Modify only `tests/eventbus/test_eventbus_requeue_edge_cases.py`.
- Test-only change; no source file is edited.

## Assumptions

- Ordering note: apply this row before the source rows (tests first).
- Overlap (compatible): `plans/done/20261028-093931_adrgate005_enforce-adr-evidence-checks.md` (archived, procedures pending) also targets the ADR-006 file; it renames two stale test citations in the Verification table while this procedure edits Implementation Notes only. Any citation added here must resolve to an existing test node once that Plan's node validation is in force.

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert observable behavior; use barriers or events, never sleeps.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/eventbus/test_eventbus_requeue_edge_cases.py`

### Procedure

- Add `test_concurrent_requeue_from_two_connections_creates_one_descendant` (new): promote an event with `_promote_to_dlq(client)`, open two connections to the test database file with `open_db`, wrap connection B in a proxy whose `execute` signals a `threading.Event` after the `redelivered_from` existence `SELECT` and then waits for a second event, run `redeliver_event` for B in a thread, run `redeliver_event` for A to completion on the main thread, release B and join; assert A returned `success`, B returned `already_redelivered`, and `SELECT COUNT(*) FROM events WHERE redelivered_from = ?` is 1.
- Add `test_redelivered_from_index_violation_maps_to_already_redelivered` (new): insert a descendant row directly, then call `redeliver_event` through a proxy that skips the pre-check, and assert the `already_redelivered` result and `conn.in_transaction is False`.
- Keep `test_requeue_constraint_failure_rolls_back_without_partial_state` unchanged: it proves an `events.event_id` collision still raises `sqlite3.IntegrityError`.
- Bound every wait with a timeout; use no sleeps.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Write before rows 1 and 2 and confirm the concurrency test fails on the unmodified code (two descendants).
- The proxy forwards every attribute it does not override with `__getattr__`, as `_FailingConn` in this file does.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py -q` | Pass |
| 2 | `uv run ruff format tests/eventbus/test_eventbus_requeue_edge_cases.py`; `uv run ruff check tests/eventbus/test_eventbus_requeue_edge_cases.py` | No finding |

## Completion criteria

- The concurrency test fails on the pre-change code and passes after rows 1 and 2.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: REQ-002, REQ-005 (concurrency and mapping tests)
- **Source issue**: issues/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120147
- **Related target files**: tests/eventbus/test_eventbus_requeue_edge_cases.py
