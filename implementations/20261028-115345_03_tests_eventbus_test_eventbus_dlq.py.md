# Procedure: add DLQ fault-injection tests for the counter, sweep isolation and DB failure after file creation

## Goal

Prove the inline counter increment, per-event sweep isolation and the DB-failure-after-file repair path (Plan REQ-003, REQ-005, REQ-006).

## Scope

- Modify only `tests/eventbus/test_eventbus_dlq.py`.
- Test-only change; no source file is edited.

## Assumptions

- Row 1 (`scripts/eventbus/dlq.py`) has landed; the test names and helpers below are created by this procedure.
- Overlap (compatible): `plans/done/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` (archived, procedures pending) also targets `scripts/eventbus/ack_route.py` (authorization at the start of the routes) and `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` (Authentication section and error table); this procedure edits only the promotion block of `_nack_and_promote` and one transition-table row.

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert observable behavior; use barriers or events, never sleeps.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/eventbus/test_eventbus_dlq.py`

### Procedure

- In `test_atomic_write_failure_leaves_db_row_unchanged`, replace the final `len(dlq_fail_lines) > 0` assertion (satisfied by the metric's `# HELP` line) with a before/after comparison of `REGISTRY.get_sample_value("eventbus_dlq_file_write_failure_total")` that expects an increase of 1.
- Add `test_inline_write_failure_increments_counter_and_raises` (new): monkeypatch `dlq._atomic_write` to raise `OSError`, call `promote_single`, assert `pytest.raises(OSError)`, the counter delta of 1 and `dlq_at` still NULL.
- Add `test_sweep_continues_after_one_event_write_failure` (new): two promotable events (insert `consumer_delivery` rows with failure counts at the limit, as `test_reconciliation_orphan_file` does); make `_atomic_write` raise only for the first `event_id`; assert `sweep_orphans` returns 1, the second event has `dlq_at`, the first stays live and the counter moved by 1.
- Add `test_db_failure_after_dlq_file_creation_is_repaired_by_next_sweep` (new): pass `promote_single` a proxy connection whose `commit` raises `sqlite3.OperationalError` (the `_CommitFailingConn` idea from `test_eventbus_publish.py`), assert the file exists and `dlq_at` is NULL, then run `sweep_orphans` on the real connection and assert `dlq_at` is set and the file content is valid JSON.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- The file's `client` fixture and `_event` helper are reused; promotable rows are created with direct `INSERT INTO consumer_delivery` statements as in the reconciliation tests.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_dlq.py -q` | Pass |
| 2 | `uv run ruff format tests/eventbus/test_eventbus_dlq.py`; `uv run ruff check tests/eventbus/test_eventbus_dlq.py` | No finding |

## Completion criteria

- The new tests fail on the pre-change code (no inline counter, sweep aborts) and pass after row 1.

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
- **Requirement ID**: REQ-003, REQ-005, REQ-006 (counter delta, sweep isolation, DB failure after file)
- **Source issue**: issues/20261027-155846_ebdurable003_define-publish-dlq-durability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115345
- **Related target files**: tests/eventbus/test_eventbus_dlq.py
