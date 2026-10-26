## Goal

Update `tests/eventbus/test_eventbus_slow_consumer.py` so it asserts the slow-consumer figure
is a gauge of the current count and that repeated `/health` polls do not inflate a cumulative
counter (REQ-003; Acceptance 2).

## Scope

- Modify only `tests/eventbus/test_eventbus_slow_consumer.py`, covering
  `test_health_reports_slow_consumer_count` (line 70) and
  `test_health_503_when_slow_consumer_threshold_exceeded` (line 94).

## Assumptions

- This test exercises `broker.slow_consumer_count()` (fixed in seq 1) via `/health`.
- The exact gauge-vs-transition decision (UNK-05) is recorded before execution; this test
  asserts the plan's recommended behavior (gauge of current count, no cumulative inflation).

## Design decisions

- **Gauge + no-inflation.** Assert the gauge reflects the current slow-subscriber count and that
  calling `slow_consumer_count()` (or polling `/health`) repeatedly does not increment a
  cumulative counter (REQ-003; Acceptance 2).

## Alternatives considered

- Asserting a transition-only counter: adopt only if UNK-05 selects that branch; record the
  assertion to match the recorded decision.

## Implementation

### Target file

`tests/eventbus/test_eventbus_slow_consumer.py`

### Procedure

1. In `test_health_reports_slow_consumer_count` (line 70), drive a slow consumer in, poll
   `/health` (or `slow_consumer_count()`) multiple times, and assert the returned/gauge value
   equals the current count and a cumulative counter does not grow across polls.
2. In `test_health_503_when_slow_consumer_threshold_exceeded` (line 94), keep the threshold
   behavior; ensure it does not depend on a cumulative counter growing.

### Method

Adjust assertions in the two named tests; add a helper to read the gauge value if needed.

### Details

- If UNK-05 selects a transition-only counter, assert the counter increments only on state
  transitions instead.

## Compatibility considerations

- Test-only change; no runtime impact.

## Security considerations

- N/A.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py` — gauge reflects current count;
  no cumulative inflation from polls.
- `uv run pytest tests/eventbus/` — full EventBus suite passes.
- `uv run mypy`, `uv run ruff` on the file.

## Completion criteria

- The test asserts the gauge reflects the current count and repeated polls do not inflate a
  cumulative counter.

## Out of Scope

- The slow-consumer metric implementation itself (broker.py, seq 1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update slow-consumer gauge + no-inflation assertions | Pending | — | — | UNK-05 decision gates the exact assertion |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-05 (gauge vs transition-only) recorded; value needed before execution | Classified non-blocking 2026-10-25 | Yes | 20261025 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/done/20261023-154326_eventbus007_side-effects-metrics-health-recovery.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123218_eventbus007_side-effects-metrics-health-recovery.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-092908
- **Related target files**: `tests/eventbus/test_eventbus_slow_consumer.py`
