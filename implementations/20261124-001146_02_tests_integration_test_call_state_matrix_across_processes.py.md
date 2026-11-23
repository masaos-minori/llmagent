## Goal

Create the cross-process state-mapping matrix test: every transition of
`agent_state_for` observed from both sides of a process boundary, plus the
at-most-once and fail-closed assertions. (REQ-001: cross-process mapping agreement;
REQ-003: at-most-once per logical call; REQ-004: fail-closed safety boundaries.)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The contracts under test are already implemented (`scripts/shared/mcp_call_state_contract.py`
  `agent_state_for` `:57-74`, `scripts/mcp_servers/control_api.py`, `scripts/agent/mcp_call_recovery.py`);
  this file adds verification only and cannot change behavior.
- Consumes the fixtures declared by sibling procedure
  `implementations/20261124-001146_01_tests_integration_conftest.py.md`
  (`control_api_subprocess` (new), `shared_call_store` (new)); nothing in `conftest.py` is
  re-derived here.
- Unit-level mapping coverage exists (`tests/shared/test_mcp_call_state_contract.py`); this
  file adds the cross-process dimension only, per AC-001.
- `pyproject.toml:146` defines the `integration` marker; no test in `tests/` pins a count
  of files under `tests/integration` (checked in the Plan's Step 3; re-confirmed in this pass).

## Design decisions
- Follow Plan Decision D3 (assertion source): compare the control API response over HTTP
  with the Agent recovery service report, and additionally with `agent_state_for(ledger_status,
  lease_live)` computed from the ledger row read directly; assert the same logical key on both sides.
- Transitions covered, exactly those of `agent_state_for` `:64-74`: pending with a live
  lease, pending with an expired lease, completed, failed, interrupted; plus the totality
  branch (unknown status raises `ValueError`) and the same-logical-key check — the Plan's
  test matrix names these `test_x01` (new) through `test_x07` (new).

## Alternatives considered
- Asserting only the Agent-side state — rejected (would not prove the two layers agree).
- Asserting only the HTTP payload — rejected (would not prove the Agent interprets it
  through the mapping).

## Implementation
### Target file
`tests/integration/test_call_state_matrix_across_processes.py` (new)

### Procedure
- `pytestmark = pytest.mark.integration`; only `tmp_path` stores; bounded timeouts; the
  ephemeral port comes from the `control_api_subprocess` fixture.
- `test_x01` (new) through `test_x07` (new): one test per transition in the list above; each seeds the
  shared store through the Agent side, then asserts the control API payload
  (`ControlClient.get_call_state`) equals the Agent recovery service report and equals the
  directly computed `agent_state_for` result, for the same logical key.
- `test_x10` (new): two child processes claim the same logical key; assert the handler
  runs at most once (AC-002).
- `test_x11` (new): an outcome the layers cannot classify is never rerun.
- `test_x12` (new) through `test_x16` (new): fail-closed boundaries across the process boundary — store
  loss, store replacement, schema and configuration fingerprint mismatch, unavailable audit
  or state store, approval argument tampering; and two independent logical calls with
  identical arguments that both execute exactly once (AC-003, AC-005).

### Method
- Fixed lease values and deterministic control points (no unbounded sleeps), following the
  conventions of `tests/shared/test_mcp_dedup_concurrency.py`.
- Lock contention is asserted as the typed `DedupStoreError`, as
  `tests/shared/test_mcp_dedup_identity.py` does; `hold_write_lock` is used only when a lock
  must be held deliberately.

### Details
- The Agent side reaches the control plane through `shared.http_transport.ControlClient`
  unchanged; the in-process fakes used by `tests/agent/test_mcp_call_recovery.py`
  (`FakeControlPlane`, `:51-70`, respx wiring `:125-126`) are not reused here.

## Compatibility considerations
- New file only; no existing test is extended. `tests/integration/test_mcp_transport_crash.py`
  stays the characterization baseline for the transport boundary and is not duplicated.

## Security considerations
- N/A: test-only; no secrets, no production store, no network beyond loopback.

## Rollback considerations
- N/A: delete the file (revert the commit).

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/integration/test_call_state_matrix_across_processes.py` | Integration, cross-process | `uv run pytest tests/integration/test_call_state_matrix_across_processes.py -m integration` | Every `agent_state_for` transition agrees from both sides; single execution per logical call; no side effect when safety state is unavailable. |
| Flaky detection | 5 consecutive runs | `uv run pytest tests/integration/ -m integration` | Stable results. |
| Style and typing | Repository gates | `uv run ruff format --check tests/integration/` and `uv run ruff check tests/integration/`; `uv run mypy --no-namespace-packages tests/integration` | Clean (explicit mypy run; not in `pyproject.toml`'s `files`). |

## Completion criteria
- AC-001, AC-002, AC-003, AC-005 hold for every asserted transition; the file passes five
  consecutive integration runs and touches no path under `/opt/llm` (AC-006).

## Out of Scope
- `tests/integration/conftest.py` (row 01), the crash-injection file (row 03), any change
  to `scripts/`, `config/`, `docs/`, and the documentation update owned by issue mcpai012.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | The file itself is the test; step 2 is the run and flakiness check. |
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
- **Requirement ID**: `REQ-001` (cross-process mapping), `REQ-003` (at-most-once), `REQ-004` (fail-closed)
- **Source issue**: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-234341_mcpdl006_two-layer-failure-verification.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-001146
- **Related target files**: `tests/integration/test_call_state_matrix_across_processes.py`
