# Procedure: remove the integrity placeholder and compute the gate predicate once

## Goal

Remove the always-`null` `integrity` field and define the readiness gate predicate (liveness and readiness) in one place (Plan REQ-003).

## Scope

- Modify only `scripts/eventbus/health_route.py`.
- In scope: the `liveness` / `readiness` / `integrity` lines and the payload.
- Out of scope: degraded reasons, the 503 rule, thresholds, the deployment script, tests, docs.

## Assumptions

- Schema integrity is enforced at startup (`scripts/eventbus/schema.py`), so the `H-03` placeholder is obsolete; no reader of `integrity` exists in `scripts/`, `deploy/` or tests other than the placeholder test (row 7).
- HTTP 503 stays for any degraded reason; capacity-only reasons are documented, not changed.
- Overlap (compatible): `plans/done/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` (archived, procedures pending) also targets `scripts/eventbus/route_helpers.py` (a post-lock shutdown re-check placed right after lock acquisition and before the active-user bump) and `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (Shutdown section). This procedure changes the timing statements around the lock and the Metrics section; whichever lands first, re-read the file and keep the other's lines.

## Design decisions

- Add a module-level `is_ready(liveness, readiness)` (new) so the contract has one definition that tests and docs reference; the payload keeps `liveness` and `readiness`.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/eventbus/health_route.py`

### Procedure

- Delete `integrity = None` and the `"integrity": integrity` payload key.
- Add `def is_ready(liveness: bool, readiness: bool) -> bool: return liveness and readiness` (new) with a docstring stating that it is the readiness gate predicate used by the deployment gate.
- Keep `liveness = dlq_task_status == "running"` and `readiness = db_ok`, and compute `ready = is_ready(liveness, readiness)` only if the payload needs it; otherwise leave the helper for the contract test (row 8) and the docs.

### Method

Remove one key and add one small function.

### Details

- `check_docstrings.py` requires the `scripts/<path> — description` module header to stay as is.

## Compatibility considerations

- Behavior change: the `integrity` key disappears from `/health`.

## Security considerations

- No security impact.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_health.py -q` | Pass |
| 2 | `uv run ruff format scripts/eventbus/health_route.py`; `uv run ruff check scripts/eventbus/health_route.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/eventbus/health_route.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- The payload has no `integrity` key and `is_ready` (new) is the single documented predicate.

## Out of Scope

- Degraded reasons, deployment script.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-165731 | 20261028-165731 | is_ready is a contract helper not called by the payload; reference table regenerated (eventbus_08, out of target) |
| 2 | Add or update tests per Validation plan | Completed | 20261028-165731 | 20261028-165731 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-165731 | 20261028-165731 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-165731 | 20261028-165731 |  |

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
- **Requirement ID**: REQ-003 (health contract)
- **Source issue**: issues/20261027-155849_ebmetrics006_correct-db-timing-health.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094217_ebmetrics006_correct-db-timing-health.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120038
- **Related target files**: scripts/eventbus/health_route.py