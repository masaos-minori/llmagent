## Goal

Make `Broker.slow_consumer_count()` (`scripts/eventbus/broker.py`) report the current
slow-subscriber count without mutating any metric, replacing the cumulative
`_slow_consumer_total` side effect so a read-only `/health` poll no longer inflates a
counter (REQ-003; Acceptance 2).

## Scope

- Modify only `scripts/eventbus/broker.py`: `slow_consumer_count()` (current lines 127-136)
  and the module-level metric definition (lines 18-21).

## Assumptions

- `slow_consumer_count()` is called from `health_route.py:57` on every poll, so any metric
  mutation inside it violates REQ-003 ("metrics MUST NEVER be mutated from health reads").
- The current count is derivable inside the broker's own consumer loop, where slow
  subscribers are detected — that is the correct place to update a gauge, not the read.
- Owner/engineering decisions UNK-05 (gauge-of-current-count vs transition-only counter) and
  UNK-03 (whether the current count is exposed as a separate gauge) are recorded before this
  row executes; this procedure implements the plan's recommended branch and flags the
  alternative in Design decisions.

## Design decisions

- **Gauge of current count.** Add a `Gauge("eventbus_slow_consumer_current", ...)` (new) and
  set it where the slow-subscriber count is computed in the consumer loop; remove the
  `_slow_consumer_total.inc(count)` side effect from `slow_consumer_count()` so the read is
  pure (REQ-003; Acceptance 2). This gives alerting a level to fire on rather than a rate.
- **Pure read.** `slow_consumer_count()` returns the current count unchanged for callers; it
  performs no metric operation.

## Alternatives considered

- Transition-only counter: keep `_slow_consumer_total` but increment only on state
  transitions (0→N, N→0, or threshold-crossing). Adopt only if the owner explicitly wants a
  rate metric (UNK-05); recorded, not prescribed.
- Keeping the current `.inc(count)` in the read: rejected — it inflates the counter on every
  health poll, the defect being fixed.

## Implementation

### Target file

`scripts/eventbus/broker.py`

### Procedure

1. Replace the module-level `_slow_consumer_total = Counter(...)` (lines 18-21) with a gauge
   `eventbus_slow_consumer_current` (new): `from prometheus_client import Counter, Gauge` and
   define the gauge next to the existing `_broker_publish_failure_counter`.
2. In `slow_consumer_count()` (lines 127-136), delete the `_slow_consumer_total.inc(count)`
   call (line 135) so the method only computes and returns the current count — no metric
   mutation.
3. Set the new gauge to the current count at the single point in the consumer loop where slow
   subscribers are detected (the location that currently feeds the `.inc(count)`), so the
   gauge reflects live state without a read-time side effect.
4. Keep `slow_consumer_count()`'s return signature (`int`) unchanged.

### Method

In-place edit of the metric definition and `slow_consumer_count()`; add the gauge import.

### Details

- If the slow count is not otherwise computed in the loop, derive it from the same subscriber
  scan the current code uses and `.set(value)` the gauge there.
- The gauge name `eventbus_slow_consumer_current` (new) is additive; existing monitors reading
  the returned int are unaffected.

## Compatibility considerations

- Renaming a cumulative `_total` counter to a gauge changes the Prometheus series type. Record
  the change in `docs/24_eventbus/eventbus_10_health_endpoint.md` (seq 13) so monitors/alerts
  are updated (Risk in the plan).

## Security considerations

- N/A: no auth, secrets, or token handling. The change removes a metric side effect; it has no
  security impact beyond observability accuracy (INV-05 is satisfied — no tokens in metrics).

## Rollback considerations

- Revert the commit; the previous `_slow_consumer_total` counter is restored.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py` — assert the gauge reflects the
  current count and that repeated `slow_consumer_count()` / `/health` polls do not increment a
  cumulative counter.
- `uv run pytest tests/eventbus/` — full EventBus suite passes; no behavior regression.
- `uv run radon cc scripts/eventbus/broker.py`; keep complexity at or below baseline.
- `uv run vulture`, `uv run bandit scripts/eventbus/ -c pyproject.toml`.
- `uv run mypy`, `uv run ruff` on the file.

## Completion criteria

- `slow_consumer_count()` returns the current count with no metric mutation; a new gauge holds
  the current count and is updated only on the consumer loop, not on reads.

## Out of Scope

- Exposing the current count as a separate HTTP/metrics field (covered by health_route.py,
  seq 3, and UNK-03).
- The gauge-vs-transition decision (UNK-05) — implement the recorded owner/engineering decision;
  if unresolved, stop and ask the owner before executing this row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Make `slow_consumer_count()` a pure read and replace `_slow_consumer_total` with a gauge of current count | Pending | — | — | UNK-05 owner/engineering decision must be confirmed before execution |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-05 (gauge vs transition-only counter) is an owner/engineering decision | Classified non-blocking 2026-10-25; concrete value still needed | Yes | 20261025 |

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
- **Related target files**: `scripts/eventbus/broker.py`
