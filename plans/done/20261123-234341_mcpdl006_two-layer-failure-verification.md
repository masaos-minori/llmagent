## Goal
- Add cross-process integration tests that prove the Agent layer and the MCP layer observe the same logical call, agree on the authoritative state mapping, execute a side effect at most once, and fail closed at every safety boundary.

## Priority
Medium

## Scope
- **In-Scope**:
  - A test-only cross-layer harness that runs the MCP control API as a real subprocess and reaches it from the Agent side through `shared.http_transport.ControlClient`.
  - A transition matrix test for the authoritative mapping `shared.mcp_call_state_contract.agent_state_for`, observed from both sides of the process boundary.
  - Crash injection at the Agent points (before send, after send, after MCP completion) and the MCP points (before the handler, during it, after the effect, before the response), asserted through the state mapping and the dedup gate rather than through the raw transport.
  - At-most-once handler execution per logical call under cross-process concurrency, and the rule that an unknown outcome is never re-executed.
  - Fail-closed behavior across the process boundary when the MCP safety state is unavailable.
  - The existing raw-transport crash tests stay separate and unchanged as characterization tests of the transport boundary; the new tests do not duplicate them.
- **Out-of-Scope**:
  - Implementation of the contracts under test (the Issue names this explicitly).
  - Any change to `scripts/`, `config/`, `docs/`, or the existing single-component tests.
  - The documentation update that links each invariant to its proving test (owned by related issue mcpai012).
- **Dependencies**: closed — mcpdl001, mcpdl002, mcpdl003, mcpdl004, mcpdl005. Their work items are in `issues/done/` and their procedures in `implementations/done/`; this Plan does not need to wait for them (see Unknowns UNK-01 for the stale Execution Status rows in the mcpdl003 and mcpdl004 plans). Related: mcpai010 covers GitHub HTTP contracts and is not duplicated here.
  - N/A: no `Depends on` bullet — every dependency is already implemented, so no phase of this Plan must wait for another Plan or Issue.

## Background
Source: consolidated MCP deduplication two-layer defense backlog (`memo-issue.md`, Issue 6). Unit tests cannot prove two-layer safety: the Agent can record durable intent while the MCP server uses another id, or the ledger can enforce one owner while the Agent retries an unknown outcome. The Issue marked "which cross-process tests already exist" as `Needs confirmation`; Step 2 resolved it against the test tree (see Problem).

## Problem
Verified against the current test tree, the Issue's claim still reproduces:

- The authoritative mapping is verified only at unit level: `tests/shared/test_mcp_call_state_contract.py` asserts `agent_state_for` totality in one process; `tests/mcp_servers/test_call_state_api.py` serves the control API through `fastapi.testclient.TestClient` (in-process ASGI, `tests/mcp_servers/test_call_state_api.py:49-65`); `tests/agent/test_mcp_call_recovery.py` answers the Agent's control calls through respx-mocked routes (`tests/agent/test_mcp_call_recovery.py:125-126`, wiring the `FakeControlPlane` handler defined at `:51-70`). No test crosses a process boundary for the state mapping.
- Genuine cross-process coverage is limited to `tests/integration/test_mcp_transport_crash.py` (raw subprocess stdio EOF, no state mapping or dedup gate) and `tests/integration/test_agent_mcp_integration.py` (respx-mocked HTTP in a single process).
- Multi-process capability exists only as short-lived subprocesses on one DB path in `tests/shared/test_mcp_dedup_concurrency.py`, and as a real uvicorn subprocess on a free loopback port in `tests/integration/test_production_security_regression.py:264-293`. Neither is wired to the call-state control plane.

So the two-layer safety property the backlog asks for has no test that observes it across two processes.

## Reason for Change
Verification of the whole defense once its parts exist. All five implementation issues are archived and their contracts are present in source, so the verification phase can start; it is separate from the implementation issues because it validates behavior across processes.

## Implementation Intent
Add integration tests only, reusing the repository's existing cross-process patterns: the real-server-subprocess-on-a-free-loopback-port pattern already used by `tests/integration/test_production_security_regression.py`, and the short-lived child-process-on-one-DB-path pattern already used by `tests/shared/test_mcp_dedup_concurrency.py`. Assert behavior through the shared mapping and the dedup gate, not through transport details. Keep legacy-behavior coverage separate as characterization tests.

## Requirements
- `REQ-001`: Assert the authoritative Agent-to-MCP state mapping across two processes. For every transition of `agent_state_for` (pending with a live lease, pending with an expired lease, completed, failed, interrupted), the state the control API reports over HTTP equals the state the Agent's recovery service reports for the same logical call id, and both refer to the same logical key.
- `REQ-002`: Inject process crashes through the state mapping and the dedup gate. Agent side: before send, after send, after MCP completion. MCP side: before the handler, during the handler, after the effect, before the response. Each case asserts the resulting state and that a side effect is not repeated.
- `REQ-003`: Assert at-most-once handler execution per logical call under cross-process concurrency, and that an outcome the layers cannot classify is never rerun.
- `REQ-004`: Assert that a safety-critical store or configuration failure rejects the write across the process boundary: store loss, store replacement, schema and configuration fingerprint mismatch, unavailable audit or state store, approval argument tampering, and two independent logical calls with identical arguments that both execute once.
- `REQ-005`: Assert that response-loss recovery uses MCP evidence and reconciliation and never re-executes the handler.
- `REQ-006`: New tests follow the repository's integration-test conventions: `pytestmark = pytest.mark.integration`, only `tmp_path` stores (no `/opt/llm` or production store), bounded timeouts with no unbounded sleeps, and an ephemeral loopback port.

## Implementation Target Files
**Freeze status**: Frozen (Step 8b passed: all rows `Verified`, `tools/audit_plan_target_paths.py` reported no missing path, `tools/check_plan_target_overlaps.py` reported no overlap with another Frozen Plan.)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/integration/conftest.py` | modify | Add the cross-layer fixtures: a real control-API subprocess on an ephemeral loopback port and a shared `tmp_path` store handle used by both sides. | REQ-006; AC-006 | The file already holds `tmp_sqlite_db` (`tests/integration/conftest.py:59-73`), `hold_write_lock` (`:88-100`) and the subprocess fixture pattern (`:103-121`); no control-API fixture exists. The port pattern exists at `tests/integration/test_production_security_regression.py:279-283` (checked in Step 3). | New fixtures consumed by `tests/integration/test_call_state_matrix_across_processes.py` and `tests/integration/test_call_state_crash_injection_across_processes.py`; the existing fixtures are exercised unchanged. | Verified |
| `tests/integration/test_call_state_matrix_across_processes.py` | create (new file) | Test-only matrix: every `agent_state_for` transition observed through two processes, plus the at-most-once and fail-closed assertions. | REQ-001, REQ-003, REQ-004; AC-001, AC-002, AC-003, AC-005, AC-006 | No existing test crosses a process boundary for the mapping (`tests/mcp_servers/test_call_state_api.py:49-65` in-process ASGI, `tests/agent/test_mcp_call_recovery.py:125-126` respx mock wiring a `FakeControlPlane` handler); the mapping itself is implemented at `scripts/shared/mcp_call_state_contract.py:57-74`. (checked in Step 2/3; line citation corrected in this pass) | `test_x01..x07` per transition, `test_x10` cross-process single-execution race, `test_x11` unknown outcome never rerun, `test_x12..x16` fail-closed boundaries. | Verified |
| `tests/integration/test_call_state_crash_injection_across_processes.py` | create (new file) | Crash injection at the Agent and MCP points, asserted through the mapping and the dedup gate; reconciliation-only recovery for a lost response. | REQ-002, REQ-005; AC-004 | The kill-mid-operation pattern exists (`tests/integration/test_mcp_transport_crash.py:40-65`, `tests/shared/test_mcp_dedup_concurrency.py:316-336`) but asserts transport EOF, not the state mapping; the recovery service that must not re-execute is implemented at `scripts/agent/mcp_call_recovery.py:1-12`. (checked in Step 3) | `test_c01..c03` Agent crash points, `test_c04..c07` MCP crash points, `test_c08` reconciliation without re-execution. | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/mcp_call_state_contract.py` | The authoritative mapping and closed vocabularies the matrix asserts. | REQ-001 |
| `scripts/mcp_servers/control_api.py` | The control-plane endpoints and the error codes the Agent side receives. | REQ-001, REQ-004 |
| `scripts/agent/mcp_call_recovery.py` | The Agent-side reader and the rule that recovery never re-executes. | REQ-001, REQ-005 |
| `scripts/shared/http_transport.py` | `ControlClient`, the client the cross-layer tests must use unchanged. | REQ-001 |
| `scripts/shared/mcp_dedup_ledger.py` | The ledger states, owner lease, and pending-row transitions the matrix maps from. | REQ-001, REQ-003 |
| `scripts/agent/workflow/tool_call_state_ops.py` | `TOOL_CALL_STATES` and `classify_stale_pending` (`scripts/agent/workflow/tool_call_state_ops.py:173`), the Agent-side states compared against the mapping. | REQ-001 |
| `tests/shared/test_mcp_dedup_concurrency.py` | The short-lived-subprocess-on-one-DB-path pattern and the killed-owner reconciliation case to follow, not duplicate. | REQ-003 |
| `tests/integration/test_mcp_transport_crash.py` | The characterization baseline for the transport boundary that the new tests must not duplicate. | Assumptions, Risks |
| `tests/integration/test_production_security_regression.py` | The real-server-subprocess and free-loopback-port fixture pattern to reuse. | REQ-006 |
| `tests/integration/test_agent_mcp_integration.py` | Existing single-process coverage; the boundary between it and the new cross-layer tests. | REQ-001 |
| `tests/shared/test_mcp_call_state_contract.py` | Existing unit-level mapping coverage; the new tests must add the cross-process dimension only. | REQ-001 |
| `pyproject.toml` | The `integration` marker definition (`pyproject.toml:146`) the new files must carry. | REQ-006 |

## Acceptance Criteria
- AC-001 (REQ-001): Every transition of `agent_state_for` has a cross-process test, and the two sides report the same state for the same logical call id.
- AC-002 (REQ-003): One logical call runs its handler at most once under cross-process concurrency.
- AC-003 (REQ-004): No side effect runs when a mandatory Agent or MCP safety state is unavailable across the process boundary.
- AC-004 (REQ-002, REQ-005): Response-loss recovery uses MCP evidence and reconciliation, and an unknown outcome is never rerun.
- AC-005 (REQ-003, REQ-004): Independent calls with identical arguments both execute exactly once.
- AC-006 (REQ-006): The new tests run with `-m integration`, touch no path under `/opt/llm`, and pass five consecutive runs.

## Tests
- Test matrix (REQ-001, AC-001): one test per mapping transition, observed through the control API over HTTP and through the Agent recovery service in the same run.
- Crash injection (REQ-002, AC-004): three Agent-side crash points and four MCP-side crash points, each asserting the state after the process dies and that no handler runs twice.
- Concurrency and at-most-once (REQ-003, AC-002, AC-005): two child processes claiming the same logical key; and two independent logical calls with identical arguments.
- Fail-closed boundaries (REQ-004, AC-003): store loss, replacement, schema and configuration fingerprint mismatch, unavailable audit or state store, approval argument tampering.
- Reconciliation-only recovery (REQ-005, AC-004): a lost response resolves from recorded evidence; the assertion is that no handler call occurs.
- Execution (REQ-006, AC-006): `uv run pytest tests/integration/ -m integration`; run the new files 5 times for flakiness; then the full suite per `rules/toolchain.md` section 7.
- Characterization tests stay separate: `tests/integration/test_mcp_transport_crash.py` remains the transport-boundary record and is not extended.

## Documentation Impact
N/A: no `docs/*.md` change from this Plan. The documentation that names the proving test for each state and recovery invariant is the scope of related issue mcpai012, which reads the MCP server spec docs through `docs/00_index.md`'s Document References by Task mapping and depends on this Plan's test names being fixed.

## Assumptions
- The contracts under test are already implemented (`scripts/shared/mcp_call_state_contract.py`, `scripts/mcp_servers/control_api.py`, `scripts/agent/mcp_call_recovery.py`); this Plan adds verification only and cannot change behavior.
- All new tests use `tmp_path` stores and an ephemeral loopback port; nothing reaches `/opt/llm` or a production store.
- The new tests are excluded from the marker-filtered coverage run (`-m "not integration and not production_paths_allowed and not repo_scan"`), so they are observed only by the full suite and CI; the coverage gate is not expected to change.
- No test pins a count of files or tests under `tests/integration`, so adding files does not break a pinned-count test (searched `tests/` in Step 3, none found).
- The stale Execution Status rows in the plans of mcpdl003 and mcpdl004 are a document-status gap, not an implementation gap; their procedures exist in `implementations/done/`. Recorded as UNK-01.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? |
|---|---|---|---|---|
| UNK-01 | Whether the `Pending` rows in the mcpdl003 and mcpdl004 plans represent work not executed. 36 rows of mcpdl004 and 44 rows of mcpdl003 read `Pending` while their procedures are in `implementations/done/` and the contracts are in source. | The plan documents cannot confirm whether the archived procedures were validated; only the plan rows would have to be updated. | Update those plans' Execution Status rows in a separate documentation pass. Not needed before this Plan is implemented: the code under test is present (Step 2 evidence). | False |
| UNK-02 | The Issue's `不明`: how multi-process crash injection is done in the repository's test environment. Resolved by repository evidence, not an open question. | None — resolved. | Established pattern: `asyncio.create_subprocess_exec` + `proc.kill()` (`tests/integration/test_mcp_transport_crash.py:40-65`) and a killed child process on a shared DB path (`tests/shared/test_mcp_dedup_concurrency.py:316-336`). Recorded as a Design decision. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`. The `File` column is a subset of the `Implementation Target Files` rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tests/integration/conftest.py` | modify | Low — test-only fixtures; no production module imports it; no other test depends on the new fixtures. | 1 commit (`git log --since=30.days`, Step 5) | N/A: `git-fame` not available | not applicable (rsynced) |
| `tests/integration/test_call_state_matrix_across_processes.py` | create | Low — no consumers; collected only by the integration marker run. | 0 (new file) | N/A: `git-fame` not available | not applicable (rsynced) |
| `tests/integration/test_call_state_crash_injection_across_processes.py` | create | Low — no consumers; collected only by the integration marker run. | 0 (new file) | N/A: `git-fame` not available | not applicable (rsynced) |

## Design
Path B classification: more than three files would change (three test files), and the tests exercise runtime-facing behavior across a process boundary. Rationale recorded in Step 3.

Architecture analysis (Step 5):
- `uv run lint-imports` reports 6 contracts kept, 0 broken. The new test files import `shared` and `agent` modules only; no production module imports `tests/`, so no new edge and no cycle. `shared-is-leaf` is untouched because no `scripts/` file changes.
- Dependency graphing: the concrete list of files requiring change is the three rows above. `pydeps` and `universal-ctags` are not installed; the consumer list came from `rg "from shared.mcp_call_state_contract import"` and `rg "from agent.mcp_call_recovery import"`, which returned the seven `scripts/` consumers already present and three test files — none of them modified by this Plan.

Historical analysis: high-churn integration test files (`test_rag_turn_integration.py` 11, `test_production_security_regression.py` 7, `test_agent_mcp_integration.py` 6) are left untouched; the only touched existing file has 1 commit in the last 30 days, so change risk is low.

Operational dependency inspection: `ss -ltnpH 'sport = :8000'` returned no listener, and the tests bind an ephemeral port, so no process holds the port the new tests use. `fuser` was not run: the tests use `tmp_path` stores, so no persisted database is touched. No dependency upgrade is planned, so `pip-audit` was not run (tool not available).

Validation quality baseline: N/A: no Python target under `scripts/` or `tools/`. `radon`, `vulture`, `bandit`, and `diff-cover` are installed but have no target here; the diff-cover threshold in `rules/toolchain.md` is not affected by a tests-only change.

Predictable fallout check (Step 3, `workflow-edge.md`):
- Module size: not affected — `check_module_size.py` covers `scripts/` and `tools/` only; `tests/integration/conftest.py` is 5762 B and outside the gate.
- Pinned counts: not affected — no test in `tests/` pins a count of files or tests in `tests/integration`.
- Tool inventory: not affected — no `tools/*.py` is added or removed.
- Generated blocks: not affected — no generated-reference domain is touched.
- Consumer scan: not applicable — no persisted schema, public API, or shared constant changes, and no symbol is removed or renamed.

Design decisions (Path B, `python-design` Step 4 applied narrowly):
- **Decision D1 — process model**: the MCP control API runs as a real uvicorn subprocess on an ephemeral loopback port against a shared `tmp_path` store; the Agent side reaches it through `shared.http_transport.ControlClient`.
  - Alternatives considered: in-process ASGI through `fastapi.testclient.TestClient` (rejected — that is what `tests/mcp_servers/test_call_state_api.py` already does and it cannot observe a process death); respx-mocked HTTP (rejected — same single process as `tests/agent/test_mcp_call_recovery.py`); both sides as separate long-lived processes (rejected — no additional assertion becomes possible; the Agent-side crash is produced by a short-lived child process, which is enough to observe its death in the ledger).
  - Compatibility impact: test-only, no production caller, no configuration key, no public contract changes. Files carry `pytestmark = pytest.mark.integration` per `pyproject.toml:146`, so the marker-filtered coverage run does not see them.
  - Reversibility: low — removing the files and the fixture restores the current state.
- **Decision D2 — crash injection**: kill the process with `proc.kill()` at a chosen point, using a test-only handler that blocks before it writes the response so the four MCP points are distinguishable; the Agent-side points are produced by a child process killed before send, after send, and after MCP completion.
  - Alternatives considered: raising an exception inside the handler (rejected — an exception is not a process death and would test the error path, not the recovery path); simulating a crash by closing the store connection (rejected — it changes the store, not the process).
  - Compatibility impact: none; follows the pattern already used in `tests/integration/test_mcp_transport_crash.py`.
  - Reversibility: low.
- **Decision D3 — assertion source**: compare what the control API returns over HTTP with what the Agent recovery service reports, and additionally with `agent_state_for(ledger_status, lease_live)` computed from the ledger row read directly. Assert the same logical key on both sides.
  - Alternatives considered: asserting only the Agent-side state (rejected — it would not prove the two layers agree); asserting only the HTTP payload (rejected — it would not prove the Agent interprets it through the mapping).
  - Compatibility impact: none.
  - Reversibility: low.

## Implementation steps
1. **Phase 1: Cross-layer test harness**
   - [ ] Add the control-API subprocess fixture (real uvicorn on an ephemeral loopback port, `tmp_path` store shared with the Agent side) and the child-process helper to `tests/integration/conftest.py` (REQ-006; `tests/integration/conftest.py`), reusing `tmp_sqlite_db` and the port-selection pattern instead of writing new ones.
2. **Phase 2: Cross-layer state-mapping matrix**
   - [ ] Create `tests/integration/test_call_state_matrix_across_processes.py` with one test per `agent_state_for` transition, asserting the control API response and the Agent recovery service report the same state and the same logical key (REQ-001; `tests/integration/test_call_state_matrix_across_processes.py`).
   - [ ] Add the cross-process at-most-once and never-rerun assertions, and the fail-closed boundary assertions, in the same file (REQ-003, REQ-004; `tests/integration/test_call_state_matrix_across_processes.py`).
3. **Phase 3: Crash injection through the mapping and the dedup gate**
   - [ ] Create `tests/integration/test_call_state_crash_injection_across_processes.py` with the three Agent crash points and four MCP crash points, asserting the resulting state and that no handler runs twice (REQ-002; `tests/integration/test_call_state_crash_injection_across_processes.py`).
   - [ ] Add the reconciliation-only recovery case for a lost response (REQ-005; `tests/integration/test_call_state_crash_injection_across_processes.py`).
   - [ ] Per-step constraint from the Issue: reuse existing fixtures; stop and report if a safety boundary cannot be tested without touching production data.
4. **Phase 4: Validation**
   - [ ] Run the gates for the three target files (see Validation plan); run the new files 5 times for flakiness, then the full suite. No deploy step: no `scripts/` or `config/` file changes, so deployment is not part of this Plan (tests/ is rsynced by `deploy/deploy.sh`); deployment remains the user's decision.

### Release units
N/A: no release unit — each phase is validated alone; Phase 2 and Phase 3 depend on Phase 1 only as a fixture provider and each passes on its own.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/integration/conftest.py` | Integration fixtures only | `uv run pytest tests/integration/ -m integration` | Existing integration tests still pass; the new fixtures start a real server on an ephemeral port and use only `tmp_path`. |
| `tests/integration/test_call_state_matrix_across_processes.py` | Integration, cross-process | `uv run pytest tests/integration/test_call_state_matrix_across_processes.py -m integration` | Every `agent_state_for` transition is observed from both sides and agrees; single execution per logical call; no side effect when safety state is unavailable. |
| `tests/integration/test_call_state_crash_injection_across_processes.py` | Integration, cross-process | `uv run pytest tests/integration/test_call_state_crash_injection_across_processes.py -m integration` | Each crash point yields the mapped state; recovery reconciles from evidence without re-executing. |
| All three | Flaky detection | `uv run pytest tests/integration/ -m integration` 5 consecutive runs | Stable results; subprocess timing is the main risk (bounded timeouts, no unbounded sleeps). |
| Regression scope | Full suite with the standard filter | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"` then `uv run coverage xml` | No existing test breaks; the coverage number is unchanged (tests-only change). |
| Style and typing | Repository gates | `uv run ruff format --check tests/integration/` and `uv run ruff check tests/integration/`; `uv run mypy --no-namespace-packages tests/integration` | Clean; `tests/integration` is not in `pyproject.toml`'s `files`, so mypy is run explicitly per `rules/toolchain.md`. |

## Risks
- **Risk**: subprocess timing makes the new tests flaky (crash points are timing-sensitive). → **Mitigation**: follow `tests/shared/test_mcp_dedup_concurrency.py`'s convention — bounded timeouts and fixed lease values, no unbounded sleeps; deterministic control points chosen by an explicit signal from the child process; run 5 times before finishing.
- **Risk**: two processes writing one SQLite file can hit lock contention, which can mask a real failure as a lock error. → **Mitigation**: keep the busy timeout short and assert the typed store error, as `tests/shared/test_mcp_dedup_identity.py` does; use `tests/integration/conftest.py:88-100` when a lock must be held deliberately.
- **Risk**: the tests could touch a production store or the real config, which the Issue forbids. → **Mitigation**: only `tmp_path` stores and an ephemeral port; stop and report if a boundary cannot be tested without production data (the Issue's own instruction).
- **Risk**: port availability in CI differs from this host. → **Mitigation**: bind port 0 and read the assigned port, following `tests/integration/test_production_security_regression.py:279-283`.
- **Risk**: duplication with existing coverage (raw transport, GitHub HTTP contracts) makes the new suite redundant. → **Mitigation**: the new tests assert the mapping and the dedup gate across a process boundary only; `test_mcp_transport_crash.py` and mcpai010's scope are left unchanged.
- **Risk**: the stale Execution Status rows in the mcpdl003 and mcpdl004 plans could mean a contract is not actually implemented. → **Mitigation**: the contracts were confirmed present in source during Step 2; recorded as UNK-01 (non-blocking). If a test asserts behavior the source does not implement, that is reported rather than worked around.

## Execution Status

Table structure and vocabulary: `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: cross-layer fixtures in `tests/integration/conftest.py` (REQ-006) | Completed | — | 20261124-082245 |  |
| 2 | Phase 2: cross-layer state-mapping matrix in `tests/integration/test_call_state_matrix_across_processes.py` (REQ-001, REQ-003, REQ-004) | Completed | — | 20261124-082245 |  |
| 3 | Phase 3: crash injection through the mapping and dedup gate in `tests/integration/test_call_state_crash_injection_across_processes.py` (REQ-002, REQ-005) | Completed | — | 20261124-082245 |  |
| 4 | Phase 4: validation of the three target files (no deploy step) | Completed | 2026-11-24T08:15 | 2026-11-24T08:20 | Batch-end validation: ruff format/check clean, mypy shows only the pre-existing conftest.py:75 baseline error, 5 consecutive integration runs (31 passed), full suite 13671 passed / 4 skipped, diff-cover N/A for test-only change. No production source changed, no deploy step. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261124-001146_01_tests_integration_conftest.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261124-001146_02_tests_integration_test_call_state_matrix_across_processes.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261124-001146_03_tests_integration_test_call_state_crash_injection_across_processes.py.md` | 3 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261123-234341
- **Related target files**: `tests/integration/conftest.py`, `tests/integration/test_call_state_matrix_across_processes.py`, `tests/integration/test_call_state_crash_injection_across_processes.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; mapping confirmed at `scripts/shared/mcp_call_state_contract.py:57-74`; no cross-process test found | `tests/integration/test_call_state_matrix_across_processes.py` | Phase 2 | AC-001 | One test per transition, cross-process | Confirmed by repository evidence |
| REQ-001 | Test harness required to cross the process boundary (existing fixtures inspected) | `tests/integration/conftest.py` | Phase 1 | AC-006 | Fixture smoke check through the integration run | Derived from confirmed evidence |
| REQ-002 | Required Changes; Unresolved Questions resolved by the kill pattern at `tests/integration/test_mcp_transport_crash.py:40-65` and `tests/shared/test_mcp_dedup_concurrency.py:316-336` | `tests/integration/test_call_state_crash_injection_across_processes.py` | Phase 3 | AC-004 | Seven crash-point tests | Confirmed by repository evidence |
| REQ-002 | Cross-layer fixtures for the killed process | `tests/integration/conftest.py` | Phase 1 | AC-006 | Fixture run in the integration suite | Derived from confirmed evidence |
| REQ-003 | Required Changes; Acceptance Criteria; existing single-process race coverage at `tests/shared/test_mcp_dedup_concurrency.py` | `tests/integration/test_call_state_matrix_across_processes.py` | Phase 2 | AC-002, AC-005 | Cross-process single-execution race | Confirmed by repository evidence |
| REQ-004 | Required Changes; fail-closed coverage exists only at unit level (`tests/mcp_servers/test_config_isolation_fail_closed.py`), cross-layer gap confirmed in Step 2 | `tests/integration/test_call_state_matrix_across_processes.py` | Phase 2 | AC-003 | Five boundary tests across the process boundary | Confirmed by repository evidence |
| REQ-005 | Required Changes; `scripts/agent/mcp_call_recovery.py:1-12` states recovery never re-executes; existing coverage is respx-mocked | `tests/integration/test_call_state_crash_injection_across_processes.py` | Phase 3 | AC-004 | Reconciliation-without-re-execution test | Confirmed by repository evidence |
| REQ-006 | Constraints; marker definition `pyproject.toml:146`; existing convention `tests/integration/test_standard_config_integration.py:50` | `tests/integration/conftest.py` | Phase 1 | AC-006 | Integration run and 5-run flakiness check | Confirmed by repository evidence |
| REQ-006 | Constraints | `tests/integration/test_call_state_matrix_across_processes.py` | Phase 2 | AC-006 | Marker and `tmp_path` isolation | Confirmed by repository evidence |
| REQ-006 | Constraints | `tests/integration/test_call_state_crash_injection_across_processes.py` | Phase 3 | AC-006 | Marker and `tmp_path` isolation | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261124-001146 -->