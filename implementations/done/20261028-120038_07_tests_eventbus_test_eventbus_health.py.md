# Procedure: update the integrity assertion and add failure-state and predicate tests

## Goal

Replace the `integrity is None` assertion and cover the DB, broker and DLQ-task failure states and the gate predicate (Plan REQ-003, REQ-006).

## Scope

- Modify only `tests/eventbus/test_eventbus_health.py`.
- Test-only change; no source file is edited.

## Assumptions

- The tests-first rows (seq 05 and 06) have been written and fail on the unmodified code before the source rows are applied (ordering note).
- Overlap (compatible): `plans/done/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` (archived, procedures pending) also targets `scripts/eventbus/route_helpers.py` (a post-lock shutdown re-check placed right after lock acquisition and before the active-user bump) and `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (Shutdown section). This procedure changes the timing statements around the lock and the Metrics section; whichever lands first, re-read the file and keep the other's lines.

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert observable behavior; use barriers or events, never sleeps.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/eventbus/test_eventbus_health.py`

### Procedure

- In `TestHealth.test_health_ok`, replace the `"integrity" in body` and `body["integrity"] is None` assertions with `"integrity" not in body`.
- Add `test_gate_predicate_is_true_for_healthy_and_capacity_only_payloads` (new) using `is_ready` from `eventbus.health_route` on the `liveness` and `readiness` values of real `/health` payloads, including the capacity-only 503 produced by shrinking `subscriber_count`.
- Add `test_gate_predicate_is_false_when_db_unavailable_or_dlq_task_stopped` (new), reusing the setups of `test_health_degraded_when_db_unavailable` and `test_health_503_when_dlq_task_stopped`.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Row 3 has landed.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_health.py -q` | Pass |
| 2 | `uv run ruff format tests/eventbus/test_eventbus_health.py`; `uv run ruff check tests/eventbus/test_eventbus_health.py` | No finding |

## Completion criteria

- The payload has no `integrity` key and the predicate tests pass.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Completed | 20261028-165731 | 20261028-165731 | Row 3 landed first (is_ready symbol) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-165731 | 20261028-165731 |  |

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
- **Requirement ID**: REQ-003, REQ-006 (health payload and gate predicate)
- **Source issue**: issues/20261027-155849_ebmetrics006_correct-db-timing-health.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094217_ebmetrics006_correct-db-timing-health.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120038
- **Related target files**: tests/eventbus/test_eventbus_health.py