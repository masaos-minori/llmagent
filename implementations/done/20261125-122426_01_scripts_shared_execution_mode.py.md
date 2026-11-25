## Goal

Create the one shared execution-mode contract (REQ-001: vocabulary and resolver) that the Agent and every MCP server import, so the mode is decided by the same rule on both sides.

## Scope
**Release unit**: R1-mode-contract

## Assumptions

- `scripts/shared/` is an import-linter leaf: the module imports only the standard library, so Agent and MCP code can both import it.
- `PreviewCapability` and its closed vocabulary already exist in `shared/tool_metadata.py` and are not changed; this module takes a plain `bool` (capable or not) instead of importing it.
- Code docstrings and comments must not carry REQ markers (the repository checks that); cite behavior, not Plan ids.

## Design decisions

- The resolver is pure and total over its inputs: it raises only for a malformed `dry_run` on a preview-capable tool, so a caller never has to catch I/O errors.
- no_op belongs to the vocabulary but is never returned by the resolver: it is a dispatcher outcome (no handler ran), not an input-derived mode.

## Alternatives considered

Reading the declared capability inside the resolver (importing `shared.tool_metadata`) was rejected: the Agent reads it from `RuntimeTool` and the MCP side from its tool table, so each caller passes the answer in and the module stays dependency-free.

## Implementation
### Target file
`scripts/shared/execution_mode.py` (new)

### Procedure
Create the module with the type, the closed value set, and the resolver.

### Method
- Define `ExecutionMode` (new) as `Literal["preview", "applied", "no_op"]` and `EXECUTION_MODES` (new) as the matching `frozenset[str]`.
- Define `resolve_execution_mode` (new) taking `(tool: str, args: Mapping[str, object], preview_capable: bool) -> ExecutionMode`.
- Return `"preview"` only when `preview_capable` (new) is true and `args.get("dry_run") is True`; otherwise return `"applied"`.
- When preview_capable is true and `dry_run` is present but not a `bool` (for example `"true"` or `1`), raise `ValueError` naming the tool and the offending type only, never the value.

### Details
- Module docstring first line: `scripts/shared/execution_mode.py — ...` (the docstring-format gate is baseline-gated).
- A tool that is not preview-capable never previews: `dry_run` stays an ordinary argument and is left to argument validation (Plan UNK-04).
- Keep the function free of logging and global state.

### Companion test files
- `tests/shared/test_execution_mode.py` (new)
  - Procedure: Add a parametrized table: capable plus `True` is preview; capable plus `False`, missing, `None` is applied; non-capable plus `True` is applied; capable plus `"true"`, `1`, `0` raises `ValueError` without echoing the value.
  - Validation: `uv run pytest tests/shared/test_execution_mode.py`

## Compatibility considerations

New module and new public names only; no existing import changes.

## Security considerations

The error text names the tool and the type, not the argument value, because arguments can carry secrets.

## Rollback considerations

Delete the module and its test; nothing else imports it until later procedures of this Plan land.

## Validation plan

- `uv run pytest tests/shared/test_execution_mode.py`
- `uv run ruff format` and `uv run ruff check` on both files
- `uv run mypy scripts/shared/execution_mode.py`
- `uv run python tools/run_validation_gates.py` (module docstring and size gates)

## Completion criteria

- The module exposes the three names above and imports only the standard library.
- The resolver table test passes, including the non-bool rejection.

## Out of Scope

- Reading `PreviewCapability` or any tool table.
- Dispatcher, header, and Agent wiring (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-165434 | 20261125-165950 | changed: `scripts/shared/execution_mode.py`, `tests/shared/test_execution_mode.py` |
| 2 | Add the companion test per Validation plan | Completed | 20261125-165434 | 20261125-165434 | tests/shared/test_execution_mode.py added, 13 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-180342 | 20261125-180342 | — release unit R1-mode-contract: end-of-unit full-suite run pending Step 5 N/A: docs work is the plan row docs/22_mcp/mcp_03_01_dispatch-and-routing.md, not this procedure end-of-batch full-suite run: 14369 passed, 4 skipped; diff-cover 92% (>=90) on changed lines; run_validation_gates.py passes |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `scripts/shared/execution_mode.py`, `tests/shared/test_execution_mode.py`