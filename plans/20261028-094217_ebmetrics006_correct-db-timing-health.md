## Goal
- Make the EventBus database timing metrics, the slow-consumer gauge and the health contract correct and consistent: lock wait measured only up to acquisition, query duration always recorded, the gauge reset when the state recovers, and one documented readiness predicate shared by the health API and the deployment gate.

## Priority
Medium

## Scope
- **In-Scope**:
  - Fix `run_with_db_lock()` timing in `scripts/eventbus/route_helpers.py`: wait measured until the lock is acquired, query duration observed in a reachable `finally`, contention threshold applied to the wait.
  - Make the slow-consumer gauge reflect the current state, including zero, and refresh it on unsubscribe, overflow disconnect and shutdown.
  - Define liveness and readiness once, remove the always-`null` `integrity` placeholder, and document the 503 semantics.
  - Make the readiness gate in `deploy/setup_services.sh` parse the health JSON structurally and use the documented predicate.
  - Replace the vacuous timing and gauge tests with tests that fail on the current code; align the health and operations docs.
- **Out-of-Scope**: new metrics or dashboards; connection pooling or lock strategy; shutdown behavior (`ebshutdown002`); the import facade migration of `route_helpers.py`; renaming any metric.
- **Dependencies**: `plans/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` also edits `_locked()` in `run_with_db_lock`; implement the two in sequence and rebase the later one. The `ebcompat002` Plan is already consumed (`plans/done/20261027-120858_ebcompat002_decide-eventbus-db-facade.md`) and only migrates imports.

## Background
`run_with_db_lock()` records lock wait, query duration and a contention counter in Prometheus histograms and a counter that `health_route.py` averages into `metrics` and into the `lock_wait_high` and `query_duration_high` degraded reasons. `eventbus_slow_consumer_current` is a gauge in `scripts/eventbus/broker.py`. The health payload carries `liveness`, `readiness` and `integrity`. `deploy/setup_services.sh` gates the Event Bus launch on the `/health` body.

## Problem
- `_locked()` ends its `try` with `return func()`, so the `elapsed` computation and `_db_query_duration.observe(elapsed)` after it never run; `vulture` reports the unreachable code. The histogram has no observations, so `query_duration_high` can never fire.
- `lock_wait` is measured from before lock acquisition to the outer `finally`, so it includes query time; the 1 ms contention threshold and the `lock_wait_high` reason (average above 0.01 s) are therefore inflated, and the documented definition ("from thread submit to lock acquisition") is not met.
- `slow_consumer_count()` sets the gauge only when the count is positive, so the gauge never returns to zero; the health doc says it reports the current number.
- `integrity` is always `null` and the doc defers it to a placeholder (`H-03`), while schema versioning is enforced at startup in `scripts/eventbus/schema.py`.
- The deployment gate substring-matches the compacted body text for `"db":"ok"` and `"dlq_task":"running"`. The API's `readiness` field is only the DB check and its `liveness` field is only the DLQ task, so no single documented predicate matches the gate.
- The existing tests do not detect these defects: `test_query_duration_metric_observed` passes because `# HELP` and `# TYPE` lines match its assertion.

## Reason for Change
Alerts and the deployment gate built on these values are not meaningful. No outage is cited; the priority is Medium (observability correctness).

## Implementation Intent
Measure wait until acquisition and hold time from acquisition to callback completion, recorded in `finally`. Set the gauge from the computed count every time. Define the readiness predicate as liveness AND readiness from the existing fields, document it, and make the deployment gate read those fields structurally.

## Requirements
- `REQ-001`: `run_with_db_lock()` observes `eventbus_db_lock_wait_time_seconds` with the time from submission to lock acquisition only, applies the 1 ms contention threshold to that wait, and observes `eventbus_db_query_duration_seconds` from acquisition to callback completion in a `finally`, including when the callback raises; the unreachable lines are removed.
- `REQ-002`: `EventBroker.slow_consumer_count()` sets `eventbus_slow_consumer_current` to the computed count on every call, including zero; the gauge is also refreshed on unsubscribe, overflow disconnect and shutdown.
- `REQ-003`: The health payload no longer contains the `integrity` placeholder; `liveness` (DLQ task running) and `readiness` (database connectable) are defined once, together with the combined gate predicate `liveness and readiness`, and the 503 semantics (any degraded reason, capacity-only reasons included) are documented without changing them.
- `REQ-004`: `deploy/setup_services.sh` parses the `/health` JSON structurally and passes the gate only when `liveness` and `readiness` are both true; a capacity-only 503 still passes, a missing or non-JSON body fails the gate, and a connection failure keeps its retry behavior.
- `REQ-005`: Tests use a controlled wait and hold (barriers, no sleeps) and fail on the pre-change code: uncontended call (near-zero wait, positive duration), contended call (contention counter increments), raising callback (duration still recorded), gauge back to zero after recovery and after unsubscribe.
- `REQ-006`: Health tests cover the database, broker and DLQ-task failure states and assert the gate predicate; a contract test feeds the real health payload to the deployment predicate.
- `REQ-007`: The EventBus health and operations docs state the metric definitions, the corrected metric name `eventbus_slow_consumer_current`, the readiness contract and the 503 semantics as current behavior.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/route_helpers.py` | `run_with_db_lock` timing | Measure wait to acquisition, observe query duration in `finally`, drop the unreachable lines | REQ-001 / AC-1, AC-2 | `_locked()` returns inside the `try`; `vulture scripts/eventbus --min-confidence 80` reports `route_helpers.py:151: unreachable code after 'try'`; `start_time` is read in the outer `finally` (checked in Step 3) | `tests/eventbus/test_eventbus_route_helpers_metrics.py` | Verified |
| `scripts/eventbus/broker.py` | Slow-consumer gauge | Set the gauge unconditionally and refresh it on unsubscribe, overflow disconnect and shutdown | REQ-002 / AC-3 | `slow_consumer_count()` calls `_slow_consumer_current.set(count)` only under `if count > 0`; no other `set` call exists (checked in Step 3) | `tests/eventbus/test_eventbus_slow_consumer.py` | Verified |
| `scripts/eventbus/health_route.py` | Health payload | Remove `integrity`; compute the gate predicate once | REQ-003 / AC-4 | `integrity = None` with the comment "deferred to H-03"; `liveness` and `readiness` computed inline (checked in Step 3) | `tests/eventbus/test_eventbus_health.py` | Verified |
| `deploy/setup_services.sh` | Deployment readiness gate | Replace the substring match with a structural JSON check of `liveness` and `readiness` | REQ-004 / AC-5 | The gate tests `"${EB_LAST_BODY}" == *'"db":"ok"'*` and `*'"dlq_task":"running"'*` on the compacted body (checked in Step 3) | `tests/deploy/test_setup_services_eventbus.py` | Verified |
| `tests/eventbus/test_eventbus_route_helpers_metrics.py` | Timing tests | Replace the vacuous metric-line assertions with sample-value assertions; add contended and raising cases | REQ-005 / AC-1, AC-2 | `test_query_duration_metric_observed` asserts `len(after_lines) > 0 or before_count == 0` and passes on the current code (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_eventbus_slow_consumer.py` | Gauge tests | Add gauge-reset tests after recovery and after unsubscribe | REQ-002, REQ-005 / AC-3 | Existing tests cover detection, health reporting and overflow disconnect but not the gauge value (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_eventbus_health.py` | Health tests | Replace the `integrity is None` assertion; add failure-state and predicate tests | REQ-003, REQ-006 / AC-4 | Asserts `"integrity" in body` and `body["integrity"] is None` (checked in Step 3) | itself | Verified |
| `tests/deploy/test_setup_services_eventbus.py` | Gate tests | Update the health fixtures to include `liveness` and `readiness`; add a malformed-body case and the shared-predicate contract test | REQ-004, REQ-006 / AC-5 | Fixtures `_HEALTH_CAPACITY_ONLY` and `_HEALTH_DB_UNAVAILABLE` carry `db`, `dlq_task` and `degraded_reasons` only; four gate tests exist (checked in Step 3) | itself | Verified |
| `docs/24_eventbus/eventbus_10_health_endpoint.md` | Health endpoint doc | Remove `integrity`; define liveness, readiness, the gate predicate and the 503 semantics; state the metric definitions | REQ-003, REQ-007 / AC-4, AC-6 | The field table lists `integrity` as deferred; the metrics paragraph defines wait as "thread submit to lock acquisition" and the gauge as the current number (checked in Step 3) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Operations doc | Correct the slow-consumer metric name and point the readiness text at the contract | REQ-007 / AC-6 | The Metrics section names `eventbus_slow_consumer_total`; the metric in `broker.py` is `eventbus_slow_consumer_current` (checked in Step 3) | `tools/check_docs_consistency.py --domain eventbus` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/schema.py` | Enforces the schema version at startup, so the `integrity` placeholder is obsolete | REQ-003 |
| `scripts/eventbus/app.py` | Calls `broker.shutdown()` and runs the lifespan the gate depends on | REQ-002 |
| `scripts/eventbus/db_conn.py` | `check_db` is the readiness DB check | REQ-003 |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Generated reference; unchanged unless a public signature changes | REQ-002 |
| `deploy/deploy.sh` | Shows that `setup_services.sh` is run from the repository, not copied | REQ-004 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-005): An uncontended call records a wait below 1 ms and a positive query duration; the unreachable code is gone.
- AC-2 (REQ-001, REQ-005): A contended call increments the contention counter; a raising callback still records its duration.
- AC-3 (REQ-002, REQ-005): The gauge reads zero after the slow consumer recovers and after it unsubscribes, and after shutdown.
- AC-4 (REQ-003, REQ-006): The health payload has no `integrity` field; `liveness` and `readiness` follow the DLQ task and the database; the status code stays 503 for any degraded reason.
- AC-5 (REQ-004, REQ-006): The deployment gate passes for a healthy body and a capacity-only 503, fails for `db_unavailable`, `dlq_task_stopped`, malformed or empty bodies, and uses the same predicate as the API.
- AC-6 (REQ-007): The docs state the metric names, definitions, the readiness contract and the 503 semantics, and `tools/check_docs_consistency.py --domain eventbus` passes.

## Tests
- Controlled-timing tests with barriers for wait versus hold, the contention counter and the exception path, asserting histogram sample values rather than the presence of metric lines (REQ-001, REQ-005).
- Broker tests for the gauge after recovery, unsubscribe, overflow disconnect and shutdown (REQ-002, REQ-005).
- Health route tests for DB, broker and DLQ-task failure states and the gate predicate (REQ-003, REQ-006).
- Deployment gate tests with the updated fixtures, a malformed body, and a contract test that feeds the real health payload to the gate predicate (REQ-004, REQ-006).
- Run `uv run pytest tests/eventbus tests/deploy -q`, mypy and ruff; confirm each new timing and gauge test fails on the pre-change code.

## Documentation Impact
Yes (REQ-007): the health endpoint and operations docs under `docs/24_eventbus/`, found through `docs/00_index.md` "Document References by Task". State current behavior only.

## Assumptions
- Removing `integrity` is safe: it was always `null`, the deployment gate does not read it, and the only reader is a test that asserts the placeholder.
- Readiness for the gate stays "database connectable and DLQ task running"; the broker is not part of the gate because the existing gate contract and its tests exclude it (UNK-01).
- Once the query-duration histogram receives observations, `query_duration_high` can fire (average above 0.05 s) and `lock_wait_high` fires less often because wait no longer includes query time; both are capacity-only reasons and keep the existing 503 behavior.
- Overlap judgment (compatible): `plans/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` also targets `scripts/eventbus/route_helpers.py`, but it adds a shutdown re-check immediately after lock acquisition while this Plan changes the timing statements around it; the order of the two edits is not significant. The same Plan also targets `docs/24_eventbus/eventbus_07_configuration-and-operations.md`; it edits the Shutdown section while this Plan edits the Metrics section.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether readiness should also require the broker | Owner decision recorded as `Needs confirmation` in the Issue | Plan default keeps the broker out of the gate; the owner may extend the predicate before `plan-to-implementation-procedure` | False |
| UNK-02 | Whether any external consumer reads the `integrity` field | No reader in `scripts/`, `deploy/` or `tests/` other than the placeholder test | Owner confirms; the field can stay `null` if one exists | False |
| UNK-03 | Whether the deployed host provides `jq` or only Python for the structural parse | Not checked on the production host | Use the repository Python (`uv run` is already used in the script) so no new tool is required | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/route_helpers.py` | Modify | High | 2 | High (single author) | not applicable (rsynced) |
| `scripts/eventbus/broker.py` | Modify | Medium | 1 | N/A | not applicable (rsynced) |
| `scripts/eventbus/health_route.py` | Modify | Medium | 1 | N/A | not applicable (rsynced) |
| `deploy/setup_services.sh` | Modify | Medium | 9 | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_route_helpers_metrics.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_slow_consumer.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_health.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/deploy/test_setup_services_eventbus.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_10_health_endpoint.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Path B (10 files; changes the health API payload and the deployment gate). `lint-imports` kept all 6 contracts earlier in this batch; the changes stay in `scripts/eventbus/`, `deploy/` and tests. `radon cc` reports `health_check` at C (15), which this change does not increase. `run_with_db_lock` is used by every route and the DLQ loop, so a timing change affects all of them but changes no return value.
- Decision 1, timing: take `t_submit` before the thread-side lock acquisition, observe wait immediately after `with get_db_lock():` is entered, then observe hold time in a `finally` around `func()`. The contention counter uses the wait only.
- Decision 2, gauge: compute the count in one private helper and always `set` it; call the helper from `slow_consumer_count()`, `unsubscribe()`, the overflow disconnect and `shutdown()`.
- Decision 3, health contract: keep `liveness` and `readiness` as defined, document `liveness and readiness` as the readiness gate, keep HTTP 503 for any degraded reason, and remove `integrity` because startup already enforces the schema version.
- Decision 4, gate: parse the body with the repository Python, require JSON with boolean `liveness` and `readiness`, and keep the no-`-f` curl so a 503 body can be inspected.
- Compatibility: no metric is renamed; `integrity` is removed from the payload; the gate now fails on a non-JSON body that previously could not match either.

## Implementation steps
1. **Phase 1: Tests that expose the defects**
   - [ ] Write the timing tests (uncontended, contended, raising callback) and confirm they fail on current code (REQ-005; `tests/eventbus/test_eventbus_route_helpers_metrics.py`)
   - [ ] Write the gauge tests and confirm they fail on current code (REQ-005; `tests/eventbus/test_eventbus_slow_consumer.py`)
2. **Phase 2: Metrics fixes**
   - [ ] Fix the timing in `run_with_db_lock` (REQ-001; `scripts/eventbus/route_helpers.py`)
   - [ ] Fix the gauge and refresh it on unsubscribe, overflow and shutdown (REQ-002; `scripts/eventbus/broker.py`)
3. **Phase 3: Health contract and gate**
   - [ ] Remove `integrity`, compute the gate predicate once and update the health tests (REQ-003, REQ-006; `scripts/eventbus/health_route.py`, `tests/eventbus/test_eventbus_health.py`)
   - [ ] Make the gate parse JSON structurally and update the gate tests (REQ-004, REQ-006; `deploy/setup_services.sh`, `tests/deploy/test_setup_services_eventbus.py`)
4. **Phase 4: Documentation**
   - [ ] Document the metric definitions, the readiness contract and the 503 semantics (REQ-007; `docs/24_eventbus/eventbus_10_health_endpoint.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`)
5. **Phase 5: Deployment & Verification**
   - [ ] Run the validation plan; after commit and push, hand off to `skills/deploy/SKILL.md` (the user decides to deploy) because `scripts/` and `deploy/` change; confirm the gate passes on a real start and that `/health` shows non-zero query duration after traffic (REQ-004; `deploy/setup_services.sh`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/route_helpers.py` | Controlled-timing unit tests | `uv run pytest tests/eventbus/test_eventbus_route_helpers_metrics.py -q` | New tests fail before the change, pass after |
| `scripts/eventbus/broker.py` | Gauge unit and route tests | `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py -q` | Gauge returns to zero |
| `scripts/eventbus/health_route.py` | Health route tests | `uv run pytest tests/eventbus/test_eventbus_health.py -q` | Payload and status match the contract |
| `deploy/setup_services.sh` | Sandboxed gate tests | `uv run pytest tests/deploy/test_setup_services_eventbus.py -q` | Healthy and capacity-only pass; failure states abort |
| Whole area | Regression | `uv run pytest tests/eventbus tests/deploy -q` | All pass |
| Static | Lint, types, security | `uv run ruff check scripts/ tests/`; `uv run mypy --no-namespace-packages scripts/`; `shellcheck deploy/setup_services.sh` if installed | Clean; shellcheck recorded as Not available if missing |
| Dead code | Unreachable check | `uv run vulture scripts/eventbus --min-confidence 80` | No finding in `route_helpers.py` |
| Coverage | Baseline then raise | diff-cover sequence in `rules/toolchain.md` section 7 | At or above the Completion checklist threshold |
| Docs | Checkers | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_consistency.py --domain eventbus` | No errors |

Baseline recorded in Step 5: `radon cc` reports `health_check` C (15) and no other function at C or above in the three modules; `vulture scripts/eventbus --min-confidence 80` reports only `route_helpers.py:151` unreachable code, which this Plan removes; `bandit -r scripts/` reported no Medium or High finding earlier in this batch.

## Risks
- **Risk**: With real observations, `query_duration_high` begins to appear and `/health` returns 503 more often → **Mitigation**: it is a capacity-only reason that the deployment gate and the documented contract already tolerate; the docs state it and the Plan records it in Assumptions.
- **Risk**: Removing `integrity` breaks a client that expects the key → **Mitigation**: no reader found in the repository (UNK-02); the removal is documented.
- **Risk**: The structural parse in a shell script fails on hosts without the expected interpreter → **Mitigation**: reuse the repository Python already used by the script (UNK-03) and cover malformed and empty bodies in tests.
- **Risk**: Timing tests are flaky → **Mitigation**: use barriers and a controlled clock, never sleeps, and bound every wait.
- **Risk**: Two Plans edit `_locked()` → **Mitigation**: implement in sequence and rebase; the edits touch different statements.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the failing timing and gauge tests | Pending | — | — | |
| 2 | Fix the timing in `route_helpers.py` and the gauge in `broker.py` | Pending | — | — | |
| 3 | Health contract and structural deployment gate with tests | Pending | — | — | |
| 4 | Health and operations docs | Pending | — | — | |
| 5 | Deployment and verification hand-off | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-155849_ebmetrics006_correct-db-timing-health.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-094217
- **Related target files**: `scripts/eventbus/route_helpers.py`, `scripts/eventbus/broker.py`, `scripts/eventbus/health_route.py`, `deploy/setup_services.sh`, `tests/eventbus/test_eventbus_route_helpers_metrics.py`, `tests/eventbus/test_eventbus_slow_consumer.py`, `tests/eventbus/test_eventbus_health.py`, `tests/deploy/test_setup_services_eventbus.py`, `docs/24_eventbus/eventbus_10_health_endpoint.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1 and 2; unreachable code reported by `vulture` | `scripts/eventbus/route_helpers.py` | Step 2 | AC-1, AC-2 | `tests/eventbus/test_eventbus_route_helpers_metrics.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1 and 2; vacuous existing test | `tests/eventbus/test_eventbus_route_helpers_metrics.py` | Step 1 | AC-1, AC-2 | `uv run pytest tests/eventbus -q` | Confirmed by repository evidence |
| REQ-002 | Required Changes 3; gauge set only for positive counts | `scripts/eventbus/broker.py` | Step 2 | AC-3 | `tests/eventbus/test_eventbus_slow_consumer.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 3 | `tests/eventbus/test_eventbus_slow_consumer.py` | Step 1 | AC-3 | `uv run pytest tests/eventbus -q` | Confirmed by repository evidence |
| REQ-003 | Required Changes 4; `integrity = None` | `scripts/eventbus/health_route.py` | Step 3 | AC-4 | `tests/eventbus/test_eventbus_health.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 4 | `tests/eventbus/test_eventbus_health.py` | Step 3 | AC-4 | `uv run pytest tests/eventbus -q` | Confirmed by repository evidence |
| REQ-003 | Required Changes 4; Constraints (503 semantics documented) | `docs/24_eventbus/eventbus_10_health_endpoint.md` | Step 4 | AC-4, AC-6 | `tools/check_docs_consistency.py --domain eventbus` | Explicit in issue |
| REQ-004 | Required Changes 5; deployment gate substring match | `deploy/setup_services.sh` | Step 3 | AC-5 | `tests/deploy/test_setup_services_eventbus.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes 5 | `tests/deploy/test_setup_services_eventbus.py` | Step 3 | AC-5 | `uv run pytest tests/deploy -q` | Confirmed by repository evidence |
| REQ-005 | Testing Expectations 1 and 2 | `tests/eventbus/test_eventbus_route_helpers_metrics.py` | Step 1 | AC-1, AC-2 | `uv run pytest tests/eventbus -q` | Explicit in issue |
| REQ-005 | Testing Expectations 2 | `tests/eventbus/test_eventbus_slow_consumer.py` | Step 1 | AC-3 | `uv run pytest tests/eventbus -q` | Explicit in issue |
| REQ-006 | Testing Expectations 2 and 3 | `tests/eventbus/test_eventbus_health.py` | Step 3 | AC-4 | `uv run pytest tests/eventbus -q` | Explicit in issue |
| REQ-006 | Testing Expectations 3 | `tests/deploy/test_setup_services_eventbus.py` | Step 3 | AC-5 | `uv run pytest tests/deploy -q` | Explicit in issue |
| REQ-007 | Documentation Impact; the doc names a metric that does not exist | `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Step 4 | AC-6 | `tools/check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-007 | Documentation Impact | `docs/24_eventbus/eventbus_10_health_endpoint.md` | Step 4 | AC-6 | `tools/check_docs_consistency.py --domain eventbus` | Explicit in issue |
