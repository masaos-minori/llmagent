## Goal

Update `tests/eventbus/test_eventbus_health.py` to assert liveness/readiness/integrity are
reported separately, existing fields remain present/backward compatible, and the
slow-consumer figure behaves as a gauge (REQ-005; Acceptance 3, 5).

## Scope

- Modify only `tests/eventbus/test_eventbus_health.py`, covering `TestHealth` (lines 88-212).

## Assumptions

- Existing `/health` response fields (`status`, `db`, `dlq_task`, `active_subscribers`, etc.)
  are consumed by monitors and must remain present.
- Integrity is not checked here (H-03); readiness without integrity must not claim schema OK.

## Design decisions

- **Tiered health.** Assert the new `liveness`/`readiness`/`integrity` fields are present and
  distinct; assert readiness without integrity does not claim schema OK; assert existing fields
  remain present (REQ-005; Acceptance 3, 5).
- **Gauge behavior.** Assert `slow_consumers` reflects the current-count gauge (relies on seq 1).

## Alternatives considered

- Asserting a single `status` field only: rejected — the plan requires tiered reporting.

## Implementation

### Target file

`tests/eventbus/test_eventbus_health.py`

### Procedure

1. In `TestHealth` (lines 88-212), assert the response contains distinct `liveness`,
   `readiness` and `integrity` fields and that they can differ (e.g. ready but not intant).
2. Assert every existing field (`status`, `db`, `dlq_task`, `active_subscribers`,
   `max_queue_depth`, `slow_consumers`, `degraded_reasons`, `metrics`) remains present.
3. Add a case where readiness fails without integrity being checked, asserting integrity is not
   reported as OK.

### Method

Add assertions to `TestHealth`; preserve existing cases.

## Compatibility considerations

- Test-only change; no runtime impact.

## Security considerations

- N/A.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_health.py` — tiered fields present; existing
  fields present; slow-consumer gauge behavior.
- `uv run pytest tests/eventbus/` — full EventBus suite passes.
- `uv run mypy`, `uv run ruff` on the file.

## Completion criteria

- The test asserts liveness/readiness/integrity are reported separately and existing fields
  remain backward compatible.

## Out of Scope

- The health-tier implementation (health_route.py, seq 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Assert tiered health reporting + backward-compatible fields | Pending | — | — | UNK-03 tier-shape gates exact field names |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-03 (tier shape) recorded; field names needed before execution | Classified non-blocking 2026-10-25 | Yes | 20261025 |

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
- **Related target files**: `tests/eventbus/test_eventbus_health.py`
