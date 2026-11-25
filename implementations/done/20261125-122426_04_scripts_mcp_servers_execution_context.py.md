## Goal

Create the typed MCP-side execution context and its builder (REQ-002), plus the preview-capability injection seam the builder reads.

## Scope
**Release unit**: R1-mode-contract

## Assumptions

- The preview-capability map is injected at the `run_http` bootstrap seam beside the retry-policy map; an unconfigured map resolves every call to `applied` (Plan Assumptions, safe direction).
- The module does not import `mcp_servers.server` or `mcp_servers.dispatch`; both import it, so there is no cycle.
- Code docstrings and comments must not carry REQ markers (the repository checks that); cite behavior, not Plan ids.

## Design decisions

- `ExecutionContext` (new) is a frozen dataclass with `request_id`, `session_id`, `idempotency_key`, `execution_mode`: the four fields the Issue names, nothing else.
- The preview-capable set is module state set by `configure_tool_preview_capabilities` (new), mirroring `configure_tool_retry_policies`; entries without a name are skipped.

## Alternatives considered

Passing the capability map into every `dispatch_tool` call was rejected: eleven entry points would each need the map, while the existing seam pattern already injects per-process declarations once.

## Implementation
### Target file
`scripts/mcp_servers/execution_context.py` (new)

### Procedure
Create the module with the context type, the error type, the seam, and two builders.

### Method
- Define ExecutionContext as a frozen dataclass of the four fields; the key is stored stripped of surrounding whitespace.
- Define `ExecutionContextError` (new) as a `ValueError` subclass.
- Define configure_tool_preview_capabilities taking `(entries)` that records the names whose entry has `preview_capability == "dry_run"`.
- Define `build_execution_context` (new) taking `(tool, args, session_id, request_id, idempotency_key, header_mode)`: resolve the mode with `resolve_execution_mode(tool, args, tool in capable set)`; a non-empty `header_mode` (new) that is not in `{"preview", "applied"}` or differs from the resolved mode raises ExecutionContextError; a `ValueError` from the resolver is re-raised as ExecutionContextError.
- Define `ExecutionContext.for_programmatic_call` (new) classmethod `(tool, args, idempotency_key="")` that builds a context with empty request and session ids and the resolved mode.

### Details
- Module docstring first line: `scripts/mcp_servers/execution_context.py — ...`.
- The error text names the tool and the disagreement, never argument values.
- The capable set is replaced wholesale on each configure call so a test can reset it with an empty iterable.

### Companion test files
- `tests/mcp_servers/test_execution_context.py` (new)
  - Procedure: Add cases: builder with and without a header; header disagreement and unknown header raise; non-bool `dry_run` on a capable tool raises; unconfigured map resolves `applied`; configure with an empty iterable resets.
  - Validation: `uv run pytest tests/mcp_servers/test_execution_context.py`

## Compatibility considerations

New module and new public names; nothing imports it until the dispatcher and server procedures land in the same release unit.

## Security considerations

Header and argument values are never echoed; the key is carried but not logged here.

## Rollback considerations

Delete the module and its test before the dependent procedures land; after that, revert the whole release unit together.

## Validation plan

- `uv run pytest tests/mcp_servers/test_execution_context.py`
- `uv run mypy scripts/mcp_servers/execution_context.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- The four names exist and the builder enforces the header cross-check.
- The companion test passes.

## Out of Scope

- Calling the builder from servers (server procedures).
- Calling configure_tool_preview_capabilities at bootstrap (server.py procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-170308 | 20261125-170308 | changed: scripts/mcp_servers/execution_context.py, tests/mcp_servers/test_execution_context.py; stale check clean |
| 2 | Add the companion test per Validation plan | Completed | 20261125-170308 | 20261125-170308 | 13 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-180342 | 20261125-180342 | — release unit R1-mode-contract: end-of-unit full-suite run pending; Step 5 N/A: docs work is the plan row docs/22_mcp/mcp_03_01_dispatch-and-routing.md, not this procedure end-of-batch full-suite run: 14369 passed, 4 skipped; diff-cover 92% (>=90) on changed lines; run_validation_gates.py passes |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `scripts/mcp_servers/execution_context.py`, `tests/mcp_servers/test_execution_context.py`