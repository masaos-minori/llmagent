## Goal

Make `deploy/setup_services.sh` prove the EventBus process stays alive and reaches readiness before reporting success, so an immediate process crash, a connection failure, an HTTP 503, or a `status != ok` body is never summarized as `started` (`REQ-004`).

## Scope

- Modify `deploy/setup_services.sh` only: replace the unconditional one-shot `/health` print and the unconditional `started` banner (lines 185, 198) with a bounded process + health poll that fails closed on a definitive bad signal and tolerates transient capacity degradation.
- Do not touch `deploy/load_env.sh`, `deploy/init_db.sh`, `scripts/eventbus/app.py`, or `scripts/eventbus/health_route.py` here — the health contract and the config/library are unchanged; the gate only consumes them (`REQ-004`, `REQ-005`).

## Assumptions

- The EventBus process is launched in the background at lines 180-183 with its PID captured in `EB_PID` (line 183); the gate polls that child and cleans it up on failure.
- `require_env_vars` (line 176) already gated the required EventBus variables, so the gate assumes the auth token and config path are present.
- The existing env-overridable retry/interval pattern at lines 87-88 (`LLM_HEALTH_RETRIES` / `LLM_HEALTH_INTERVAL`) is reused for the EventBus poll so the new gate matches the established, tunable convention.
- The `/health` contract in `scripts/eventbus/health_route.py` is authoritative and unchanged: `status` is `ok` or `degraded`, `db` is `ok` or `unavailable`, `dlq_task` is `running` or `stopped`, and HTTP 503 is returned whenever any `degraded_reasons` entry exists.

## Design decisions

- **Prove readiness with the provisional signal, not `status == ok`.** The gate treats the start as ready only when the `/health` body reports `db == ok` AND `dlq_task == running`. This is why a 503 that carries only capacity-only `degraded_reasons` is a healthy start and is NOT fatal: its body still has `db == ok` and `dlq_task == running`, so the readiness predicate holds.
- **Fail fast on a definitive bad signal.** Each poll first checks that `EB_PID` is still alive (`kill -0`); a dead child is a crash and aborts immediately. A response whose body does not satisfy the readiness predicate means the service is up but genuinely unavailable (`db_unavailable` or `dlq_task_stopped`, i.e. `status != ok`), which aborts. Only a connection failure (service not listening yet during startup) is retried, until the retry budget is exhausted, at which point the gate fails.
- **Mirror the existing LLM gate.** The new `eb_gate_fail` (new) helper prints a `[FATAL]`, logs the last `/health` response, kills the child (`kill ${EB_PID}`) and `wait`s it, then `exit 1`; the retry counts reuse `LLM_HEALTH_RETRIES` / `LLM_HEALTH_INTERVAL` so the poll is bounded and env-overridable.

## Alternatives considered

- **Require `status == ok` for readiness.** Rejected: `/health` returns 503 on any degraded reason including transient capacity signals, so `status == ok` would fail a healthy start; the provisional `db == ok` AND `dlq_task == running` signal distinguishes real unavailability from capacity-only degradation.
- **Keep the one-shot `sleep 2 && curl` at line 185 and only guard the banner.** Rejected: a single snapshot cannot prove the process stayed alive or that readiness held; the malformed-DB crash (lifespan failure → process exit) must be caught by polling, not by one curl.

## Implementation

### Target file

`deploy/setup_services.sh`

### Procedure

1. Open `deploy/setup_services.sh` and locate the EventBus launch block (lines 180-185): the background launch at lines 180-183, the PID print at line 184, and the unconditional one-shot `/health` print at line 185.
2. After the PID print at line 184, insert a bounded readiness poll that reuses `LLM_HEALTH_RETRIES` / `LLM_HEALTH_INTERVAL` (lines 87-88), defines an `eb_gate_fail` (new) helper that logs the last response, runs `kill ${EB_PID}` plus `wait`, and exits 1, and loops up to the retry budget checking liveness, connection, and the readiness predicate.
3. Replace the unconditional `started` banner at line 198 with a conditional line printed only after the poll confirms readiness; keep the surrounding summary block.

### Method

- Define the poll immediately after line 184 so `EB_PID` (line 183) is in scope. For each attempt: run `kill -0 "${EB_PID}" 2>/dev/null`; if it fails, call `eb_gate_fail` (new) (the child crashed during startup). Otherwise `curl -fsS -o <tmp> -w '%{http_code}'` against `http://127.0.0.1:8015/health` with `${EB_AUTH_HEADER}` (line 178).
- If the HTTP code is empty (connection refused while the server is still binding), log `...待機` and `sleep "${LLM_HEALTH_INTERVAL}"`, then continue — this is the only retried branch.
- When a response body is available, read the `db` and `dlq_task` fields. If both are `ok`/`running` respectively, set `EB_READY=1` and break. Otherwise the service responded with `status != ok` for a non-capacity reason, so call `eb_gate_fail` (new).
- After the loop, if `EB_READY` (new) is still 0 the connection never succeeded within the budget, so call `eb_gate_fail` (new).
- `eb_gate_fail` (new) mirrors `gate_fail` (lines 116-121): it writes `[FATAL]` to stderr, echoes the last `/health` response captured during the poll, ensures the child is gone with `kill "${EB_PID}" 2>/dev/null || true` followed by `wait "${EB_PID}" 2>/dev/null || true`, and `exit 1`.
- Replace the banner text at line 198 (`Event Bus (:8015, PID ${EB_PID}): started`) with `Event Bus (:8015, PID ${EB_PID}): READY (db ok, dlq_task running)` and guard it so it prints only when the gate passed; a failed gate has already exited.

### Details

- The readiness predicate reads the two JSON fields the shared readiness definition depends on: `db` must equal `ok` and `dlq_task` must equal `running`. Both come from `scripts/eventbus/health_route.py`, where `db_status` is `ok`/`unavailable` and `dlq_task_status` is `running`/`stopped`.
- Capacity-only degradation does not fail the gate. The `degraded_reasons` array in `scripts/eventbus/health_route.py` includes the transient capacity signals `lock_wait_high`, `slow_consumers_detected`, `query_duration_high`, `broker_queue_backlog_high`, and `subscribers_at_capacity`; none of these change `db` or `dlq_task`, so a body carrying only them still satisfies the readiness predicate and the start is reported READY.
- A malformed EventBus database is caught indirectly: `_init_schema()` rejects it at runtime, the uvicorn lifespan fails, and the process exits; the poll's `kill -0` check then fires `eb_gate_fail` (new) before any response is seen.
- No new shell function beyond `eb_gate_fail` (new); the poll reuses the `uv run` flags already used at lines 36-68 via the shared `UV_PROD_FLAGS` list.

## Compatibility considerations

- `setup_services.sh` is sourced by `deploy.sh`; the gate only adds a bounded, env-overridable poll and a fatal path that previously did not exist, so a canonical start proceeds exactly as before once readiness holds.
- The poll reads `/health` with the same `${EB_AUTH_HEADER}` bearer already used at line 185, so no new auth path is introduced.

## Security considerations

- Fail-closed: a crashed, unreachable, or degraded process aborts `setup_services.sh` instead of reporting success. The last `/health` response is logged to stderr; it contains health metrics, not secrets or token values.

## Rollback considerations

- Revert the EventBus readiness block in `deploy/setup_services.sh` (or `git checkout` the parent commit); the Workflow pre-flight (lines 24-75), the LLM gate (lines 80-155), and `require_env_vars` (line 176) are untouched.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `deploy/setup_services.sh` | Integration: process-exit/connection-failure/non-200/status!=ok abort with cleanup; healthy start passes; capacity-only 503 does not fail | `uv run pytest tests/deploy/test_setup_services_eventbus.py` | each fatal case aborts with child cleanup and last-response logging; healthy start reports READY; capacity-only degradation does not abort |

## Completion criteria

- The EventBus block polls `/health` up to `LLM_HEALTH_RETRIES` times with `LLM_HEALTH_INTERVAL` between attempts and only reports READY when `db == ok` AND `dlq_task == running`.
- A dead child, a persistent connection failure, or a non-capacity `status != ok` body aborts with `eb_gate_fail` (new), which kills `EB_PID` and logs the last response.
- A healthy start carrying only capacity-only `degraded_reasons` still reports READY.
- `shellcheck`, `ruff`, `mypy`, `bandit`, and `lint-imports` pass with all contracts KEPT.

## Out of Scope

- The `/health` contract and `degraded_reasons` taxonomy (`scripts/eventbus/health_route.py`), the runtime startup gate (`REQ-002`), the `init_db.sh` strict gate (`REQ-003`), and the config/token preflight (`REQ-005`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert the bounded EventBus readiness poll after the PID print (line 184), reusing `LLM_HEALTH_RETRIES` / `LLM_HEALTH_INTERVAL` | Pending | — | — | REQ-004 |
| 2 | Add `eb_gate_fail` (new) (last-response logging + `kill ${EB_PID}` cleanup) and replace the unconditional banner at line 198 | Pending | — | — | REQ-004 |
| 3 | Add `tests/deploy/test_setup_services_eventbus.py` per the Validation plan | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: deploy only |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261023-154326_eventbus003_startup-gate-schema-health.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-111552_eventbus003_startup-gate-schema-health.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-155039
- **Related target files**: `deploy/setup_services.sh`
