# Procedure: build the health registry before the executor

## Goal

Create `McpServerHealthRegistry` first and pass it to `ToolExecutor` instead of attaching it afterwards (Plan REQ-005).

## Scope

- Modify only `scripts/agent/factory.py`.
- In scope: `_build_tool_executor`.
- Out of scope: the lifecycle router, other builders, tests.

## Assumptions

- Row 4 has landed, so `ToolExecutor` requires `health_registry`.
- `_build_tool_executor` is the only production constructor of `ToolExecutor`.
- Sequencing: the mcpcompat001, mcpinv002 and mcpinv004 implementation procedures (`implementations/20261028-013216_*` and `implementations/20261028-004831_*`) edit `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py` and the discovery side of the posture gate; re-read the current file before editing and keep whatever those procedures produced (UNK-01).
- Overlap (compatible): `plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md` also targets `tests/shared/test_runtime_tool_registry.py`; it only changes which builder the existing calls use.

## Design decisions

- Keep the returned `ToolExecutorResult` fields unchanged.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/agent/factory.py`

### Procedure

- Move `registry = McpServerHealthRegistry()` above the `ToolExecutor(...)` call and pass `health_registry=registry`.
- Delete `tools.set_health_registry(registry)`.

### Method

Reorder two statements and add one keyword argument.

### Details

- `tests/agent/test_agent_factory.py` asserts the old setter call; row 18 updates it.

## Compatibility considerations

- No behavior change at runtime: the same registry instance reaches the executor.

## Security considerations

- No security impact.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/agent/test_agent_factory.py -q` | Pass |
| 2 | `uv run ruff format scripts/agent/factory.py`; `uv run ruff check scripts/agent/factory.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/agent/factory.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- `factory.py` contains no `set_health_registry` call and builds the registry before the executor.

## Out of Scope

- Other factory functions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-10-28 | 2026-10-28 | — |
| 2 | Add or update tests per Validation plan | Completed | 2026-10-28 | 2026-10-28 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-28 | 2026-10-28 | Static green. Factory test (old setter assertion) deferred to procedure 18. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-10-28 | 2026-10-28 | — |

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
- **Requirement ID**: REQ-005 (single production construction passes the registry)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: scripts/agent/factory.py
