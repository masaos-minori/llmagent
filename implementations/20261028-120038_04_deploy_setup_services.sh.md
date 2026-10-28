# Procedure: make the EventBus readiness gate parse the health JSON structurally

## Goal

Replace the substring match on the compacted body with a JSON check of the `liveness` and `readiness` booleans (Plan REQ-004).

## Scope

- Modify only `deploy/setup_services.sh`.
- In scope: the readiness predicate inside the EventBus gate loop and its comment block.
- Out of scope: the retry loop, the curl call, the LLM health checks, tests.

## Assumptions

- The script already uses `uv run "${UV_PROD_FLAGS[@]}" python` for the EventBus start, so the repository Python is available for the parse (UNK-03).
- A capacity-only 503 must still pass; a connection failure keeps its retry branch; a non-JSON or empty body fails the gate.
- Overlap (compatible): `plans/done/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` (archived, procedures pending) also targets `scripts/eventbus/route_helpers.py` (a post-lock shutdown re-check placed right after lock acquisition and before the active-user bump) and `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (Shutdown section). This procedure changes the timing statements around the lock and the Metrics section; whichever lands first, re-read the file and keep the other's lines.

## Design decisions

- Keep `EB_LAST_BODY` for the error message; add a small inline Python predicate that reads the raw body file.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`deploy/setup_services.sh`

### Procedure

- Replace `if [[ "${EB_LAST_BODY}" == *'"db":"ok"'* && ... ]]` with a call such as `if uv run "${UV_PROD_FLAGS[@]}" python -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get("liveness") is True and d.get("readiness") is True else 1)' < "${EB_BODY_FILE}" 2>/dev/null; then`.
- Update the comment block above the gate: ready means `liveness` and `readiness` are both true (the contract in `scripts/eventbus/health_route.py`); capacity-only degraded reasons still pass.
- Update the failure message that names the predicate (`db=ok, dlq_task=running`) to name `liveness` and `readiness`.

### Method

Edit one conditional and two message lines; no new variables.

### Details

- `EB_BODY_FILE` is removed before `eb_gate_fail`; read it inside the loop before that `rm`.
- Run `shellcheck deploy/setup_services.sh` if installed; record `Not run` otherwise.

## Compatibility considerations

- A body without the two booleans now fails the gate; the fixtures in `tests/deploy/test_setup_services_eventbus.py` are updated in row 8.

## Security considerations

- No new external input; the body comes from the loopback EventBus.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/deploy/test_setup_services_eventbus.py -q` | Pass |
| 2 | `uv run ruff format deploy/setup_services.sh`; `uv run ruff check deploy/setup_services.sh`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r deploy/setup_services.sh -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |
| 4 | `shellcheck deploy/setup_services.sh` | No finding, or recorded as `Not run: shellcheck not installed` |

## Completion criteria

- Healthy and capacity-only bodies pass the gate; `db_unavailable`, `dlq_task_stopped`, malformed and empty bodies abort it.

## Out of Scope

- Retry behavior, LLM checks.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (structural readiness gate)
- **Source issue**: issues/20261027-155849_ebmetrics006_correct-db-timing-health.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094217_ebmetrics006_correct-db-timing-health.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120038
- **Related target files**: deploy/setup_services.sh
