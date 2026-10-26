## Goal

Document the liveness/readiness/integrity tiers, the metric definitions, and the corrected
degraded-reason semantics in `docs/24_eventbus/eventbus_10_health_endpoint.md` (REQ-003,
REQ-004, REQ-005; Acceptance 3, 5).

## Scope

- Modify only `docs/24_eventbus/eventbus_10_health_endpoint.md`.

## Assumptions

- Existing `/health` response fields (`status`, `db`, `dlq_task`, `active_subscribers`,
  `max_queue_depth`, `slow_consumers`, `degraded_reasons`, `metrics`) are consumed by monitors
  and remain present.
- Integrity (schema-version match) is checked by `eventbus003` (H-03), not here; readiness
  must not claim schema integrity unless integrity is checked.
- The tier field shape is an owner/engineering decision (UNK-03), recorded before writing.
- `eventbus_slow_consumer_current` is introduced by an earlier-seq procedure in this Plan
  (`scripts/eventbus/broker.py`, seq 01); this doc records its exposition, not its creation.
  (case-2 cross-reference)

## Design decisions

- **Tier section.** Document liveness = process/endpoint reachable, readiness = dependencies
  healthy enough to accept work (DB connectable via `check_db`), integrity = schema matches
  expected version (deferred to H-03). State each as a distinct field and how `status`/
  `degraded_reasons` derive backward-compatibly.
- **Metric definitions.** Document the timing metrics (`eventbus_db_lock_wait_time_seconds`,
  `eventbus_db_query_duration_seconds`, `eventbus_db_lock_contention_total`) with the
  corrected semantics: `_db_query_duration` measures DB-execution while holding the lock
  (excludes lock wait), and `lock_wait_high`/`query_duration_high` are independent. Note the
  slow-consumer series is now a gauge of current count (`eventbus_slow_consumer_current`).

## Alternatives considered

- Collapsing tiers into the single `status` field: rejected — the plan requires distinct
  operational questions (UNK-03).

## Implementation

### Target file

`docs/24_eventbus/eventbus_10_health_endpoint.md`

### Procedure

1. Add a "Health Tiers" subsection defining liveness, readiness and integrity and how they map
   to the response fields; state that readiness without integrity does not claim schema OK.
2. Update the metric definitions to reflect the corrected degraded-reason semantics (independent
   lock-wait vs query-duration measurements) and the slow-consumer gauge.

### Method

Additive prose sections; preserve existing verified content.

## Compatibility considerations

- Docs-only; update Migration Notes per `skills/DESIGN.md` if referenced elsewhere.

## Security considerations

- N/A.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain eventbus` — pass.
- Confirm the tier/metric claims match `scripts/eventbus/health_route.py` and `route_helpers.py`.

## Completion criteria

- The doc defines the three health tiers, documents the metric definitions with corrected
  degraded-reason semantics, and preserves backward-compatibility notes.

## Out of Scope

- Implementing schema-integrity checking (H-03 / eventbus003).
- Changing the `/health` response shape (health_route.py, seq 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Document health tiers + metric definitions | Pending | — | — | UNK-03 tier-shape gates the recorded field names |
| 2 | Run the documentation checkers (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-03 (tier shape) recorded; field names needed before writing | Classified non-blocking 2026-10-25 | Yes | 20261025 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003`, `REQ-004`, `REQ-005`
- **Source issue**: `issues/done/20261023-154326_eventbus007_side-effects-metrics-health-recovery.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123218_eventbus007_side-effects-metrics-health-recovery.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-092908
- **Related target files**: `docs/24_eventbus/eventbus_10_health_endpoint.md`
