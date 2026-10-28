# Procedure: replace the set_health_registry assertion with a constructor assertion

## Goal

Assert that `ToolExecutor` is constructed with the health registry instead of `set_health_registry` being called (Plan REQ-005).

## Scope

- Modify only `tests/agent/test_agent_factory.py`.
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

`tests/agent/test_agent_factory.py`

### Procedure

- Replace `tool_executor_instance.set_health_registry.assert_called_once()` and the `call_args[0][0]` check with an assertion on the `ToolExecutor` mock's constructor call: `health_registry` is passed and is the same instance as `ctx.services.health_registry`.
- Keep `assert isinstance(ctx.services.health_registry, McpServerHealthRegistry)`.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Row 7 has landed. The test uses a mock `ToolExecutor`, so assert on `call_args.kwargs`, not on state the test assigned to the mock.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/agent/test_agent_factory.py -q` | Pass |
| 2 | `uv run ruff format tests/agent/test_agent_factory.py`; `uv run ruff check tests/agent/test_agent_factory.py` | No finding |

## Completion criteria

- The factory test asserts the constructor keyword and passes.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Completed | — | 20261028-180629 | Verified here. Replaced set_health_registry assertion with ToolExecutor constructor call_args.kwargs['health_registry'] check; kept isinstance check. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261028-180634 | ruff format+check clean; 43 tests pass. |

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
- **Requirement ID**: REQ-005 (factory passes the registry at construction)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: tests/agent/test_agent_factory.py