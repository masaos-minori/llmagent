# Procedure: define liveness, readiness, the gate predicate and the metric definitions

## Goal

Remove `integrity`, define the gate predicate and 503 semantics, and state the metric definitions (Plan REQ-003, REQ-007).

## Scope

- Modify only `docs/24_eventbus/eventbus_10_health_endpoint.md`.
- Documentation-only change; state current behavior only.

## Assumptions

- The tests-first rows (seq 05 and 06) have been written and fail on the unmodified code before the source rows are applied (ordering note).
- All text stays English (`skills/DESIGN.md` Output language).
- Overlap (compatible): `plans/done/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` (archived, procedures pending) also targets `scripts/eventbus/route_helpers.py` (a post-lock shutdown re-check placed right after lock acquisition and before the active-user bump) and `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (Shutdown section). This procedure changes the timing statements around the lock and the Metrics section; whichever lands first, re-read the file and keep the other's lines.

## Design decisions

- Edit the named sentences after re-reading the current text; do not reflow surrounding paragraphs.

## Alternatives considered

N/A: lightweight row.

## Implementation

### Target file

`docs/24_eventbus/eventbus_10_health_endpoint.md`

### Procedure

- In the field table, delete the `integrity` row and the sentence that explains it; replace with: `liveness` (the DLQ task is running) and `readiness` (the database is connectable); the deployment readiness gate is `liveness and readiness`; the broker is not part of the gate.
- State the 503 semantics: HTTP 503 is returned for any degraded reason, including capacity-only reasons (`subscribers_at_capacity`, `lock_wait_high`, `query_duration_high`, `slow_consumers_detected`, `broker_queue_backlog_high`), and a capacity-only 503 still satisfies the gate.
- Update the metrics paragraph: `eventbus_db_lock_wait_time_seconds` is the time from thread submit to lock acquisition; `eventbus_db_query_duration_seconds` is DB execution while holding the lock, recorded also when the callback raises; `eventbus_slow_consumer_current` is the current slow-consumer count and returns to zero.

### Method

Targeted sentence edits after re-reading the current file state.

### Details

- The doc already states the wait and gauge definitions; the edits make them true of the code and remove the placeholder.

## Compatibility considerations

N/A: documentation-only.

## Security considerations

N/A: documentation-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py --strict`; `uv run python tools/check_docs_japanese.py`; `uv run python tools/check_docs_consistency.py --domain eventbus` | No finding |

## Completion criteria

- The document states the behavior described in Details.
- All listed documentation checkers report no finding.

## Out of Scope

- Every other document.
- Code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-007 (health contract and metric definitions)
- **Source issue**: issues/20261027-155849_ebmetrics006_correct-db-timing-health.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094217_ebmetrics006_correct-db-timing-health.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120038
- **Related target files**: docs/24_eventbus/eventbus_10_health_endpoint.md
