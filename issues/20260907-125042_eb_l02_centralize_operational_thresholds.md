# Centralize and validate EventBus operational thresholds

## Priority
Low

## Summary
Subscriber queue capacity, the slow-consumer threshold, and the backlog health threshold are
hardcoded in separate modules — confirmed by direct read: `scripts/eventbus/broker.py`'s
`_SLOW_CONSUMER_THRESHOLD = 100` (line 12) and `asyncio.Queue(maxsize=1000)` (line 32), and
`scripts/eventbus/health_route.py`'s `max_queue_depth >= 500` (line 51). None of these values
appear in `scripts/eventbus/config.py`'s `EventBusConfig` dataclass, and there is no documented
rationale or validated relationship between them (e.g. that `500 < 1000`, or that `100 < 500`,
happens to hold today only by coincidence of separately-chosen literals).

## Background
Confirmed by direct read: `EventBusConfig` (`config.py` lines 29-54) has fields for `port`,
`db_path`, `storage_dir`, `offsets_dir`, `deadletter_dir`, `max_retry`, and `host` only — none
of the three thresholds above are represented. There is no `_DLQ_INTERVAL`-style constant
review needed for the sweep interval, since `app.py`'s `_DLQ_INTERVAL = 60.0` (line 52) is
already a single named module constant (not duplicated elsewhere) — memo4.md's "DLQ sweep
interval" mention refers to this constant, which is arguably already centralized in one place,
though not yet in validated configuration.

## Problem
Tuning any of these values today requires editing source in three different files with no
single place that validates their relationships are sensible (e.g. nothing currently prevents
setting the slow-consumer threshold above the queue's own `maxsize`, which would make the
health check's slow-consumer branch unreachable in practice). This makes tuning inconsistent
and can produce misleading health status if the values drift out of a sane relationship.

## Reason for Change
Create one validated source of truth for operational thresholds. Values that affect capacity
and alerting should be configurable where necessary, have safe defaults, and fail validation
when their relationships are invalid.

## Implementation Intent
Inventory all hardcoded EventBus operational thresholds (`_SLOW_CONSUMER_THRESHOLD`, queue
`maxsize`, health's backlog threshold, and the already-single-instance `_DLQ_INTERVAL`). Move
the tunable ones into `EventBusConfig` with documented rationale and safe defaults matching
today's hardcoded values (so behavior is unchanged unless an operator explicitly reconfigures
them). Validate relationships such as slow-consumer threshold being below queue capacity, and
backlog threshold not exceeding queue capacity, in `EventBusConfig.__post_init__` alongside the
existing `port`/`max_retry`/`host` validations.

## Target Files or Areas
- `scripts/eventbus/config.py`
- `scripts/eventbus/app.py`
- `scripts/eventbus/broker.py`
- `scripts/eventbus/health_route.py`
- `docs/06_eventbus_05_configuration-and-operations.md`

## Required Changes
- Inventory all hardcoded EventBus operational thresholds.
- Move tunable values into validated EventBus configuration.
- Document the rationale and default for each threshold.
- Validate relationships such as slow-consumer threshold below queue capacity and backlog
  threshold not exceeding queue capacity.
- Update health checks and broker construction to use the validated values.

## Constraints
- Keep unrelated behavior unchanged — defaults must preserve today's hardcoded values
  (`_SLOW_CONSUMER_THRESHOLD=100`, `maxsize=1000`, backlog threshold `500`) unless an approved
  design change states otherwise.
- Do not weaken fail-closed behavior, validation, or auditability.
- Do not mark this issue complete with documentation-only changes when runtime behavior is
  defective.
- Do not invent configuration values, migration history, or approval evidence.

## Acceptance Criteria
- [ ] All operational thresholds have one canonical source (`EventBusConfig`).
- [ ] Invalid combinations (e.g. slow-consumer threshold >= queue capacity) fail startup with
      actionable errors.
- [ ] Boundary-value tests cover health-state transitions and queue behavior at the configured
      thresholds.
- [ ] Defaults preserve today's hardcoded behavior unless an approved design change states
      otherwise.

## Testing Expectations
Add tests for `EventBusConfig`'s new threshold fields and their validation (valid combination,
invalid combination raising at startup), and boundary tests for `broker.py`'s
`slow_consumer_count()`/`health_route.py`'s degraded-status logic at the configured threshold
values. Run the complete EventBus test suite and the repository's linting, type checking, and
documentation consistency checks.

## Documentation Impact
Update `docs/06_eventbus_05_configuration-and-operations.md` to document each threshold's
rationale, default, and validated relationship to the others as the canonical specification.

## Out of Scope
- Deriving these thresholds from load-test measurement (tracked separately in this batch as
  EB-M05, which defines the evidence-based capacity envelope) — this issue only centralizes and
  validates today's existing hardcoded values into configuration; it does not re-derive them.
- Backpressure disconnect behavior itself (tracked separately in this batch as EB-H02).

## Dependencies
The capacity/latency measurements produced by this batch's EB-M05 issue should inform whether
this issue's default threshold *values* need to change — but this issue can proceed
independently using today's hardcoded values as defaults, then be revisited once EB-M05's
measurements are available.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Preserve today's hardcoded numeric values as the new configuration fields' defaults exactly —
this issue is about centralizing and validating, not re-tuning. Add validation to
`EventBusConfig.__post_init__` alongside the existing `port`/`max_retry`/`host` checks rather
than introducing a separate validation path.
