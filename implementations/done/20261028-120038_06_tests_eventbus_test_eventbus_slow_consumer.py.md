# Procedure: add gauge-reset tests

## Goal

Prove the slow-consumer gauge goes back to zero after recovery, unsubscribe, overflow disconnect and shutdown (Plan REQ-002, REQ-005).

## Scope

- Modify only `tests/eventbus/test_eventbus_slow_consumer.py`.
- Test-only change; no source file is edited.

## Assumptions

- Ordering note: apply this row before the source rows (tests first).
- Overlap (compatible): `plans/done/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` (archived, procedures pending) also targets `scripts/eventbus/route_helpers.py` (a post-lock shutdown re-check placed right after lock acquisition and before the active-user bump) and `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (Shutdown section). This procedure changes the timing statements around the lock and the Metrics section; whichever lands first, re-read the file and keep the other's lines.

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert observable behavior; use barriers or events, never sleeps.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/eventbus/test_eventbus_slow_consumer.py`

### Procedure

- Add `test_slow_consumer_gauge_returns_to_zero_after_recovery` (new): fill a subscriber queue past the threshold, call `broker.slow_consumer_count()` and read `eventbus_slow_consumer_current` (1), drain the queue, call again and assert 0.
- Add `test_slow_consumer_gauge_is_zero_after_unsubscribe` (new), `test_slow_consumer_gauge_is_zero_after_overflow_disconnect` (new) and `test_slow_consumer_gauge_is_zero_after_shutdown` (new) using the broker directly (the file already builds brokers for `test_slow_consumer_threshold_detection`).
- Read the gauge through `REGISTRY.get_sample_value("eventbus_slow_consumer_current")`.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Write before row 2; the first test fails on the unmodified code (the gauge is never reset).

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py -q` | Pass |
| 2 | `uv run ruff format tests/eventbus/test_eventbus_slow_consumer.py`; `uv run ruff check tests/eventbus/test_eventbus_slow_consumer.py` | No finding |

## Completion criteria

- The gauge tests fail on the pre-change code and pass after row 2.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Completed | 20261028-165731 | 20261028-165731 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-165731 | 20261028-165731 |  |

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
- **Requirement ID**: REQ-002, REQ-005 (gauge returns to zero)
- **Source issue**: issues/20261027-155849_ebmetrics006_correct-db-timing-health.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094217_ebmetrics006_correct-db-timing-health.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120038
- **Related target files**: tests/eventbus/test_eventbus_slow_consumer.py