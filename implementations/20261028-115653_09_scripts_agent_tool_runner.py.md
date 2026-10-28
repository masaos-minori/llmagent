# Procedure: align the tool_runner comments with the routing result contract

## Goal

Update the comments that say an unregistered tool raises `ValueError` and mention `strict_mode` wording (Plan REQ-006).

## Scope

- Modify only `scripts/agent/tool_runner.py`.
- In scope: the docstring and inline note of `_execute_prepared_call`.
- Out of scope: logic, tests.

## Assumptions

- After row 4, `ToolExecutor.execute()` returns a `routing` result for an unregistered tool instead of raising, so the gateway-bypass justification must name the result.
- Sequencing: the mcpcompat001, mcpinv002 and mcpinv004 implementation procedures (`implementations/20261028-013216_*` and `implementations/20261028-004831_*`) edit `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py` and the discovery side of the posture gate; re-read the current file before editing and keep whatever those procedures produced (UNK-01).
- Overlap (compatible): `plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md` also targets `tests/shared/test_runtime_tool_registry.py`; it only changes which builder the existing calls use.

## Design decisions

- Comment-only change.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/agent/tool_runner.py`

### Procedure

- Rewrite the docstring sentence to: a tool name that is not in the RuntimeToolRegistry yields a `routing` `ToolCallResult` from `ToolExecutor.execute()` and cannot execute.
- Delete the inline `NOTE: strict_mode behavior` lines.

### Method

Edit comments only.

### Details

- The per-call boundary `_recorded_call` still catches unexpected exceptions.

## Compatibility considerations

- No behavior change.

## Security considerations

- No security impact; the safety argument (an unregistered tool cannot execute) is preserved.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/agent -k tool_runner -q` | Pass |
| 2 | `uv run ruff format scripts/agent/tool_runner.py`; `uv run ruff check scripts/agent/tool_runner.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/agent/tool_runner.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- No comment mentions `strict_mode` or says the resolver raises for an unregistered tool in this file.

## Out of Scope

- Logic changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-10-28 | 2026-10-28 | — |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-28 | 2026-10-28 | Comment-only. Static green. tool_runner tests deferred to procedure 19. |

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
- **Requirement ID**: REQ-006 (stale comments)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: scripts/agent/tool_runner.py
