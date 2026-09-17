## Goal

Repoint the 3 `unittest.mock.patch("agent.config_builders._build_mcp_servers", ...)` sites (`tests/agent/services/test_config_reload.py` lines 301, 725, 879) to patch the new module-level import location, and verify all tests that transitively depend on them still pass.

## Scope

- Repoint 3 mock-patch targets in `tests/agent/services/test_config_reload.py` to the new import location
- No other files are modified in this row

## Assumptions

- The 3 patch sites at L301, L725, L879: L301 feeds a `_run()` helper used by 6 test methods, L725/L879 feed `svc`/`svc_with_mocked_mcp` fixtures used by 5 test methods — 11 distinct tests total, not the Issue's claimed "7".
- After the module-level import move in `config_outcome_classification.py`, patches on `agent.config_builders._build_mcp_servers` no longer observe because the import location changed.
- The new patch target should be `config_outcome_classification._build_mcp_servers` (or the fully qualified path depending on how the import is structured).

## Design decisions

- Changing the patch target from `agent.config_builders._build_mcp_servers` to `config_outcome_classification._build_mcp_servers`: this reflects the new import location in the classification module.
- Running the full `test_config_reload.py` file (not just the 3 patched lines' immediate assertions) before considering REQ-006 complete: the blast radius extends beyond the 3 patch sites via shared helper/fixture functions.

## Alternatives considered

- Keeping the patch target as `agent.config_builders._build_mcp_servers` — rejected: after the module-level import move, this would no longer work because `config_outcome_classification.py` imports directly from `shared.mcp_config` instead.

## Implementation

### Target file

`tests/agent/services/test_config_reload.py`

### Procedure

Repoint the 3 `unittest.mock.patch` sites to the new import location.

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): Confirmed exact 3 sites at L301, L725, L879; L301 feeds a `_run()` helper used by 6 test methods, L725/L879 feed `svc`/`svc_with_mocked_mcp` fixtures used by 5 test methods — 11 distinct tests total, not the Issue's claimed "7".
2. Change the patch target at L301 from `"agent.config_builders._build_mcp_servers"` to `"config_outcome_classification._build_mcp_servers"`.
3. Change the patch target at L725 from `"agent.config_builders._build_mcp_servers"` to `"config_outcome_classification._build_mcp_servers"`.
4. Change the patch target at L879 from `"agent.config_builders._build_mcp_servers"` to `"config_outcome_classification._build_mcp_servers"`.
5. Verify all 11 dependent tests pass.

### Details

```python
# Line 301: change patch target
# Before:
with patch(
    "agent.config_builders._build_mcp_servers",
    return_value=new_mcp_servers,
):
    return svc._classify_mcp_server_changes(svc._ctx, {})

# After:
with patch(
    "config_outcome_classification._build_mcp_servers",
    return_value=new_mcp_servers,
):
    return svc._classify_mcp_server_changes(svc._ctx, {})

# Line 725: change patch target
# Before:
@patch("agent.config_builders._build_mcp_servers")
def fixture(svc_with_mocked_mcp, mock_build):
    ...

# After:
@patch("config_outcome_classification._build_mcp_servers")
def fixture(svc_with_mocked_mcp, mock_build):
    ...

# Line 879: change patch target
# Before:
@patch("agent.config_builders._build_mcp_servers")
def fixture(svc, mock_build):
    ...

# After:
@patch("config_outcome_classification._build_mcp_servers")
def fixture(svc, mock_build):
    ...
```

## Compatibility considerations

- The patch target change is backward compatible: the mocked function returns the same value regardless of which module it's patched against.
- All 11 dependent tests must be verified to pass after the change.

## Security considerations

- No security impact. This is updating test mocks to reflect the new import location.

## Rollback considerations

- Reverting this change restores the original patch targets pointing to `agent.config_builders._build_mcp_servers`. If needed later, the fields should be reimplemented to match the canonical exclude-and-FATAL duplicate-ownership policy from `McpToolDiscoveryService._dedupe_and_build()`.

## Validation plan

- Unit: run `uv run pytest tests/agent/services/test_config_reload*.py tests/agent/commands/test_agent_cmd_config.py -q` to confirm all existing + new tests pass; the 11 tests depending on the repointed patches pass (REQ-006, REQ-007).
- Static analysis: `uv run ruff check tests/agent/services/test_config_reload.py`, `uv run mypy tests/agent/services/test_config_reload.py`.
- Import lint: `PYTHONPATH=scripts uv run lint-imports` to confirm no broken contracts introduced.

## Completion criteria

- All 3 `unittest.mock.patch` sites are repointed and all 11 dependent tests pass (REQ-006).
- `ConfigReloadService.__init__` still accepts only `AgentContext` (REQ-007).
- No new lint/type errors introduced.

## Out of scope

- Changes to `scripts/agent/services/config_reload.py` — covered by separate row (REQ-001–REQ-007).
- Changes to `scripts/agent/services/config_field_registry.py` — covered by separate row (REQ-001).
- Changes to `scripts/agent/services/config_section_reload.py` — covered by separate row (REQ-002).
- Changes to `scripts/agent/services/config_service_sync.py` — covered by separate row (REQ-003).
- Changes to `scripts/agent/services/config_outcome_classification.py` — covered by separate row (REQ-004, REQ-005).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Repoint patch at L301 | Pending | — | — | |
| 2 | Repoint patch at L725 | Pending | — | — | |
| 3 | Repoint patch at L879 | Pending | — | — | |
| 4 | Verify 11 dependent tests pass | Pending | — | — | |
| 5 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260915-101458_refactor_config_reload_module_split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-135937_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-235003
- **Related target files**: tests/agent/services/test_config_reload.py
