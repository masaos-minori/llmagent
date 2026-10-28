# Procedure: update the gate fixtures and add malformed-body and contract tests

## Goal

Add `liveness` and `readiness` to the canned bodies and cover malformed bodies and the real-payload contract (Plan REQ-004, REQ-006).

## Scope

- Modify only `tests/deploy/test_setup_services_eventbus.py`.
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

`tests/deploy/test_setup_services_eventbus.py`

### Procedure

- Add `"liveness": True, "readiness": True` to `_HEALTH_CAPACITY_ONLY`, and `"liveness": True, "readiness": False` to `_HEALTH_DB_UNAVAILABLE`.
- Add `test_setup_services_malformed_body_aborts` (new) (the canned server returns a non-JSON body) and `test_setup_services_missing_liveness_field_aborts` (new).
- Add `test_setup_services_accepts_real_health_payload` (new): build a payload with the real `health_check` through a `TestClient` (as `tests/eventbus/test_eventbus_health.py` does) and serve it from `_start_canned`; assert the gate passes.
- Keep the existing four gate tests; they run the script in the sandbox copy and never write production paths.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Rows 3 and 4 have landed. The sandbox helpers (`_make_sandbox`, `_run_setup`, `_start_canned`) are reused unchanged.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/deploy/test_setup_services_eventbus.py -q` | Pass |
| 2 | `uv run ruff format tests/deploy/test_setup_services_eventbus.py`; `uv run ruff check tests/deploy/test_setup_services_eventbus.py` | No finding |

## Completion criteria

- Healthy and capacity-only bodies pass; the failure and malformed bodies abort; the real payload passes.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004, REQ-006 (structural gate; shared predicate)
- **Source issue**: issues/20261027-155849_ebmetrics006_correct-db-timing-health.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094217_ebmetrics006_correct-db-timing-health.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120038
- **Related target files**: tests/deploy/test_setup_services_eventbus.py
