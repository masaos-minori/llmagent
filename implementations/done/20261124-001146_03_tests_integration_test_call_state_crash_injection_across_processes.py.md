## Goal

Create the cross-process crash-injection test: process deaths at the Agent and MCP points,
asserted through the state mapping and the dedup gate rather than the raw transport, plus
reconciliation-only recovery for a lost response. (REQ-002: crash injection through the
mapping; REQ-005: response-loss recovery never re-executes.)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Consumes the fixtures declared by sibling procedure
  `implementations/20261124-001146_01_tests_integration_conftest.py.md`
  (`control_api_subprocess` (new), `shared_call_store` (new), `crashed_child` (new)).
- Crash injection uses `proc.kill()` at a chosen point (resolved by repository evidence,
  Plan UNK-02): `tests/integration/test_mcp_transport_crash.py:40-65` and the killed-child
  case on a shared DB path `tests/shared/test_mcp_dedup_concurrency.py:316-336`.
- The recovery service that must not re-execute is implemented at
  `scripts/agent/mcp_call_recovery.py` (module docstring `:1-12` states it never executes a
  tool handler); the file asserts this existing behavior, it cannot change it.

## Design decisions
- Follow Plan Decision D2: kill the process with `proc.kill()` at a chosen point; the four
  MCP points (before the handler, during the handler, after the effect, before the response)
  are made distinguishable by a test-only handler that blocks on a signal before writing the
  response. The Agent-side points (before send, after send, after MCP completion) are
  produced by a short-lived child process killed at each point.
- Assertions go through the mapping (`agent_state_for`) and the dedup gate, not through raw
  transport EOF — `tests/integration/test_mcp_transport_crash.py` remains the separate
  characterization record of the transport boundary and is not extended.

## Alternatives considered
- Raising an exception inside the handler — rejected (an exception is not a process death;
  it tests the error path, not the recovery path).
- Simulating a crash by closing the store connection — rejected (changes the store, not the
  process).

## Implementation
### Target file
`tests/integration/test_call_state_crash_injection_across_processes.py` (new)

### Procedure
- `pytestmark = pytest.mark.integration`; only `tmp_path` stores; bounded timeouts; the
  ephemeral port comes from the `control_api_subprocess` fixture.
- `test_c01` (new) through `test_c03` (new): Agent-side crash points — before send, after send, after
  MCP completion; each asserts the resulting state through the mapping and that a side
  effect is not repeated.
- `test_c04` (new) through `test_c07` (new): MCP-side crash points — before the handler, during the
  handler, after the effect, before the response; each asserts the resulting state and that
  no handler runs twice.
- `test_c08` (new): a lost response resolves from recorded evidence via reconciliation;
  the assertion is that no handler call occurs (AC-004).

### Method
- The child signals the reached point before being killed, so each test is deterministic;
  no unbounded sleeps (Plan Risks mitigation).
- Assert the state as read back through `ControlClient.get_call_state` and the Agent
  recovery service, equal to `agent_state_for` computed from the ledger row, for the same
  logical key — the same assertion source as row 02 (Decision D3).

### Details
- If a safety boundary cannot be tested without touching production data, stop and report
  (the Issue's own instruction); the fixture guarantees only `tmp_path` stores.

## Compatibility considerations
- New file only; existing single-process tests (`tests/integration/test_agent_mcp_integration.py`,
  `tests/agent/test_mcp_call_recovery.py`) are unchanged.

## Security considerations
- N/A: test-only; no secrets, no production store, loopback only.

## Rollback considerations
- N/A: delete the file (revert the commit).

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/integration/test_call_state_crash_injection_across_processes.py` | Integration, cross-process | `uv run pytest tests/integration/test_call_state_crash_injection_across_processes.py -m integration` | Each crash point yields the mapped state; recovery reconciles from evidence without re-executing. |
| Flaky detection | 5 consecutive runs | `uv run pytest tests/integration/ -m integration` | Stable results; crash-point timing is the main risk. |
| Style and typing | Repository gates | `uv run ruff format --check tests/integration/` and `uv run ruff check tests/integration/`; `uv run mypy --no-namespace-packages tests/integration` | Clean (explicit mypy run; not in `pyproject.toml`'s `files`). |

## Completion criteria
- AC-004 holds for all seven crash points and the reconciliation case; the file passes five
  consecutive integration runs and touches no path under `/opt/llm` (AC-006).

## Out of Scope
- `tests/integration/conftest.py` (row 01), the matrix file (row 02),
  `tests/integration/test_mcp_transport_crash.py` (characterization baseline, not extended),
  any change to `scripts/`, `config/`, `docs/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-24T00:11 | 2026-11-24T08:20 |  |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-24T07:50 | 2026-11-24T08:20 | The file itself is the test; step 2 is the run and flakiness check. 8 crash points c01-c08; 5 consecutive full integration runs, 31 passed. Deterministic: bounded signal hold, seeded now_epoch, effects counted in a file rather than from printed labels. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-24T08:15 | 2026-11-24T08:20 | Same batch gates as row 01; full suite run once at batch end. Child process uses sys.executable with PYTHONPATH=scripts/, never the parent conftest sys.path shim. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | N/A: no docs in scope. |

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
- **Requirement ID**: `REQ-002` (crash injection through the mapping), `REQ-005` (reconciliation-only recovery)
- **Source issue**: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-234341_mcpdl006_two-layer-failure-verification.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-001146
- **Related target files**: `tests/integration/test_call_state_crash_injection_across_processes.py`