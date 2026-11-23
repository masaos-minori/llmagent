## Goal

Add the missing automated test for ADR-003 INV-07: tools of a Circuit-Open MCP server stay in `llm_tool_definitions()` and keep `enabled_for_llm` (AAL-035).

## Scope
**Release unit**: N/A: not part of a release unit

Test-only change in one existing file. No production change.

## Assumptions

- `RuntimeToolRegistry.llm_tool_definitions` filters only on `enabled_for_llm` (`scripts/shared/runtime_tool_registry.py:152`, re-read in Step 3a).
- `McpServerHealthRegistry(failure_threshold=1)` turns a server UNAVAILABLE on its first `record_failure` (`scripts/shared/mcp_health.py:51`).

## Design decisions

- A new test class `TestCircuitOpenKeepsLlmVisibility` (new) in the same file, using the existing helpers `_make_executor`, `_http_cfg`, and `_runtime_registry_for`.
- The test asserts visibility from the registry, not from the executor, so it fails if any health-driven path writes `enabled_for_llm`.

## Alternatives considered

Test through a full Agent startup: rejected, it needs discovery and ports for no extra coverage of INV-07.

## Implementation
### Target file
`tests/shared/test_tool_executor_routing.py`

### Procedure
1. Read `TestToolExecutorHealthGate` in the same file for the existing health-gate pattern.
2. Build a registry with `_runtime_registry_for` and an executor with `_make_executor(health_registry=registry)`.
3. Record the tool list and each tool's `enabled_for_llm` before any failure.
4. Call `record_failure(server_key)` until UNAVAILABLE, then re-read the tool list and flags; also after the cooldown opens HALF_OPEN.
5. Assert the list and flags are equal, the tool still resolves, and `_raw_execute` returns an unavailable error without a transport call.

### Method
- Use `time.monotonic` patching or `half_open_cooldown_sec=0.0` to reach HALF_OPEN without sleeping.
- Compare `llm_tool_definitions()` output by value before and after.

### Details
- Cite the new class in ADR-003's INV-07 row in procedure 07 as `tests/shared/test_tool_executor_routing.py::TestCircuitOpenKeepsLlmVisibility`.
- Mutation check: make the health gate set `enabled_for_llm=False` for an UNAVAILABLE server, confirm the test fails, revert.

## Compatibility considerations

N/A: adds a test only; no production behavior changes.

## Security considerations

N/A: no secret, permission, or input handling is touched; test fixtures use dummy tokens only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_tool_executor_routing.py -q`
- `uv run ruff check tests/shared/test_tool_executor_routing.py`, `uv run ruff format --check`, `uv run mypy` on it

## Completion criteria

- The class passes on current code and fails under the mutation.
- No file other than the target changed.

## Out of Scope

- Any file other than the target file (and its companions, if any); any change under `scripts/` or `config/`.
- Approval text: no approver, date, or approval sentence is written.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Mutation-check the new test: break the invariant temporarily, confirm the test fails, revert the break | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (Circuit-Open tools stay visible to the LLM (ADR-003 INV-07)), `REQ-008` (no production change, every test mutation-checked)
- **Source issue**: issues/20261123-164658_gov006_restore-blocking-verification-rows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-165432_gov006_restore-blocking-verification-rows.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-165833
- **Related target files**: `tests/shared/test_tool_executor_routing.py`
