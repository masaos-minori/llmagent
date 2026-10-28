# Procedure: construct the crash-test executor with a health registry

## Goal

Pass a health registry to the `ToolExecutor(` construction used with the mocked process (Plan REQ-005).

## Scope

- Modify only `tests/integration/test_mcp_transport_crash.py`.
- Test-only change; no source file is edited.

## Assumptions

- The code procedures of this Plan with a lower `seq` have landed.
- Sequencing: the mcpcompat001, mcpinv002 and mcpinv004 implementation procedures (`implementations/20261028-013216_*` and `implementations/20261028-004831_*`) edit `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py` and the discovery side of the posture gate; re-read the current file before editing and keep whatever those procedures produced (UNK-01).
- Overlap (compatible): `plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md` also targets `tests/shared/test_runtime_tool_registry.py`; it only changes which builder the existing calls use.

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert observable behavior; use barriers or events, never sleeps.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/integration/test_mcp_transport_crash.py`

### Procedure

- In the test code around `_make_running_proc`, pass `health_registry=McpServerHealthRegistry()` to `ToolExecutor(...)` and import the type from `shared.mcp_health`.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Row 4 and 5 have landed.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/integration/test_mcp_transport_crash.py -m integration -q` | Pass |
| 2 | `uv run ruff format tests/integration/test_mcp_transport_crash.py`; `uv run ruff check tests/integration/test_mcp_transport_crash.py` | No finding |

## Completion criteria

- The construction passes a registry.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Completed | — | 20261028-181055 | Changes were NOT previously landed; applied here. Added 'from shared.mcp_health import McpServerHealthRegistry' and passed health_registry=McpServerHealthRegistry() to ToolExecutor in the d05 crash test. ruff clean; 5 tests pass (ran directly -m integration deselects all 5: file lacks the marker). |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261028-181101 | ruff format+check clean; 5 tests pass (run directly). |

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
- **Requirement ID**: REQ-005 (integration executor construction)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: tests/integration/test_mcp_transport_crash.py