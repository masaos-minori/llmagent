# Keep the slow-consumer gauge current without depending on health reads

## Priority
Low

## Summary
Decide and implement one consistent contract for `eventbus_slow_consumer_current`: either refresh the gauge when a subscriber queue drains, so it tracks current state without any external trigger, or narrow the documentation to the triggers that actually refresh it. In both cases, make the broker's slow-consumer read free of metric side effects.

## Background
Source: `memo-issue.md` item 02, re-verified against current source on 2026-10-29. Most of that item is already resolved or decided:
- The gauge is refreshed on subscribe, on unsubscribe (which also covers an overflow disconnect), and set to zero on shutdown (`Explicit in code`, `EventBroker` in `scripts/eventbus/broker.py`). This is the outcome of `plans/done/20261028-094217_ebmetrics006_correct-db-timing-health.md`.
- That plan also decided to remove the always-`null` `integrity` placeholder from `/health`, so the memo's "implement integrity" request is a reversal of an archived owner decision, not a defect. It is not filed here (see Unresolved Questions).
- The service serves no Prometheus scrape endpoint, so the gauge is in-process only (`docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `Documentation only`; no exposition call exists under `scripts/eventbus/`, `Explicit in code`).

What remains (`Explicit in code`): `EventBroker.slow_consumer_count()` is a read that calls `_refresh_slow_consumer_gauge()`, which writes the gauge. `health_check()` calls it on every poll. The SSE loop in `scripts/eventbus/subscribe_route.py` drains `sub.queue` with `queue.get()` and does not refresh the gauge. The recovery test `TestSlowConsumerGauge.test_slow_consumer_gauge_returns_to_zero_after_recovery` in `tests/eventbus/test_eventbus_slow_consumer.py` drains the queue and then calls `broker.slow_consumer_count()` before asserting the gauge, so the read itself performs the refresh (`Verified by test`).

## Problem
After a subscriber's queue drains below the threshold with no unsubscribe, the gauge keeps its previous positive value until the next `/health` poll or the next subscribe or unsubscribe. `docs/24_eventbus/eventbus_10_health_endpoint.md` states that the gauge "returns to zero after recovery", which holds only after one of those triggers. A health read also mutates a metric, so the gauge value depends on polling.

## Reason for Change
Documentation and code disagree on when the gauge returns to zero, and a read method has a write side effect. Impact is limited because the gauge is not exported and `/health` always reports a freshly computed count, so no operator-visible value is wrong today. Priority is Low; the issue becomes relevant if a scrape endpoint is added.

## Implementation Intent
Choose one contract, and apply it in both code and documentation:
- Option A (state tracks reality): refresh the gauge where queue depth changes, that is on publish fan-out and on drain, and make `slow_consumer_count()` a pure read.
- Option B (refresh on defined triggers): keep the current trigger set, make `slow_consumer_count()` a pure read with an explicit, separately named refresh used by `health_check()`, and narrow the documentation to the triggers that exist.

Recommendation: Option A if a scrape endpoint is planned, otherwise Option B, since it is the smaller change. Keep the slow-consumer threshold comparison and its naming identical between `/health` and the gauge.

## Target Files or Areas
- `scripts/eventbus/broker.py` (`EventBroker`, `slow_consumer_count`, `_refresh_slow_consumer_gauge`)
- `scripts/eventbus/subscribe_route.py` (queue drain loop), only under Option A
- `scripts/eventbus/health_route.py` (`health_check`), only if a separate refresh call is introduced
- `tests/eventbus/test_eventbus_slow_consumer.py`
- `docs/24_eventbus/eventbus_10_health_endpoint.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`

## Required Changes
- Make `EventBroker.slow_consumer_count()` side-effect free.
- Implement the chosen option so that the gauge value and the `/health` `slow_consumers` value are derived from the same threshold comparison.
- Change the recovery test so it asserts the gauge value according to the chosen contract: under Option A, assert the gauge after a drain with no intervening read; under Option B, assert that the documented trigger refreshes it.
- Add a test that repeated `slow_consumer_count()` calls do not change the gauge.
- Align the threshold wording in the docs with the code: the code treats a queue depth equal to the threshold as slow, while `eventbus_07_configuration-and-operations.md` says "exceeds".

## Constraints
- `/health` response fields and the `slow_consumers_detected` degraded reason keep their current meaning.
- No scrape endpoint is introduced in this issue.
- Docs under `docs/` are written in English and describe current behavior and responsibility only, not implementation locations (`skills/DESIGN.md` Docs content policy).

## Acceptance Criteria
- A read of the slow-consumer count does not change `eventbus_slow_consumer_current`.
- The documented trigger set for returning the gauge to zero is exactly what the code and tests demonstrate.
- A test pins the behavior of a queue drain with no unsubscribe, and fails if the contract regresses.
- `/health` `slow_consumers` and the gauge agree whenever the gauge has been refreshed under the chosen contract.
- The threshold comparison wording in the docs matches the code.

## Testing Expectations
- Unit tests in `tests/eventbus/test_eventbus_slow_consumer.py` for drain, repeated reads, unsubscribe, overflow disconnect, and shutdown; the Prometheus gauge is read from the collector, not through a health call.
- `uv run pytest tests/eventbus` passes.
- `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, and `uv run bandit -r scripts/eventbus -c pyproject.toml -ll` pass for the changed files.
- `uv run python tools/check_docs_consistency.py --domain eventbus` and `uv run python tools/check_docs_quality.py` pass after the doc edit.

## Documentation Impact
Yes. `eventbus_10_health_endpoint.md` must state when the gauge is refreshed and when it returns to zero, and `eventbus_07_configuration-and-operations.md` must match the code's threshold comparison. Document operational behavior and failure semantics only.

## Out of Scope
- `/health` integrity reporting (archived decision in `plans/done/20261028-094217_ebmetrics006_correct-db-timing-health.md`).
- A Prometheus scrape endpoint and other counters (`eventbus_jsonl_append_failure_total` and similar).
- DB lock-wait and query-duration metrics, and the broker backlog threshold.

## Dependencies
N/A: none. `plans/done/20261028-094217_ebmetrics006_correct-db-timing-health.md` is archived; its slow-consumer procedure is already implemented in `scripts/eventbus/broker.py`. No open issue or in-flight plan under `issues/` or `plans/` targets `scripts/eventbus/broker.py`.

## Unresolved Questions
- `Needs confirmation`: whether the owner wants `/health` integrity reinstated. The memo requests a meaningful integrity state, while an archived plan decided to remove the placeholder. This issue assumes the archived decision stands; a reversal needs its own issue and a readiness contract decision.
- `Needs confirmation`: Option A or Option B. It depends on whether a scrape endpoint is planned, which is not stated in the repository.
- `Needs confirmation`: whether "exceeds" in `eventbus_07_configuration-and-operations.md` is deliberate wording or a mismatch with the `>=` comparison in code.

## AI Implementation Instruction
- Change only the slow-consumer read and refresh paths, the matching tests, and the two named docs.
- Do not change `/health` response fields, thresholds, or the degraded-reason names.
- Do not add a scrape endpoint or new metrics.
- If the owner has not chosen Option A or B, stop and report instead of choosing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-090247
- **Related target files**: `scripts/eventbus/broker.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/health_route.py`, `tests/eventbus/test_eventbus_slow_consumer.py`, `docs/24_eventbus/eventbus_10_health_endpoint.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`
