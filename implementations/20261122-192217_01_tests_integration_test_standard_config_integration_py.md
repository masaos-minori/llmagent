## Goal

End-to-end coverage against the real reduced `config/agent.toml` (REQ-001 - startup-path integration verification), closing the gap that current real-file coverage is unit-level single-point checks only.

## Scope
**Release unit**: N/A: not part of a release unit

One file is modified: the new integration test module. `config/agent.toml`, `config/rag_pipeline_mcp_server.toml`, and `config/tool_catalog.toml` are read as references, not modified.

## Assumptions
- `config/agent.toml` stays as it is today and already passes strict validation (falsifiable by re-running `tests/shared/test_config_validator.py` line 173 before this file is executed).
- The tests do not touch `/opt/llm` (issue constraint).
- The mcpdl003 overlap on shared files does not affect this row; no sequencing dependency.

## Design decisions
- Follow the existing `tests/integration/` pattern (`tests/integration/test_production_security_regression.py` shows the fixture shape) and carry the `integration` marker.
- Load the real files through the normal startup path (`ConfigLoader.load_all()` / `load_config()`) so the startup path itself is exercised, not a hand-built config dict.

## Alternatives considered
Extending the existing real-file unit tests was rejected: AC-1 requires re-assertion through the startup path, which unit single-point checks do not cover.

## Compatibility considerations
The module asserts error classes and behavior outcomes, not exact message text, so the corrected design D3 message format (sibling procedure seq 02) does not affect it.

## Security considerations
N/A: offline test only; no production connection.

## Rollback considerations
N/A: delete the new test module.

## Implementation
### Target file
`tests/integration/test_standard_config_integration.py` (new)
### Procedure
1. Cover startup validation against the real `config/agent.toml` (AC-1).
2. Cover MCP discovery and the RAG Pipeline MCP starting from `config/rag_pipeline_mcp_server.toml` (AC-2).
3. Cover approval, plan mode, reload, Memory, and database maintenance paths against the real files.
### Method
Test functions load the real config files through the standard loader with the `integration` marker; required-capability checks read `config/tool_catalog.toml` as the ownership source (AC-5).
### Details
- The file must read the real `config/` files, not fixtures; fixtures are used only for the runtime objects the existing integration tests already construct via `tests/integration/conftest.py`.

## Validation plan
- `uv run pytest tests/integration/test_standard_config_integration.py -m integration`
- Full `rules/toolchain.md` sequence; the module runs in CI via the full pytest job.

## Completion criteria
All startup/discovery/approval/plan-mode/reload/Memory/maintenance tests pass against the real files, re-asserting AC-1 and AC-2 through the startup path.

## Out of Scope
No source, config, or documentation changes; existing unit-level real-file tests stay as the baseline.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test module per Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) and the module | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (real-file startup-path integration coverage)
- **Source issue**: `issues/20261120-114214_agentcfg006_reduction-integration-verification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-190238_agentcfg006_reduction-integration-verification.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192217
- **Related target files**: `tests/integration/test_standard_config_integration.py`
