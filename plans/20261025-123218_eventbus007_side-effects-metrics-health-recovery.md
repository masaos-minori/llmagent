## Goal
Make the publish and requeue side effects observable and unambiguous, make health and metrics measure what their names claim, separate liveness/readiness/integrity, and provide a supported DLQ file reconciliation path — without changing the SQLite durability boundary or the requeue transaction (H-01).

## Priority
Medium

## Scope
- **In-Scope**:
  - Document (and, where useful, return in the response) that requeue is delivered through consumer replay rather than immediate broker push; record the owner decision on whether immediate broker notification on requeue is required.
  - Export the existing JSONL-append-failure and broker-notification-failure counters (and add a DLQ-file-write-failure counter) through a metrics exposition endpoint or equivalent, or document them as intentionally log-only.
  - Represent the slow-consumer figure as a gauge of the current count (or increment the cumulative counter only on state transitions); never mutate metrics from health reads.
  - Start the query-duration timer after the lock is acquired and measure thread-dispatch, lock-wait, DB-execution and total duration separately so the `lock_wait_high` and `query_duration_high` degraded reasons are independent measurements.
  - Define liveness, readiness and integrity checks separately; readiness must not imply schema integrity unless integrity is checked; keep existing health response fields backward compatible unless the owner agrees otherwise.
  - Add a DLQ reconciliation tool or deterministic recovery procedure for DLQ files missing or corrupted relative to `dlq_at` rows, and for orphan files.
  - Update the ops docs (`docs/24_eventbus/`) for requeue delivery semantics, metric definitions, health tiers and the DLQ recovery procedure.
- **Out-of-Scope**:
  - Changing the SQLite durability boundary (the write-file-then-set-`dlq_at` order in `dlq.py`).
  - The requeue transaction fix (memo H-01).
  - The startup schema-integrity gate (memo H-03 / `eventbus003`); coordinate the readiness definition so H-03 can rely on it.
  - The memo's `published_at` comment claim (not found in current source).
  - Lazy loading of the Step 0 mandatory-load set — no action required (fixed load absorbed by prompt cache, user decision 2026-10-24).
- **Dependencies**:
  - Related memo tasks H-01 (requeue transaction) and H-03 (integrity/startup gate). No open issue under `issues/` overlaps.
  - The readiness definition feeds H-03 (`eventbus003`); coordinate the response fields so H-03 can rely on them.
  - Owner decisions on the unknowns below gate implementation; they are recorded, not guessed.

## Background
Confirmed against HEAD (adversarial re-verification):
- The database health check is `SELECT 1` only (`check_db`, `scripts/eventbus/db_conn.py:52-58`); `/health` mixes liveness, readiness and capacity into one 200/503 status (`scripts/eventbus/health_route.py:25-110`).
- `Broker.slow_consumer_count()` (`scripts/eventbus/broker.py:127-136`) calls `_slow_consumer_total.inc(count)` on every call when `count > 0`; `health_check` calls it on every poll (`health_route.py:57`), so a read-only health request inflates the cumulative counter while a consumer stays slow.
- In `run_with_db_lock` (`scripts/eventbus/route_helpers.py:131-151`) the query-duration timer starts before the lock is acquired (`start_time` at line 137, `with get_db_lock()` at line 139), so `_db_query_duration` includes lock wait; the separately measured `lock_wait` (lines 145-148) includes thread dispatch and queuing. `lock_wait_high` and `query_duration_high` are therefore not independent measurements.
- JSONL-append and broker-notification failures are not log-only: `scripts/eventbus/publish_route.py` increments `_jsonl_append_failure_counter` (line 25) and `_broker_notify_failure_counter` (line 30) (prometheus counters). However no metrics exposition endpoint or exporter exists in `scripts/eventbus/` (no `/metrics`, no `generate_latest`, no `start_http_server`; grep confirms only `Counter` imports), and `/health` reports only the lock-contention counter, so the counters are in-process and not observable. No DLQ-file-write-failure counter exists.
- DLQ promotion writes the file first (`_atomic_write`, `dlq.py:108`) and then sets `dlq_at` in SQLite (`dlq.py:109-113`); a crash between the two leaves an orphan file with `dlq_at IS NULL`, which the next sweep re-promotes (self-heals). Unrecoverable cases are a file deleted or corrupted after promotion. A write failure inside `_shared_promote` propagates as `OSError` and aborts the rest of that sweep cycle (caught by `_dlq_loop`).
- `dlq_requeue` (`scripts/eventbus/dlq_route.py:49-99`) creates a new event row via the lineage model (`redeliver_event`) and does NOT call `broker.publish()`; requeue is delivered through consumer replay, not immediate broker push, and this is not stated to operators.
- The memo's `published_at` comment inaccuracy was not confirmed (no idempotency-equality comment next to `published_at` exists in `scripts/eventbus/`).
- `test_eventbus_slow_consumer.py::test_health_reports_slow_consumer_count` and `::test_health_503_when_slow_consumer_threshold_exceeded` poll `/health` repeatedly, exercising the counter inflation. `test_eventbus_route_helpers_metrics.py::test_query_duration_metric_observed` asserts the `_db_query_duration` histogram is still observed after any change.

## Problem
Requeue relies on consumer replay rather than live broker push, which is not stated for operators; side-effect failure counters exist but are not exported (in-process only, no exposition endpoint, no DLQ-file-write counter); a read-only health request mutates `_slow_consumer_total`; lock-wait and query-duration measurements overlap, producing misleading degraded reasons; the database health check does not distinguish liveness, readiness and integrity; and a DLQ file deleted or corrupted after promotion has no reconciliation path.

## Reason for Change
Liveness, readiness and integrity are different operational questions, SQLite/DLQ-file divergence needs a deterministic recovery path, and monitoring must detect side-effect failures without log scraping and survive repeated health polls without inflating cumulative counters.

## Implementation Intent
Keep the existing SQLite durability boundary unless an owner changes it. Document (and where useful return) that requeue is delivered through replay, expose side-effect failure metrics through a metrics exposition endpoint or equivalent (adding a DLQ file write-failure counter), represent the current slow-consumer count as a gauge or increment the counter only on state transitions, stop mutating metrics from health reads, separate thread-dispatch/lock-wait/DB-execution/total duration, define liveness/readiness/integrity checks, and add a DLQ reconciliation tool or deterministic recovery procedure.

## Requirements
- `REQ-001`: Requeue delivery MUST be unambiguous to operators: documented as replay-based, and returned in the requeue response where useful; the decision on whether immediate broker notification is required is an owner decision recorded as UNK-01. (Acceptance 1)
- `REQ-002`: The JSONL-append-failure and broker-notification-failure counters AND a new DLQ-file-write-failure counter MUST be observable outside the process log through a metrics exposition endpoint or equivalent, OR documented as intentionally log-only (UNK-02). (Acceptance 5)
- `REQ-003`: The slow-consumer figure MUST be a gauge of the current count, OR the cumulative counter MUST increment only on state transitions; metrics MUST NEVER be mutated from health reads. (Acceptance 2)
- `REQ-004`: The query-duration timer MUST start after the lock is acquired, and thread-dispatch, lock-wait, DB-execution and total duration MUST be measured separately so the `lock_wait_high` and `query_duration_high` degraded reasons are independent. (Acceptance 3)
- `REQ-005`: Liveness, readiness and integrity MUST be defined and reported separately; readiness MUST NOT imply schema integrity unless integrity is checked; existing health response fields consumed by monitors stay backward compatible unless the owner agrees otherwise. (Acceptance 3; Constraint)
- `REQ-006`: A supported reconciliation tool or deterministic recovery procedure MUST exist for DLQ files missing or corrupted relative to `dlq_at` rows and for orphan files. (Acceptance 4)
- `REQ-007`: Token values and secrets MUST stay out of metrics and audit records. (Constraint; INV-05)

## Implementation Target Files
**Freeze status**: Frozen (set once `issue-to-plan` Step 8's Implementation Target
Files Validation passed — `check_workitem_structure.py` reports No findings;
`check_plan_target_overlaps.py` reports 9 cross-plan overlaps, ALL between already
Frozen Plans (`plans/...002...`, `...004...`, `...005...`, `...006...`) on
`docs/10_adr/adr_02_04_006...`, `adr_02_04_013...`, `scripts/eventbus/ack_route.py`,
`scripts/eventbus/app.py`, `scripts/eventbus/auth.py` and three test files. None of the
9 findings involves this Issue 7 Plan. The shared files are edited additively and in
different regions: `app.py` — Issue 4 owns `lifespan()`/shutdown, Issue 6 owns startup
publish wiring, this Plan registers a conditional `/metrics` route (UNK-02); `auth.py`
and `adr_02_04_013...` are owned by Issues 2 and 6 only. Every row is `Verified`.

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/broker.py` | Make slow-consumer metric a gauge of current count, or increment `_slow_consumer_total` only on state transitions; keep `slow_consumer_count()` returning the current count without side effects | Removes cumulative-counter inflation from health reads (Acceptance 2) | REQ-003; Acceptance 2 | `slow_consumer_count()` broker.py:127-136 (`.inc(count)` at 134-136) | `tests/eventbus/test_eventbus_slow_consumer.py` | Verified |
| `scripts/eventbus/route_helpers.py` | Start `_db_query_duration` timer after the lock is acquired; add separate dispatch/lock-wait/execution/total timing; keep the three existing metrics names stable | Makes `lock_wait_high` and `query_duration_high` independent (Acceptance 3) | REQ-004; Acceptance 3 | `run_with_db_lock()` route_helpers.py:131-151 (timer at 137, lock at 139) | `tests/eventbus/test_eventbus_route_helpers_metrics.py` | Verified |
| `scripts/eventbus/health_route.py` | Separate liveness/readiness/integrity into distinct fields/reasons; report slow consumers as a gauge value; keep existing response fields backward compatible | Fixes mixed health status and overlapping degraded reasons (Acceptance 3, 5) | REQ-004, REQ-005; Acceptance 3, 5 | `health_check()` health_route.py:25-110; capacity reasons 80-88 | `tests/eventbus/test_eventbus_health.py` | Verified |
| `scripts/eventbus/publish_route.py` | Add a DLQ-file-write-failure counter is out of scope here (that lives in `dlq.py`); confirm the two existing counters are the ones exported | Side-effect failure counters to export (Acceptance 5) | REQ-002; Acceptance 5 | `_jsonl_append_failure_counter`/`_broker_notify_failure_counter` publish_route.py:25-33 | `tests/eventbus/test_eventbus_publish.py` (if present) | Verified |
| `scripts/eventbus/dlq.py` | Add a DLQ-file-write-failure counter around `_atomic_write` (write failure after commit is a side-effect failure); preserve the write-file-then-set-`dlq_at` durability order | New observable counter for the previously silent write-failure path | REQ-002; Acceptance 5 | `_atomic_write()` dlq.py:194-209; promotion write-then-update dlq.py:108-113 | `tests/eventbus/test_eventbus_dlq.py` | Verified |
| `scripts/eventbus/dlq_route.py` | Return requeue delivery semantics in the response (replay-based) per UNK-01; record owner decision on immediate broker notification | Makes requeue delivery unambiguous (Acceptance 1) | REQ-001; Acceptance 1 | `dlq_requeue()` dlq_route.py:49-99 (no `broker.publish()`) | `tests/eventbus/test_eventbus_dlq.py` | Verified |
| `scripts/eventbus/app.py` | Register the metrics exposition route (if a `/metrics` endpoint is adopted, UNK-02) under the loopback + auth model; no change if counters are documented as log-only | Host the exposition endpoint and apply the existing auth/loopback contract | REQ-002; Acceptance 5 | route registration app.py:163-281 (`/health` at 163) | `tests/eventbus/test_eventbus_app_isolation.py` | Verified |
| `tests/eventbus/test_eventbus_slow_consumer.py` | Assert the gauge reflects the current count and that repeated `/health` polls do not inflate a cumulative counter | Covers Acceptance 2 | REQ-003; Acceptance 2 | `test_health_reports_slow_consumer_count` test_eventbus_slow_consumer.py:70 | this file | Verified |
| `tests/eventbus/test_eventbus_route_helpers_metrics.py` | Keep `_db_query_duration` observed after the timer fix; assert execution time excludes lock wait | Preserves the existing metric contract | REQ-004; Acceptance 3 | `test_query_duration_metric_observed` test_eventbus_route_helpers_metrics.py:104 | this file | Verified |
| `tests/eventbus/test_eventbus_health.py` | Assert liveness/readiness/integrity are reported separately; existing fields remain present/backward compatible; slow-consumer gauge behavior | Covers Acceptance 3, 5 | REQ-005; Acceptance 3, 5 | `TestHealth` test_eventbus_health.py:88-212 | this file | Verified |
| `tests/eventbus/test_eventbus_dlq.py` | Cover the DLQ-file-write-failure counter and the reconciliation path (missing/orphan/corrupt files) | Covers Acceptance 4, 5 | REQ-002, REQ-006; Acceptance 4, 5 | `_shared_promote` write-then-update dlq.py:108-113 | this file | Verified |
| `docs/24_eventbus/eventbus_09_publish_durability.md` | Document requeue delivery semantics (replay vs immediate push) and the side-effect failure metrics | Canonical ops contract for publish/requeue | REQ-001, REQ-002; Acceptance 1, 5 | eventbus_09 publish durability | N/A | Verified |
| `docs/24_eventbus/eventbus_10_health_endpoint.md` | Document the liveness/readiness/integrity tiers, the metric definitions, and the corrected degraded-reason semantics | Canonical ops contract for health | REQ-003, REQ-004, REQ-005; Acceptance 3, 5 | eventbus_10 health endpoint | N/A | Verified |
| `docs/24_eventbus/eventbus_03_dlq_operations.md` | Document the DLQ reconciliation tool/procedure and the orphan/self-heal behavior | Canonical ops contract for DLQ recovery | REQ-006; Acceptance 4 | eventbus_03 DLQ operations | N/A | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/db.py` | Facade re-exports (`check_db`, `get_db_lock`, `redeliver_event`); needed to know the public surface the metrics/health/DLQ changes import | `scripts/eventbus/health_route.py`, `scripts/eventbus/dlq_route.py`; REQ-004, REQ-006 |
| `scripts/eventbus/dlq_repo.py` | `sweep_orphans`/sweep orchestration used by `_dlq_loop`; preserve sweep behavior when adding the write-failure counter | `scripts/eventbus/dlq.py`; REQ-002 |
| `scripts/eventbus/config.py` | `EventBusConfig` health thresholds and slow-consumer threshold consumed by health/broker | `scripts/eventbus/health_route.py`, `scripts/eventbus/broker.py`; REQ-003 |
| `scripts/eventbus/audit.py` | `log_privileged_action` convention reused for the requeue response/audit; INV-05 no-secret rule | `scripts/eventbus/dlq_route.py`; REQ-001, REQ-007 |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Replay-delivery semantics the requeue response must match | `scripts/eventbus/dlq_route.py`; REQ-001 |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | EVENTBUS tracking (Part 1); confirms scope and that deploy/readiness gaps are separate | `docs/24_eventbus/eventbus_10_health_endpoint.md`; Scope |

## Acceptance Criteria
- Requeue delivery timing is unambiguous (replay-based, stated in the response and docs) (REQ-001; Acceptance 1).
- Monitoring detects side-effect failures without log scraping alone, and repeated health polls do not inflate cumulative counters (REQ-002, REQ-003; Acceptance 2, 5).
- Lock and query degraded reasons use distinct measurements; readiness does not imply schema integrity unless integrity is checked; existing monitor-consumed fields stay backward compatible (REQ-004, REQ-005; Acceptance 3).
- Missing and orphaned DLQ files have a supported recovery path (REQ-006; Acceptance 4).
- Side-effect failure counters (JSONL, broker, DLQ file) are observable outside the process log, or are documented as intentionally log-only (REQ-002; Acceptance 5).

## Tests
- Slow consumer enters, remains, recovers and re-enters: the gauge reflects the current count and repeated `/health` polls do not increment a cumulative counter. (REQ-003; Acceptance 2)
- `run_with_db_lock` with a short query and with contention: execution time is measured only while holding the lock; lock-wait and dispatch are separate; `lock_wait_high` and `query_duration_high` are independent. (REQ-004; Acceptance 3)
- Health tiers: liveness, readiness and integrity are reported separately; readiness without integrity does not claim schema OK; existing fields remain present. (REQ-005; Acceptance 3, 5)
- JSONL append failure after commit; broker notification failure after commit; the counters are exported and increment. (REQ-002; Acceptance 5)
- DLQ file write failure (disk-full / permission fault injection): the new counter increments and the DB row is not promoted. (REQ-002; Acceptance 5)
- Missing and orphaned DLQ files: the reconciliation tool/procedure reconciles them deterministically. (REQ-006; Acceptance 4)
- Requeue followed by reconnect and replay; the response states replay-based delivery. (REQ-001; Acceptance 1)
- Then ruff and mypy.

## Documentation Impact
Yes. Requeue delivery semantics, metric definitions, health tiers and the DLQ recovery procedure must be documented. Target docs named via `docs/00_index.md` / `routing.md` Docs mapping:
- `docs/24_eventbus/eventbus_09_publish_durability.md` — requeue delivery semantics (replay vs immediate push) + side-effect failure metrics. Drives REQ-001, REQ-002.
- `docs/24_eventbus/eventbus_10_health_endpoint.md` — liveness/readiness/integrity tiers, metric definitions, corrected degraded-reason semantics. Drives REQ-003, REQ-004, REQ-005.
- `docs/24_eventbus/eventbus_03_dlq_operations.md` — DLQ reconciliation tool/procedure + orphan/self-heal behavior. Drives REQ-006.
No deployment-script documentation is in scope.

## Assumptions
- A metrics exposition route can reuse the existing loopback + bearer-auth model applied to other routes; where it is added it inherits that contract.
- The three existing metric names (`eventbus_db_lock_wait_time_seconds`, `eventbus_db_query_duration_seconds`, `eventbus_db_lock_contention_total`) are consumed by monitors and must stay stable; new timing is additive.
- Existing `/health` response fields (`status`, `db`, `dlq_task`, `active_subscribers`, `max_queue_depth`, `slow_consumers`, `overflow_disconnects`, `duplicate_connection_rejections`, `degraded_reasons`, `metrics`) are consumed by monitors and must remain present unless the owner agrees otherwise.
- The DLQ reconciliation target is a CLI entry point under `scripts/eventbus/` or a documented deterministic procedure, not a new HTTP route (to avoid expanding the auth surface).
- `deploy.sh` rsyncs `scripts/` and `docs/` wholesale to `/opt/llm/`, so every target row's `deploy.sh Impact` is "not applicable (rsynced)".

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Is immediate broker notification on requeue required? Today requeue is replay-only (no `broker.publish()`). What should the default be, and what should the response state? | Owner availability; no client in repo to constrain | Owner decision; documented in `eventbus_09`; non-blocking sign-off gate before implementation (per `rules/coding.md` Explicit sign-off gates) | True |
| UNK-02 | Is a metrics exposition endpoint wanted at all? The counters exist today but nothing scrapes them. If yes, where is the route and how does the loopback/auth model apply? | Owner availability; no existing endpoint to mirror | Owner decision; add `/metrics` under the existing auth/loopback model, or document counters as intentionally log-only; non-blocking sign-off gate | True |
| UNK-03 | How exactly to separate liveness/readiness/integrity while keeping existing monitor-consumed fields backward compatible? What is the new field shape vs the deprecated single-status shape? | No existing tiered schema; monitor contract not reviewed | Engineering + owner decision; documented in `eventbus_10`; keep existing fields additive | False |
| UNK-04 | Tool versus procedure for DLQ reconciliation: a CLI entry point under `scripts/eventbus/` versus a documented manual procedure? | Trade-off between automation and surface area; no existing DLQ CLI in repo | Engineering decision; recorded in design; drives a new `scripts/eventbus/` file or doc only | False |
| UNK-05 | For the slow-consumer metric, gauge-of-current-count versus transition-only counter? And should the current count be exposed as a separate gauge regardless? | Product preference for alerting on level versus rate | Owner/engineering decision; recorded in design; drives `broker.py` change | False |
| UNK-06 | The memo's `published_at` comment claim and the exact DLQ divergence scenarios beyond file deletion/corruption were not confirmed; which, if any, are in scope? | Not confirmed in current source | Verify before implementing; likely out of scope (recorded) | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/broker.py` | Slow-consumer gauge / transition-only counter | Every `/health` poll + slow-consumer tests | 0 (last change 2026-09-15) | N/A (git-fame unavailable) | not applicable (rsynced) |
| `scripts/eventbus/route_helpers.py` | `run_with_db_lock` timing split | All DB-bound routes (every route uses it) | 0 (last change 2026-09-15) | N/A | not applicable (rsynced) |
| `scripts/eventbus/health_route.py` | Tiered liveness/readiness/integrity; gauge value | `/health` consumers (monitors) | 0 (last change 2026-09-15) | N/A | not applicable (rsynced) |
| `scripts/eventbus/dlq.py` | DLQ-file-write-failure counter | DLQ promotion path (sweep + inline) | 8 (last change 2026-10-23) | N/A | not applicable (rsynced) |
| `scripts/eventbus/publish_route.py` | (export only; no counter added here) | Publish path | 0 (last change 2026-09-18) | N/A | not applicable (rsynced) |
| `scripts/eventbus/dlq_route.py` | Requeue response delivery semantics | `/dlq/requeue` callers | 0 (last change 2026-09-16) | N/A | not applicable (rsynced) |
| `scripts/eventbus/app.py` | Register `/metrics` route (if adopted, UNK-02) | FastAPI route table | 6 (last change 2026-10-22) | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_slow_consumer.py` | Gauge + no-inflation assertions | Test-only | 0 | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_route_helpers_metrics.py` | Timing-split assertions | Test-only | 0 | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_health.py` | Tiered-health assertions | Test-only | 0 | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_dlq.py` | Write-failure counter + reconciliation | Test-only | 0 | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_09_publish_durability.md` | Requeue delivery + metrics doc | Doc-only | 0 | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_10_health_endpoint.md` | Health-tier + metric doc | Doc-only | 0 | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_03_dlq_operations.md` | DLQ reconciliation doc | Doc-only | 0 | N/A | not applicable (rsynced) |

Baseline complexity (radon): `health_check` = C (15); `publish` = B (7); `run_with_db_lock` = M (low); `dlq_requeue` = A (4); `slow_consumer_count` = M (low).
bandit and vulture are clean on all target files. `health_check` at C(15) is already
above maintainability comfort; the tier refactor should keep `health_route.py` at or
below its current grade by extracting per-tier check helpers.

## Design
**North star (REQ-005):** liveness, readiness and integrity are three distinct
operational questions, and each health signal measures exactly one of them. Every
candidate mechanism below serves that separation; backward compatibility with existing
monitor-consumed fields is preserved unless the owner changes it.

**Slow-consumer metric (UNK-03/UNK-05) — recommended: gauge of current count.**
- Replace the cumulative `_slow_consumer_total.inc(count)` side effect with a gauge
  `eventbus_slow_consumer_current` reflecting the current slow-subscriber count, and make
  `slow_consumer_count()` a pure read (no metric mutation). This removes the inflation
  from health reads (REQ-003) and gives alerting a level to fire on rather than a rate.
- Alternative (recorded, not prescribed): keep the counter but increment only on state
  transitions (0→N or N→0, or when the count crosses the threshold), so repeated polls do
  not inflate it. Adopt only if the owner explicitly wants a rate metric.
- Either way `slow_consumer_count()` returns the current count unchanged for callers.

**Timing split (REQ-004).** In `run_with_db_lock()`, measure four durations: (a) total
wall time from submit to completion, (b) thread-dispatch time (submit → lock acquire
start), (c) lock-wait time (lock acquire start → lock held), (d) DB-execution time (while
holding the lock, i.e. the current `_db_query_duration` body moved inside the `with`).
Keep the three existing metric names stable and additive; the degraded-reason thresholds
(`lock_wait_avg > 0.01`, `query_dur_avg > 0.05`) now compare independent measurements.
Extract a small `_DbTiming` helper to keep `run_with_db_lock` complexity low.

**Health tiers (UNK-03).** Define: liveness = process/endpoint reachable (broker task
running, app responds); readiness = dependencies healthy enough to accept work (DB
connectable via `check_db`); integrity = schema matches expected version (feeds H-03, not
implemented here). Report each as a distinct field (`liveness`, `readiness`, `integrity`)
and derive `status`/`degraded_reasons` backward-compatibly: keep the existing fields and
reason strings, add the tier fields, and make readiness degrade without claiming integrity
unless integrity is checked. Coordinate with H-03 so the readiness field can rely on the
integrity check once H-03 adds it.

**Metrics exposition (UNK-02).** Two branches (owner decision): (a) add a `/metrics`
route registering the default registry via `generate_latest`, under the existing loopback +
bearer-auth model; (b) document the counters as intentionally log-only and stop short of an
endpoint. If (a), the new DLQ-file-write-failure counter and the two existing side-effect
counters are exported automatically with the rest of the default registry.

**DLQ-file-write-failure counter (REQ-002).** Wrap `_atomic_write()` in `dlq.py` so a
write failure after the DB commit path is counted (`eventbus_dlq_file_write_failure_total`),
mirroring the JSONL/broker counters, without changing the write-file-then-set-`dlq_at`
durability order.

**Reconciliation (UNK-04).** Add a deterministic reconciliation entry point (CLI under
`scripts/eventbus/`, e.g. `reconcile_dlq.py`) OR a documented procedure that: lists
`dlq_at IS NULL` events whose `{event_id}.json` exists (orphan → promote or delete per
policy), lists `{event_id}.json` files whose `dlq_at` row is missing (missing file →
rebuild row or quarantine), and reports corruption (unparseable JSON) for manual review.
Preserve the existing self-heal sweep; the tool is the deterministic path for the cases the
sweep cannot self-heal (file deleted/corrupted after promotion).

**Import-linter:** `eventbus-is-isolated` is KEPT (verified above). No file crosses into
`shared/`; a new reconciliation CLI stays within `scripts/eventbus/`.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Slow-consumer metric (broker.py)**
   - [ ] Make `slow_consumer_count()` a pure read in `scripts/eventbus/broker.py`; replace `_slow_consumer_total` with a gauge of the current count (or gate increments on state transitions per UNK-05). (REQ-003; `scripts/eventbus/broker.py`)
2. **Phase 2: Timing split (route_helpers.py)**
   - [ ] Extract a `_DbTiming` helper and split `run_with_db_lock()` into dispatch/lock-wait/execution/total; move `_db_query_duration.observe` inside the lock in `scripts/eventbus/route_helpers.py`. (REQ-004; `scripts/eventbus/route_helpers.py`)
3. **Phase 3: Health tiers (health_route.py)**
   - [ ] Separate liveness/readiness/integrity into distinct fields and reasons while keeping existing monitor-consumed fields present; report slow consumers as a gauge value in `scripts/eventbus/health_route.py`. (REQ-005; `scripts/eventbus/health_route.py`)
4. **Phase 4: Side-effect counters (dlq.py, publish_route.py)**
   - [ ] Add the DLQ-file-write-failure counter around `_atomic_write()` in `scripts/eventbus/dlq.py` without changing the durability order. (REQ-002; `scripts/eventbus/dlq.py`)
   - [ ] Confirm the two existing counters in `scripts/eventbus/publish_route.py` are the exported set (no change unless UNK-02 requires a new one). (REQ-002; `scripts/eventbus/publish_route.py`)
5. **Phase 5: Metrics exposition (app.py) — only if UNK-02 adopts an endpoint**
   - [ ] Register the `/metrics` route under the loopback + auth model in `scripts/eventbus/app.py`. (REQ-002; `scripts/eventbus/app.py`)
6. **Phase 6: Requeue delivery semantics (dlq_route.py)**
   - [ ] State replay-based delivery in the `dlq_requeue` response per UNK-01 in `scripts/eventbus/dlq_route.py`. (REQ-001; `scripts/eventbus/dlq_route.py`)
7. **Phase 7: DLQ reconciliation (new tool or procedure)**
   - [ ] Add the reconciliation entry point or documented procedure for missing/orphan/corrupt DLQ files (`scripts/eventbus/` or docs) per UNK-04. (REQ-006; `scripts/eventbus/dlq.py` context)
8. **Phase 8: Tests**
   - [ ] Update `tests/eventbus/test_eventbus_slow_consumer.py`, `test_eventbus_route_helpers_metrics.py`, `test_eventbus_health.py`, `test_eventbus_dlq.py` for the above. (Acceptance 1-5)
9. **Phase 9: Documentation**
   - [ ] Document requeue delivery + metrics (`eventbus_09`), health tiers + metrics (`eventbus_10`), DLQ reconciliation (`eventbus_03`). (REQ-001, REQ-002, REQ-006)
10. **Phase 10: Validation**
    - [ ] Run ruff, mypy, bandit, vulture, lint-imports, and the affected test files; confirm no counter inflation, independent degraded reasons, tiered health, and reconciliation works. (Acceptance 1-5)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/broker.py` | Unit: repeated `slow_consumer_count()` does not inflate; gauge reflects current count | `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py` | Gauge = current count; no cumulative inflation from polls |
| `scripts/eventbus/route_helpers.py` | Unit: execution time excludes lock wait; dispatch/lock-wait separate | `uv run pytest tests/eventbus/test_eventbus_route_helpers_metrics.py` | `_db_query_duration` observed while holding lock; independent timings |
| `scripts/eventbus/health_route.py` | Integration: tiered fields present; existing fields backward compatible | `uv run pytest tests/eventbus/test_eventbus_health.py` | liveness/readiness/integrity separate; existing fields present |
| `scripts/eventbus/dlq.py` | Fault injection: disk-full/permission write failure increments counter; row not promoted; reconciliation fixes missing/orphan | `uv run pytest tests/eventbus/test_eventbus_dlq.py` | Write-failure counter increments; reconciliation deterministic |
| `scripts/eventbus/dlq_route.py` | Integration: requeue response states replay-based delivery | `uv run pytest tests/eventbus/test_eventbus_dlq.py` | Response states replay delivery |
| `scripts/eventbus/*` | Static: complexity, dead code, security | `uv run radon cc scripts/eventbus/health_route.py scripts/eventbus/route_helpers.py`; `uv run vulture scripts/eventbus/`; `uv run bandit scripts/eventbus/ -c pyproject.toml` | `health_check` ≤ C(15); bandit/vulture clean |
| Import boundaries | Architecture contract | `PYTHONPATH=scripts uv run lint-imports` | `eventbus-is-isolated` KEPT |
| Types / format | Quality gates | `uv run mypy`, `uv run ruff` | Pass |

## Risks
- **Risk**: `health_check` is already C(15); the tier refactor could raise complexity past maintainability limits. → **Mitigation**: extract per-tier check helpers; keep `health_route.py` at or below C(15).
- **Risk**: Changing the slow-consumer metric from a counter to a gauge breaks monitors expecting a `_total` series. → **Mitigation**: record the change in `eventbus_10`; keep the current count available as a gauge and document the alerting change; owner sign-off (UNK-03/UNK-05).
- **Risk**: The timing split changes what `_db_query_duration` measures, which `test_eventbus_route_helpers_metrics.py` asserts. → **Mitigation**: keep the histogram name and observation (now inside the lock); update the test to assert execution-excludes-lock-wait.
- **Risk**: Adding a `/metrics` route expands the auth/loopback surface (UNK-02). → **Mitigation**: adopt only with owner sign-off; reuse the existing loopback + bearer-auth model; otherwise document counters as log-only.
- **Risk**: The reconciliation tool adds a new entry point and surface. → **Mitigation**: prefer a CLI under `scripts/eventbus/` or a documented procedure over an HTTP route (UNK-04).
- **Risk**: Backward-incompatible `/health` shape breaks monitors. → **Mitigation**: keep existing fields additive; new tier fields are additions, not replacements (Constraint; REQ-005).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: slow-consumer gauge in `broker.py` | Pending | — | — | Sign-off gate on UNK-03/UNK-05 |
| 2 | Phase 2: timing split in `route_helpers.py` | Pending | — | — | |
| 3 | Phase 3: health tiers in `health_route.py` | Pending | — | — | Sign-off gate on UNK-03 (shape) |
| 4 | Phase 4: side-effect counters in `dlq.py`/`publish_route.py` | Pending | — | — | |
| 5 | Phase 5: `/metrics` route in `app.py` (only if UNK-02 adopts endpoint) | Pending | — | — | Sign-off gate on UNK-02 |
| 6 | Phase 6: requeue delivery semantics in `dlq_route.py` | Pending | — | — | Sign-off gate on UNK-01 |
| 7 | Phase 7: DLQ reconciliation tool/procedure | Pending | — | — | UNK-04 |
| 8 | Phase 8: tests | Pending | — | — | |
| 9 | Phase 9: docs (`eventbus_09`/`10`/`03`) | Pending | — | — | |
| 10 | Phase 10: ruff/mypy/bandit/vulture/lint-imports + affected test runs | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1, 5, 6 | UNK-02 (metrics endpoint), UNK-01 (requeue notification), UNK-03/05 (slow-consumer metric) are owner decisions (sign-off gates) | — | — |
| 3 | UNK-03: health-tier field shape is an owner/engineering decision | — | — |
| 7 | UNK-04: reconciliation tool vs procedure is an engineering decision | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261023-154326_eventbus007_side-effects-metrics-health-recovery.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261025-123218
- **Related target files**: `scripts/eventbus/publish_route.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/dlq.py`, `scripts/eventbus/broker.py`, `scripts/eventbus/route_helpers.py`, `scripts/eventbus/health_route.py`, `scripts/eventbus/db_conn.py`, `scripts/eventbus/app.py`, `tests/eventbus/test_eventbus_health.py`, `tests/eventbus/test_eventbus_route_helpers_metrics.py`, `tests/eventbus/test_eventbus_slow_consumer.py`, `tests/eventbus/test_eventbus_dlq.py`, `docs/24_eventbus/eventbus_09_publish_durability.md`, `docs/24_eventbus/eventbus_10_health_endpoint.md`, `docs/24_eventbus/eventbus_03_dlq_operations.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required change 1; Acceptance 1 | `scripts/eventbus/dlq_route.py`, `docs/24_eventbus/eventbus_09_publish_durability.md` | 6 | Requeue delivery stated (replay) | Requeue-response test | Draft |
| REQ-002 | Required change 2; Acceptance 5 | `scripts/eventbus/dlq.py`, `scripts/eventbus/publish_route.py`, `scripts/eventbus/app.py` (conditional) | 4, 5 | Side-effect counters exported incl. DLQ write failure | Write-failure-counter test | Draft |
| REQ-003 | Required change 3; Acceptance 2 | `scripts/eventbus/broker.py`, `tests/eventbus/test_eventbus_slow_consumer.py` | 1 | No metric mutation from health reads; gauge of current | Slow-consumer gauge test | Draft |
| REQ-004 | Required change 4; Acceptance 3 | `scripts/eventbus/route_helpers.py`, `tests/eventbus/test_eventbus_route_helpers_metrics.py` | 2 | Independent lock-wait/query timings | Timing-split test | Draft |
| REQ-005 | Required change 5; Acceptance 3; Constraint | `scripts/eventbus/health_route.py`, `tests/eventbus/test_eventbus_health.py` | 3 | Tiered health; backward-compatible fields | Tiered-health test | Draft |
| REQ-006 | Required change 6; Acceptance 4 | `scripts/eventbus/dlq.py`, `tests/eventbus/test_eventbus_dlq.py`, `docs/24_eventbus/eventbus_03_dlq_operations.md` | 7 | Missing/orphan/corrupt files reconciled | Reconciliation test | Draft |
| REQ-007 | Constraint; INV-05 | `scripts/eventbus/dlq.py`, `scripts/eventbus/dlq_route.py` | 4, 6 | Secrets out of metrics/audit | Audit/redaction review | Draft |
