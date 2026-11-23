## Goal

Add the cross-layer fixtures that let the new tests in rows 02 and 03 observe the MCP
control API and the Agent side as two processes: a real control-API subprocess on an
ephemeral loopback port and a shared `tmp_path` store handle. (REQ-006: integration-test
conventions for cross-layer tests.)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Only `tests/integration/conftest.py` is modified; the existing fixtures
  (`tmp_sqlite_db` `tests/integration/conftest.py:59-73`, `hold_write_lock` `:88-100`,
  the subprocess fixture pattern `:103-121`) stay unchanged and are reused, not rewritten.
- pytest-asyncio is available in this directory (existing async fixtures such as
  `stdio_echo_server` `tests/integration/conftest.py:35-56`), so async fixtures may use it.
- No existing test depends on the new fixtures; only the two new test files
  (`tests/integration/test_call_state_matrix_across_processes.py`,
  `tests/integration/test_call_state_crash_injection_across_processes.py`) consume them.

## Design decisions
- Follow Plan Decision D1: the control API runs as a real uvicorn subprocess on an
  ephemeral loopback port against a shared `tmp_path` store; the Agent side reaches it
  through `shared.http_transport.ControlClient` unchanged.
- Reuse the free-port selection pattern from
  `tests/integration/test_production_security_regression.py:279-283` (bind port 0, read
  the assigned port) rather than writing a new port picker.
- Add one child-process helper for the Agent-side crash points, mirroring the
  kill-and-cleanup pattern of `tests/integration/test_mcp_transport_crash.py:40-65`.

## Alternatives considered
- In-process ASGI through `fastapi.testclient.TestClient` — rejected (cannot observe a
  process death; already what `tests/mcp_servers/test_call_state_api.py:49-65` does).
- respx-mocked HTTP — rejected (single process; already what
  `tests/agent/test_mcp_call_recovery.py:125-126` does).

## Implementation
### Target file
`tests/integration/conftest.py` (modify)

### Procedure
- Add an async fixture `control_api_subprocess` (new) that starts the real control API
  (`mcp_servers.control_api.attach_control_api`) as a uvicorn subprocess on an ephemeral
  loopback port against the `tmp_sqlite_db` store, waits for the port to accept
  connections with a bounded timeout, yields the port and store path, then kills the
  subprocess.
- Add a fixture `shared_call_store` (new) returning the store path plus the handle the
  Agent side opens, so both sides refer to the same `tmp_path` SQLite file.
- Add a helper `crashed_child` (new): start a short-lived child process that performs
  one call for a given logical key and is killed at a point signaled by the test.

### Method
- Model the subprocess fixture on `tests/integration/conftest.py:103-121`
  (`asyncio.create_subprocess_exec` + bounded cleanup) and the port selection on
  `tests/integration/test_production_security_regression.py:279-283`.
- Signal-based control points (no unbounded sleeps), per the Plan's Risks section;
  keep the SQLite busy timeout short so a lock contention surfaces as the typed
  `DedupStoreError`, as `tests/shared/test_mcp_dedup_identity.py` asserts.

### Details
- The fixtures expose only what rows 02 and 03 need: port, store path, child start/kill.
- No fixture touches `/opt/llm` or a production store (REQ-006); all state lives under
  `tmp_path`.

## Compatibility considerations
- Test-only; no production module imports `tests/`; no public contract or configuration
  key changes. Existing integration tests must keep passing unchanged.

## Security considerations
- N/A: test-only fixtures; no secrets, no production store access.

## Rollback considerations
- N/A: revert the commit (fixture additions only).

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/integration/conftest.py` | Integration fixtures | `uv run pytest tests/integration/ -m integration` | Existing integration tests still pass; the new fixture starts a real server on an ephemeral port and uses only `tmp_path`. |
| Style and typing | Repository gates | `uv run ruff format --check tests/integration/` and `uv run ruff check tests/integration/`; `uv run mypy --no-namespace-packages tests/integration` | Clean; `tests/integration` is not in `pyproject.toml`'s `files`, so mypy is run explicitly. |

## Completion criteria
- The control-API subprocess fixture starts a real uvicorn on an ephemeral port against a
  `tmp_path` store, cleans up the process, and the full integration run passes five
  consecutive times (AC-006).

## Out of Scope
- The two new test files (rows 02, 03) and any change to `scripts/`, `config/`, `docs/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by rows 02/03 documents; no test for the fixture alone beyond the integration run. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs in scope. |

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
- **Requirement ID**: `REQ-006` (integration-test conventions for the cross-layer harness)
- **Source issue**: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-234341_mcpdl006_two-layer-failure-verification.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-001146
- **Related target files**: `tests/integration/conftest.py`
