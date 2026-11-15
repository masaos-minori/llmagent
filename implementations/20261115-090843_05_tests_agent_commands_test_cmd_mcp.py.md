## Goal

Update `test_cmd_mcp.py`: replace the static-count assertion with registry-total assertions, and add a test for the typed fail-closed error when the registry is absent. (`REQ-005`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The existing `test_http_ok` (lines 102-117) asserts `"2 (from config/tools_definitions.toml)" in out`; this breaks once `cmd_mcp.py` derives the count from the registry (`REQ-002`), so it must be updated here.
- The `_Ctx` stub sets `services_required.runtime_tools = None` by default (line 41); give it a registry mock where a positive assertion is needed.

## Design decisions
- Drive counts through a `runtime_tools` mock whose `diagnostics()` returns a known set of rows, and assert the displayed LLM-visible/disabled/unavailable totals.
- Add a test that an absent registry makes `_stream_llm()` raise the typed fail-closed error (REQ-001) rather than falling back.

## Alternatives considered
- Testing only the `None` case: insufficient — the registry-derived path is the point of `REQ-002`/`REQ-005`.

## Implementation
### Target file
`tests/agent/commands/test_cmd_mcp.py`

### Procedure
1. In `test_http_ok`: attach a `runtime_tools` mock to `ctx` whose `diagnostics()` returns a known number of rows, and change the line-115 assertion to the registry-derived totals (drop the `from config/tools_definitions.toml` claim).
2. Add `test_tool_totals_from_registry` (new): build a `_Ctx`, attach a `runtime_tools` mock with N rows, call `_cmd_mcp_status()`, and assert the displayed LLM-visible / disabled / unavailable totals.
3. Add `test_absent_registry_fails_closed` (new): drive `LLMTurnRunner._stream_llm()` (or the relevant turn path) with `runtime_tools = None` and assert the typed configuration/wiring error is raised (not a fallback to `cfg.tool.tool_definitions`).

### Method
Locate `test_http_ok` (lines 102-117); set `ctx.services_required.runtime_tools = MagicMock(diagnostics=lambda: [{} for _ in range(N)])` before calling; assert on `capsys.readouterr().out`.

### Details
- `diagnostics()` contract: each dict has keys `name, server_key, config_dependent, enabled, disabled_reason, enabled_for_llm`; aggregate into totals. For the fail-closed test, reference the production change in `scripts/agent/llm_turn_runner.py` (`REQ-001`).
- Do not remove the other `_cmd_mcp_status` coverage (health/lifecycle/serialization sections).

## Compatibility considerations
Test-only change; aligns tests with the `cmd_mcp.py` (`REQ-002`) and `llm_turn_runner.py` (`REQ-001`) changes.

## Security considerations
None.

## Rollback considerations
Revert the commit.

## Validation plan
- Run `pytest tests/agent/commands/test_cmd_mcp.py` green after the change.
- Confirm no remaining assertion ties a count to `cfg.tool.tool_definitions`.

## Completion criteria
- `/mcp status` counts are asserted against registry totals; the static-count label is gone; an absent-registry fail-closed test exists.

## Out of Scope
- The `/help` count test (separate row, `REQ-003`).
- The `cmd_mcp.py` / `llm_turn_runner.py` production changes themselves.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: `REQ-005` — command tests must assert registry totals and the fail-closed error
- **Source issue**: `issues/20261111-163741_rtregistry001_runtime-registry-sole-authority.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-050235_rtregistry001_runtime-registry-sole-authority.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-090843
- **Related target files**: `tests/agent/commands/test_cmd_mcp.py`
