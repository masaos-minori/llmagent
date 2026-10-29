# Plan: Keep the slow-consumer gauge contract consistent between code and documentation

## Goal
- Make `EventBroker.slow_consumer_count()` a side-effect-free read, refresh `eventbus_slow_consumer_current` only through an explicitly named refresh at the documented triggers, and make the documentation state exactly those triggers and the code's threshold comparison.

## Priority
Low

## Scope
- **In-Scope**: Option B of the Issue (refresh on defined triggers): split the slow-consumer count into a pure read and an explicit refresh in `scripts/eventbus/broker.py`; make `health_check()` call the explicit refresh; update the slow-consumer tests; rewrite the gauge-trigger sentence in `eventbus_10_health_endpoint.md` and the threshold wording in `eventbus_07_configuration-and-operations.md`.
- **Out-of-Scope**: Option A (refreshing the gauge on publish fan-out and on queue drain, which needs a change to the SSE drain loop in `scripts/eventbus/subscribe_route.py`); `/health` response fields, thresholds, and degraded-reason names; `/health` integrity reporting (archived decision in `plans/done/20261028-094217_ebmetrics006_correct-db-timing-health.md`); a Prometheus scrape endpoint and other counters; DB lock-wait and query-duration metrics; the `backlog_health_threshold` wording.
- **Dependencies**: N/A: none. No other open Plan under `plans/` targets `scripts/eventbus/broker.py` or `scripts/eventbus/health_route.py` (checked in Step 3); `plans/done/20261028-094217_ebmetrics006_correct-db-timing-health.md` is archived and its slow-consumer procedure is already implemented.

## Background
`EventBroker` (`scripts/eventbus/broker.py:43`) refreshes the gauge through `_refresh_slow_consumer_gauge()` (line 129), which counts subscribers with `queue.qsize() >= slow_consumer_threshold` and writes the gauge (lines 131-136). It is called from `unsubscribe()` (line 83, which also runs on an overflow disconnect from `publish()` at line 104) and from `slow_consumer_count()` (line 141), and `shutdown()` sets the gauge to zero (line 118). `health_check()` (`scripts/eventbus/health_route.py:66`) calls `broker.slow_consumer_count()` on every poll, so a read mutates a metric. The SSE drain loop in `scripts/eventbus/subscribe_route.py` takes events from `sub.queue` without refreshing the gauge, and `publish()` fan-out does not refresh it either. The service serves no Prometheus scrape endpoint (`eventbus_07_configuration-and-operations.md:138`, `eventbus_09_publish_durability.md:89`), so the gauge is in-process only.

Correction to the Issue (Step 2 finding): the Issue says the gauge is refreshed "on subscribe". `EventBroker.subscribe()` (lines 60-73) does not call the refresh. A newly registered subscriber's queue is empty, so subscribing cannot change the count, and the documented trigger set must not list subscribe.

## Problem
After a subscriber's queue drains below the threshold without an unsubscribe, the gauge keeps its previous positive value until the next `/health` poll or the next unsubscribe. `eventbus_10_health_endpoint.md:82` states that the gauge "returns to zero after recovery", which holds only after one of those triggers. A read method (`slow_consumer_count()`) writes a metric, so the gauge value depends on polling. The recovery test `test_slow_consumer_gauge_returns_to_zero_after_recovery` (`tests/eventbus/test_eventbus_slow_consumer.py:208`) drains the queue and then calls `broker.slow_consumer_count()` before asserting the gauge, so the read itself performs the refresh. Documentation also says the queue "exceeds" the threshold (`eventbus_07_configuration-and-operations.md:138`) or holds "more than" it (line 158), while the code compares with `>=` (`broker.py:134`).

## Reason for Change
Documentation and code disagree on when the gauge returns to zero and on the threshold comparison, and a read method has a write side effect. Impact is limited because the gauge is not exported and `/health` always reports a freshly computed count. Priority is Low; the contract matters if a scrape endpoint is added later.

## Implementation Intent
Apply Option B: keep the current trigger set and make it explicit. A private counting helper holds the single threshold comparison; `slow_consumer_count()` returns it without touching the gauge; a separately named public refresh writes the gauge from the same helper and returns the count; `unsubscribe()` and `health_check()` call the refresh; `shutdown()` still sets the gauge to zero. The documentation then states that the gauge is refreshed on `/health` reads and on unsubscribe (including an overflow disconnect), is set to zero at shutdown, and is not refreshed when a queue drains by itself.

## Requirements
- `REQ-001`: `EventBroker.slow_consumer_count()` does not modify `eventbus_slow_consumer_current`; repeated calls leave the gauge unchanged.
- `REQ-002`: the gauge is written only by an explicitly named refresh method, which `unsubscribe()` and `health_check()` call, and by `shutdown()` (zero); the gauge value and the `/health` `slow_consumers` value come from the same single threshold comparison (`queue depth >= slow_consumer_threshold`).
- `REQ-003`: tests pin the contract: a drain without unsubscribe leaves the gauge stale until a refresh, a refresh brings it to the current count, repeated `slow_consumer_count()` calls do not change the gauge, a `/health` read refreshes it, and unsubscribe, overflow disconnect, and shutdown return it to zero; the gauge is read from the collector, not through a health call.
- `REQ-004`: `eventbus_10_health_endpoint.md` states when the gauge is refreshed and when it returns to zero (exactly the triggers the code and tests demonstrate), and `eventbus_07_configuration-and-operations.md` describes the threshold as reached (`>=`) at both places where it says "exceeds" or "more than", in English and without implementation locations.
- `REQ-005`: `/health` response fields, the `slow_consumers_detected` degraded reason, thresholds, and behavior of existing tests are unchanged.

## Implementation Target Files
**Freeze status**: Frozen (every row is `Verified`; `issue-to-plan` Step 8b
Implementation Target Files Validation passed — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/eventbus/broker.py | Modify | Make `slow_consumer_count()` a pure read; add the explicit public refresh; keep one threshold comparison; `unsubscribe()` calls the refresh | REQ-001, REQ-002, REQ-005; AC-1, AC-2 | `broker.py:129-141` `_refresh_slow_consumer_gauge` writes the gauge and `slow_consumer_count` returns it; `:83` unsubscribe refresh; `:118` shutdown zero; `:134` `>=` comparison (checked in Step 2) | tests/eventbus/test_eventbus_slow_consumer.py | Verified |
| scripts/eventbus/health_route.py | Modify | `health_check()` calls the explicit refresh instead of the read | REQ-002, REQ-005; AC-2, AC-4 | `health_route.py:66` `slow_consumers = broker.slow_consumer_count()`; `:78-79` degraded reason (checked in Step 2) | tests/eventbus/test_eventbus_slow_consumer.py | Verified |
| tests/eventbus/test_eventbus_slow_consumer.py | Modify | Replace read-triggered gauge assertions with explicit-refresh assertions; add drain, repeated-read, and health-refresh tests | REQ-003; AC-1, AC-3, AC-4 | `:208-221` recovery test asserts the gauge after `slow_consumer_count()`; `:223-260` unsubscribe, overflow, shutdown tests call `slow_consumer_count()` before asserting the gauge; `_slow_gauge()` at `:177` reads the collector (checked in Step 3) | The tests themselves | Verified |
| docs/24_eventbus/eventbus_10_health_endpoint.md | Modify | State the gauge refresh triggers and that a self-drained queue does not refresh it | REQ-004; AC-5 | `:82` "It returns to zero after recovery, unsubscribe, an overflow disconnect and shutdown" (checked in Step 2) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| docs/24_eventbus/eventbus_07_configuration-and-operations.md | Modify | Align the threshold wording with the `>=` comparison | REQ-004; AC-5 | `:138` "depth exceeds `slow_consumer_threshold`"; `:158` "holding more than `slow_consumer_threshold` events" (checked in Step 2) | `tools/check_docs_consistency.py --domain eventbus` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/eventbus/subscribe_route.py | The SSE drain loop does not refresh the gauge; it stays unchanged under Option B and is the reason a drain is not a refresh trigger | REQ-002, REQ-004 |
| docs/24_eventbus/eventbus_08_reference_api.md | Generated reference lists `EventBroker` at class level only; confirm it is unchanged after adding a public method | REQ-002 |
| docs/24_eventbus/eventbus_09_publish_durability.md | States that the gauge is registered in-process only and not reported by `/health`; the rewritten text must stay consistent | REQ-004 |
| docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md | Authoritative ADR for broker delivery semantics; confirm no invariant constrains gauge timing | REQ-004 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-003): a read of `slow_consumer_count()` does not change `eventbus_slow_consumer_current`; repeated reads leave it unchanged even when the live count differs from the gauge.
- `AC-2` (REQ-002, REQ-005): the gauge and the `/health` `slow_consumers` value are derived from one threshold comparison, and `health_check()` is the only caller of the explicit refresh outside the broker.
- `AC-3` (REQ-003): a test pins a queue drain with no unsubscribe (gauge stale until refresh, then current) and fails if the contract regresses.
- `AC-4` (REQ-003, REQ-005): a `/health` read refreshes the gauge, and `/health` field names, the `slow_consumers_detected` reason, and existing tests are unchanged.
- `AC-5` (REQ-004): the documented trigger set for the gauge equals what the code and tests demonstrate, and the docs say the threshold is reached (`>=`), not exceeded.

## Tests
- `T1` (REQ-001, REQ-003): repeated `slow_consumer_count()` calls after a drain leave the gauge at its previous value while the returned count is current.
- `T2` (REQ-003): drain without unsubscribe, then the explicit refresh brings the gauge to the current count.
- `T3` (REQ-003): existing unsubscribe, overflow-disconnect, and shutdown tests assert the gauge after the explicit refresh or the trigger itself, reading the collector via `_slow_gauge()`.
- `T4` (REQ-003, REQ-005): a `/health` request refreshes the gauge and still reports `slow_consumers` and the degraded reason.
- `T5` (REQ-004): docs checkers pass after the edits (see Validation plan).

## Documentation Impact
Yes. `docs/24_eventbus/eventbus_10_health_endpoint.md` (Slow Consumer Metric) and `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (Monitoring Slow Consumers and the metrics paragraph) are updated for REQ-004, found through `docs/00_index.md` "Document References by Task" for the Event Bus domain. Document operational behavior and failure semantics only, in English, without implementation locations (`skills/DESIGN.md` Docs content policy).

## Assumptions
- Option B is chosen over Option A as the Issue recommends when no scrape endpoint is planned; the repository states there is none (`eventbus_07_configuration-and-operations.md:138`, `eventbus_09_publish_durability.md:89`). Falsifiable: if the owner plans a scrape endpoint, Option A replaces this Plan's Design (refresh on publish fan-out and drain, touching `scripts/eventbus/subscribe_route.py`).
- The public refresh is a new method name on `EventBroker`; the generated reference lists `EventBroker` at class level only, so `tools/generate_reference_table.py --check` is expected to stay clean (confirmed by running it in implementation).
- "Exceeds" and "more than" in the docs are a mismatch, not deliberate wording: the code compares with `>=` and `eventbus_07_configuration-and-operations.md:61` requires the threshold to be strictly below the queue size. Falsifiable by the owner.
- `backlog_health_threshold` wording ("exceeds" in `eventbus_10_health_endpoint.md:57` versus `>=` at `health_route.py:76`) shows the same mismatch pattern; it is outside the Issue and left unchanged.
- No other `docs/24_eventbus/` text constrains the gauge refresh timing (checked in Step 3).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the owner wants Option A (state tracks reality) instead of Option B | Whether a scrape endpoint is planned is not stated in the repository | Owner confirmation at plan approval; if Option A is chosen, revise this Plan before generating the implementation procedure | False |
| UNK-02 | Whether "exceeds" in `eventbus_07_configuration-and-operations.md` is deliberate wording | Owner intent | Treat as a mismatch with `>=` (REQ-004); owner may veto at plan approval | False |
| UNK-03 | Whether the owner wants `/health` integrity reinstated | Owner decision; contradicts the archived `plans/done/20261028-094217_ebmetrics006_correct-db-timing-health.md` | Out of scope; needs its own issue and a readiness-contract decision | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here is a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/eventbus/broker.py | Modify | Medium — `slow_consumer_count` is called by `health_route.py:66` and tests only; `unsubscribe()` is called by `publish()` and the SSE route (checked in Step 5) | 2 commits | N/A | not applicable (rsynced) |
| scripts/eventbus/health_route.py | Modify | Low — one call site changes; response fields unchanged (checked in Step 5) | 2 commits | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_slow_consumer.py | Modify | Low — test-only | 3 commits | N/A | not applicable (rsynced) |
| docs/24_eventbus/eventbus_10_health_endpoint.md | Modify | Low — one paragraph | 5 commits | N/A | not applicable (rsynced) |
| docs/24_eventbus/eventbus_07_configuration-and-operations.md | Modify | Low — two sentences; high-churn document, so rebase carefully | 21 commits | N/A | not applicable (rsynced) |

## Design
Path B classification (5 target files; the Issue's `Target Files or Areas` list, minus the Option-A-only `subscribe_route.py`).

Analyses (Step 5): architecture — `PYTHONPATH=scripts uv run lint-imports` reports 6 contracts kept, 0 broken; no import changes are needed. Dependency — `slow_consumer_count` is referenced by `scripts/eventbus/health_route.py:66` and `tests/eventbus/test_eventbus_slow_consumer.py` (lines 66, 214, 220, 228, 240, 255) only; `_refresh_slow_consumer_gauge` has no caller outside `broker.py`. Historical — 30-day churn listed in Affected areas; `git shortlog` gave no output, so bus factor is `N/A`. Operational — no port, database, or dependency change; `fuser` check not needed because no DB file is touched. Validation baseline — `radon cc`: `health_check` C (15), `EventBroker.publish` B (6), the slow-consumer methods A; `vulture` reports only pre-existing findings outside `scripts/eventbus/`; `bandit` reports Low only (0 Medium/High); `broker.py` is 5474 B and `health_route.py` 4244 B (under the 20480 B gate); the `diff-cover` baseline number was not measured in this phase (deferred to implementation).

Design decision (Option B, recorded with alternatives): Option A would refresh the gauge on publish fan-out and on every drain, giving a gauge that tracks reality without polling but adding a hot-path write and a change to the SSE drain loop; it is justified only with a scrape endpoint. Option B keeps the trigger set and makes it honest: `slow_consumer_count()` pure, one public refresh method (`refresh_slow_consumer_gauge`) called by `unsubscribe()` and `health_check()`, `shutdown()` zero. Compatibility: the `/health` payload and degraded reasons are unchanged; the only behavior change is that a bare `slow_consumer_count()` call no longer writes the gauge.

Test contract under Option B: the existing assertions `broker.slow_consumer_count() == 1` followed by `_slow_gauge() == 1` (`test_eventbus_slow_consumer.py:214-215,228-229,240-241,255-256`) are changed to call the explicit refresh, because the pure read no longer sets the gauge. The recovery test is rewritten to show the stale-until-refresh behavior.

## Implementation steps
1. **Phase 1: Split the read from the refresh**
   - [ ] Add a private counting helper holding the `>=` comparison; make `slow_consumer_count()` return it without writing the gauge; add the public refresh that writes the gauge from the helper and returns the count; `unsubscribe()` calls the refresh and `shutdown()` keeps setting zero (REQ-001, REQ-002; File Path: scripts/eventbus/broker.py)
2. **Phase 2: Use the explicit refresh on health reads**
   - [ ] Replace the `broker.slow_consumer_count()` call in `health_check()` with the explicit refresh; keep the response fields and the degraded reason (REQ-002, REQ-005; File Path: scripts/eventbus/health_route.py)
3. **Phase 3: Tests**
   - [ ] Change the existing gauge assertions to the explicit refresh, rewrite the recovery test for stale-until-refresh, add the repeated-read test and a `/health`-refreshes-gauge test (REQ-003; File Path: tests/eventbus/test_eventbus_slow_consumer.py)
4. **Phase 4: Documentation**
   - [ ] Rewrite the Slow Consumer Metric paragraph to state the refresh triggers (health reads, unsubscribe including overflow disconnect, shutdown to zero) and that a self-drained queue does not refresh the gauge (REQ-004; File Path: docs/24_eventbus/eventbus_10_health_endpoint.md)
   - [ ] Change "exceeds" and "more than" to the reached (`>=`) wording at both places (REQ-004; File Path: docs/24_eventbus/eventbus_07_configuration-and-operations.md)
5. **Phase 5: Deployment & Verification**
   - [ ] Run the validation plan below; commit and push, then hand off to `skills/deploy/SKILL.md` (deploying is the user's decision, it has an approval gate) (REQ-001, REQ-002, REQ-005; File Path: scripts/eventbus/broker.py, scripts/eventbus/health_route.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_slow_consumer.py | Unit/Integration (drain, repeated read, health refresh, unsubscribe, overflow, shutdown) | `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py -v` | All pass |
| scripts/eventbus | Package regression | `uv run pytest tests/eventbus` | All pass |
| scripts/eventbus/broker.py, scripts/eventbus/health_route.py | Static | `uv run ruff check scripts/eventbus tests/eventbus`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `uv run bandit -r scripts/eventbus -c pyproject.toml -ll` | No errors; no Medium/High |
| scripts/eventbus | Generated reference and size | `uv run python tools/generate_reference_table.py --check`; `uv run python tools/check_module_size.py` | Exit 0 |
| docs/24_eventbus/*.md | Docs consistency | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_consistency.py --domain eventbus`; `uv run python tools/check_docs_japanese.py` | All pass |
| whole change | Architecture / coverage | `PYTHONPATH=scripts uv run lint-imports`; `uv run diff-cover coverage.xml --compare-branch=master` | No violations; changed-line coverage meets `rules/toolchain.md` threshold |

## Risks
- **Risk**: another caller relies on `slow_consumer_count()` refreshing the gauge → **Mitigation**: the dependency check found only `health_route.py:66` and the slow-consumer tests; the full `tests/eventbus` run confirms.
- **Risk**: the gauge is stale between health reads if nothing calls the refresh → **Mitigation**: accepted and documented (REQ-004) because no scrape endpoint exists; UNK-01 records that a scrape endpoint needs Option A.
- **Risk**: doc wording drifts into implementation detail and trips the content-policy checker → **Mitigation**: describe operational behavior only; run `check_docs_content_policy.py --strict`-equivalent gates listed in the Validation plan.
- **Risk**: `eventbus_07_configuration-and-operations.md` has high churn (21 commits in 30 days), so edits may conflict → **Mitigation**: keep the edit to two sentences and rebase before committing.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Split pure read from explicit refresh (scripts/eventbus/broker.py) | In Progress | — | — | REQ-001, REQ-002 |
| 2 | `health_check()` uses the explicit refresh (scripts/eventbus/health_route.py) | In Progress | — | — | REQ-002, REQ-005 |
| 3 | Update and add slow-consumer tests (tests/eventbus/test_eventbus_slow_consumer.py) | In Progress | — | — | REQ-003 |
| 4 | Update gauge-trigger and threshold wording (docs/24_eventbus/eventbus_10_health_endpoint.md, docs/24_eventbus/eventbus_07_configuration-and-operations.md) | In Progress | — | — | REQ-004 |
| 5 | Run validation plan; deploy hand-off | Pending | — | — | Deploy is user-gated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261029-101659_01_scripts_eventbus_broker.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261029-101659_02_scripts_eventbus_health_route.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261029-101659_03_tests_eventbus_test_eventbus_slow_consumer.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261029-101659_04_docs_24_eventbus_eventbus_10_health_endpoint.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261029-101659_05_docs_24_eventbus_eventbus_07_configuration-and-operations.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261029-090247_eventbus002_slow-consumer-gauge-refresh.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261029-092153
- **Related target files**: scripts/eventbus/broker.py, scripts/eventbus/health_route.py, tests/eventbus/test_eventbus_slow_consumer.py, docs/24_eventbus/eventbus_10_health_endpoint.md, docs/24_eventbus/eventbus_07_configuration-and-operations.md

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (side-effect-free read); `broker.py:139-141` (Step 2) | scripts/eventbus/broker.py | Phase 1 | AC-1 | T1 | Confirmed by repository evidence |
| REQ-002 | Required Changes (single threshold comparison); `broker.py:129-141`, `health_route.py:66` (Step 2) | scripts/eventbus/broker.py | Phase 1 | AC-2 | T2, T3 | Confirmed by repository evidence |
| REQ-002 | Required Changes (single threshold comparison); `health_route.py:66` (Step 2) | scripts/eventbus/health_route.py | Phase 2 | AC-2 | T4 | Confirmed by repository evidence |
| REQ-003 | Required Changes (recovery test, repeated-read test); `test_eventbus_slow_consumer.py:208-260` (Step 3) | tests/eventbus/test_eventbus_slow_consumer.py | Phase 3 | AC-1, AC-3, AC-4 | T1, T2, T3, T4 | Confirmed by repository evidence |
| REQ-004 | Required Changes (docs and threshold wording); `eventbus_10_health_endpoint.md:82`, `eventbus_07_configuration-and-operations.md:138,158` (Step 2) | docs/24_eventbus/eventbus_10_health_endpoint.md | Phase 4 | AC-5 | T5 | Confirmed by repository evidence |
| REQ-004 | Required Changes (threshold wording); `eventbus_07_configuration-and-operations.md:138,158` (Step 2) | docs/24_eventbus/eventbus_07_configuration-and-operations.md | Phase 4 | AC-5 | T5 | Confirmed by repository evidence |
| REQ-005 | Constraints (`/health` fields and degraded reason unchanged) | scripts/eventbus/health_route.py | Phase 2 | AC-2, AC-4 | T4 | Explicit in issue |
| REQ-005 | Constraints (`/health` fields and degraded reason unchanged) | scripts/eventbus/broker.py | Phase 1 | AC-2 | T3 | Explicit in issue |