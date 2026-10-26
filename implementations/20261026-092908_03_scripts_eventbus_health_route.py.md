## Goal

Separate liveness, readiness and integrity into distinct fields/reasons in
`scripts/eventbus/health_route.py` so each health signal measures exactly one question, report
the slow-consumer figure as a gauge value, and keep every existing monitor-consumed field
backward compatible (REQ-005; Acceptance 3, 5).

## Scope

- Modify only `scripts/eventbus/health_route.py`: `health_check()` (current lines 25-110).

## Assumptions

- Existing `/health` response fields (`status`, `db`, `dlq_task`, `active_subscribers`,
  `max_queue_depth`, `slow_consumers`, `overflow_disconnects`,
  `duplicate_connection_rejections`, `degraded_reasons`, `metrics`) are consumed by monitors
  and must remain present unless the owner agrees otherwise.
- Integrity (schema-version match) feeds `eventbus003` (H-03) and is NOT implemented here;
  readiness must not claim schema integrity unless integrity is checked.
- The tier shape (new field names vs the deprecated single-status shape) is an
  owner/engineering decision (UNK-03) recorded before this row executes.

## Design decisions

- **Three tier fields.** Add distinct `liveness`, `readiness` and `integrity` fields and derive
  them from the existing checks: liveness = broker task running + app responds; readiness = DB
  connectable via `check_db`; integrity = schema matches expected version (deferred to H-03).
  Keep all existing fields and reason strings; add the tier fields as additions, not
  replacements (REQ-005; Acceptance 3, 5).
- **Backward-compatible derivation.** `status`/`degraded_reasons` are computed as today;
  readiness degrades without claiming integrity unless integrity is checked. Coordinate with
  H-03 so the readiness field can rely on the integrity check once H-03 adds it.
- **Gauge value.** Report `slow_consumers` as the current gauge value (from seq 1), not a
  cumulative count.

## Alternatives considered

- Replacing the single `status` field with a tiered object: rejected — it breaks monitor
  backward compatibility (Risk in the plan); the plan keeps existing fields additive.

## Implementation

### Target file

`scripts/eventbus/health_route.py`

### Procedure

1. In `health_check()` (lines 25-110), after computing `db_ok`/`db_status` and the broker
   metrics, derive three tier booleans: `liveness` (dlq task running and app reachable),
   `readiness` (`db_ok` via `check_db`), and `integrity` (`N/A: not checked here; report as
   null/absent rather than true).
2. Add `liveness`, `readiness` and `integrity` to the returned `JSONResponse` content alongside
   the existing fields; do not remove or rename any existing field.
3. Ensure `degraded_reasons` still includes the existing reasons (`db_unavailable`,
   `dlq_task_stopped`, `broker_queue_backlog_high`, `slow_consumers_detected`,
   `broker_unavailable`, `subscribers_at_capacity`, `lock_wait_high`, `query_duration_high`)
   unchanged.
4. Make `status`/`status_code` derive from liveness and readiness (not integrity) so readiness
   without integrity does not claim schema OK.

### Method

Additive edits to `health_check()`; extract per-tier check helpers (e.g. `_check_liveness` (new),
`_check_readiness` (new)) to keep `health_check` at or below C(15).

### Details

- `integrity` should be reported as absent/null (not `true`) since schema integrity is checked
  by H-03, not here.
- Keep `slow_consumers` as the current-count gauge value (relies on seq 1 making
  `slow_consumer_count()` a pure read).

## Compatibility considerations

- New tier fields are additive; existing monitor-consumed fields stay present and unchanged.
  Document the new fields in `docs/24_eventbus/eventbus_10_health_endpoint.md` (seq 13).
- The slow-consumer series changes from a cumulative counter to a gauge (seq 1); document in
  the same doc.

## Security considerations

- N/A: observability/shape change only; no secrets or token handling (INV-05 satisfied).

## Rollback considerations

- Revert the commit; the previous single-status response is restored.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_health.py` — assert liveness/readiness/integrity
  are reported separately, readiness without integrity does not claim schema OK, existing
  fields remain present, and slow_consumers reflects the gauge value.
- `uv run pytest tests/eventbus/` — full EventBus suite passes.
- `uv run radon cc scripts/eventbus/health_route.py`; keep `health_check` at or below C(15) by
  extracting per-tier helpers.
- `uv run vulture`, `uv run bandit scripts/eventbus/ -c pyproject.toml`.
- `uv run mypy`, `uv run ruff` on the file.

## Completion criteria

- `/health` reports liveness, readiness and integrity as distinct fields; existing
  monitor-consumed fields remain present; readiness does not imply schema integrity.

## Out of Scope

- Implementing schema-integrity checking (H-03 / eventbus003).
- Removing or renaming any existing `/health` field.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Separate liveness/readiness/integrity into distinct fields; report slow consumers as gauge | Pending | — | — | UNK-03 tier-shape is an owner/engineering decision |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-03: health-tier field shape is an owner/engineering decision | Classified non-blocking 2026-10-25; concrete shape still needed | Yes | 20261025 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/done/20261023-154326_eventbus007_side-effects-metrics-health-recovery.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123218_eventbus007_side-effects-metrics-health-recovery.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-092908
- **Related target files**: `scripts/eventbus/health_route.py`
