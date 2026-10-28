## Goal

Update the `concurrency_limits` parameter description in `ToolExecutor.__init__`
where "If None, no concurrency limiting is applied" is no longer true after the
per-server default cap (`REQ-004`, `REQ-006`).

## Scope

Modifies only the `concurrency_limits` docstring in `scripts/shared/tool_executor.py`
`ToolExecutor.__init__` (lines 54-56). No code, signature, or behavior change.

## Assumptions

- This edit is disjoint from the `mcpinv002` Plan's edits to the same file
  (`_check_startup_mode` deletion at lines 68-79 and the redundant
  `self._server_configs` assignment at line 60); both Plans record the overlap as
  Compatible and the second implementer rebases.
- After this Plan, `concurrency_limits=None` means every configured server falls
  back to the seq-01 constant DEFAULT_PER_SERVER_CONCURRENCY (defined in
  `scripts/shared/tool_transport_invoker.py`, so it exists by the time
  code-implementation executes the rows in order); the constant is referenced here
  only as the bounded default, and an explicit `0`/negative per-key value still
  opts out (unlimited).

## Design decisions

- Keep the existing "fixed at initialization time" sentence intact; only correct
  the now-false "no concurrency limiting is applied" clause.

## Alternatives considered

- Rewriting the whole `Args` block: rejected — only the `concurrency_limits` clause
  is stale; minimal edit preserves the rest.

## Implementation
### Target file

`scripts/shared/tool_executor.py`

### Procedure

1. Replace the `concurrency_limits` clause in `ToolExecutor.__init__`'s docstring
   (currently lines 54-56):

   ```python
               concurrency_limits: Optional concurrency limits per server. A
                   configured positive value caps that server; a server with no
                   positive limit falls back to the process-wide
                   DEFAULT_PER_SERVER_CONCURRENCY. An explicit 0/negative value
                   opts out (unlimited). Note: this value is fixed at
                   initialization time and cannot be changed later.
   ```

### Method

A single docstring-clause replacement inside `__init__`. No runtime path changes,
so no test or static-contract edit is required beyond the standard toolchain run.

### Details

- The old clause read "If None, no concurrency limiting is applied." The rewritten
  clause states the bounded default and the preserved `0`/negative opt-out, matching
  the new `_ensure_semaphores()` behavior in `tool_transport_invoker.py`.

## Compatibility considerations

- Docstring-only: no existing test asserts on this text, so the full suite passes
  unmodified.
- Disjoint from `mcpinv002`'s dead-method deletion in the same file.

## Security considerations

N/A: docstring text only; no behavior change.

## Rollback considerations

Revert the commit; the change is one docstring clause.

## Validation plan

- Static + contract: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages
  scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`,
  `PYTHONPATH=scripts uv run lint-imports`.
- Regression: `uv run pytest tests/shared/test_tool_executor*.py`.
- Full suite: `uv run pytest tests/`.

## Completion criteria

- `ToolExecutor.__init__`'s `concurrency_limits` docstring no longer claims "no
  concurrency limiting is applied"; it states the bounded default and the
  preserved `0`/negative opt-out (`REQ-004`).
- No other text in the repo states that an unconfigured server is unlimited
  (`REQ-006`).

## Out of Scope

- Any change to `tool_transport_invoker.py` (constant + `_ensure_semaphores()`,
  covered by a separate row).
- The two `docs/23_agent` concurrency updates (covered by separate rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261028-102436 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261028-102436 | docstring-only; no test edit |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261028-102436 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261028-102436 |  |

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
- **Requirement ID**: `REQ-004` (update the `concurrency_limits` docstring to state the default ceiling and opt-out), `REQ-006` (no text still says an unconfigured server is unlimited)
- **Source issue**: issues/20261027-001921_mcpinv004_unbounded-per-server-concurrency-default.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-104612_mcpinv004_unbounded-per-server-concurrency-default.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-004831
- **Related target files**: scripts/shared/tool_executor.py