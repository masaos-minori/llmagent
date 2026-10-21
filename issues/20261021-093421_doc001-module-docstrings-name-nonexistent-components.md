# Module docstrings and helper comments describe components that no longer exist

## Priority
Low

## Summary
Correct the stale module-level claims in `scripts/agent/repl.py` and `scripts/shared/tool_executor_helpers.py`
so that a reader following the docstring reaches code that exists.

## Background
Module docstrings are the first architecture description a new reader sees, and these two are the entry
points for the REPL and tool paths.

## Problem
- `scripts/agent/repl.py:15` lists `ToolExecutor — MCP routing, error handling, TTL cache
  (shared/tool_executor.py)`. There is no cache or TTL in that module (`grep -n 'cache|ttl'
  scripts/shared/tool_executor.py` matches nothing). The idempotency cache with TTL and eviction exists only
  server-side in `scripts/mcp_servers/dispatch.py:93`, `:113-130` (`_duplicate_cache`,
  `_IDEMPOTENCY_CACHE_TTL_SECONDS`), which `docs/22_mcp/mcp_03_01_dispatch-and-routing.md:58-70` documents
  correctly.
- `repl.py:19` names `AgentConfig — mutable runtime config dataclass (agent/config.py)`;
  `scripts/agent/config.py` does not exist (verified: `ls` reports no such file). The config dataclasses live
  in `scripts/agent/config_dataclasses.py`.
- `repl.py:21` states "Imported by agent.py as the entry point"; `scripts/agent.py` does not exist. The real
  entry point is `agent.repl:main()` (`repl.py:170-172`), which is what the deployed Nuitka binary
  `/opt/llm/bin/agent` is built from. Running `python scripts/agent/repl.py` directly fails with
  `ModuleNotFoundError: No module named 'agent'`.
- `scripts/shared/tool_executor_helpers.py:41` states "Cache keys use plain string concatenation:
  f'{name}:{json_dumps(args)}'". No such cache key is constructed anywhere in `scripts/shared/`.
- The same block of `repl.py` also declares attributes nothing uses: `_turn_active` (`:81`; the live flag is
  `ReplInputLoop._turn_active`), `_input_coro` (`:83`; tests use `repl._input_loop._input_coro`), `_prompt`
  (`:94-97`), `_n_tools` (`:99-103`, no reference anywhere under `scripts/` or `tests/`), and
  `_REPL_RESERVED_COMMANDS` (`:42`), which is only reachable through `reserved_repl_command_names()`
  (`:52-54`). `_spawned_subprocesses` (`:123`, `:132`) is handled in `shutdown003`.

## Reason for Change
These claims are how a new contributor locates the config dataclass, the entry point, and the tool cache. Each
of the three pointers currently leads to a file that does not exist, and the unused attributes make it
ambiguous which object owns the live state (`ReplInputLoop` does).

## Implementation Intent
Make module-level descriptions point at real files and real owners, and delete declared-but-unused state from
the composition facade.

## Target Files or Areas
- `scripts/agent/repl.py` (module docstring, `__init__`, unused properties)
- `scripts/shared/tool_executor_helpers.py` (comment at `:41`)

## Required Changes
- Update the `repl.py` architecture list to the actual modules and remove claims about a nonexistent cache and
  `agent/config.py` / `agent.py`.
- State the real entry point (`agent.repl:main`, packaged as `/opt/llm/bin/agent`).
- Remove `_turn_active`, `_input_coro`, `_prompt`, `_n_tools` from `AgentREPL` if nothing reads them, or give
  them a real owner; keep `reserved_repl_command_names()`/`completion_command_names()` as the documented
  public helpers they are.
- Correct or delete the cache-key comment in `tool_executor_helpers.py:41`.

## Constraints
- Do not change behavior: this issue must not alter runtime paths.
- `SLASH_COMMANDS`, `builtin_command_names()`, `reserved_repl_command_names()`,
  `completion_command_names()` are public helpers; keep their behavior unless a test proves they are unused.
- Any attribute removal must be checked against `tests/agent/test_repl.py` first.

## Acceptance Criteria
- Every file path named in a module docstring exists.
- No `AgentREPL` attribute remains that nothing in `scripts/` or `tests/` reads.
- A grep for "TTL cache" in `scripts/agent/repl.py` and "Cache keys" in `scripts/shared/` returns nothing.

## Testing Expectations
- Documentation-and-comment-only change plus attribute removals: run `uv run pytest tests/agent -q` to confirm
  no test depends on a removed attribute, then `uv run ruff check scripts/agent` and
  `uv run mypy --no-namespace-packages scripts/agent`.
- No new test is required for the docstring text itself.

## Documentation Impact
This issue changes in-code documentation only. If `docs/23_agent/` names any of the removed components, update
those sections in the same change; verify against `docs/00_index.md`'s scope mapping before editing.

## Out of Scope
- Using `_spawned_subprocesses` at the REPL level (`shutdown003`).
- Adding a tool-result cache to `ToolExecutor` (no such feature is proposed).
- `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`, which already documents the server-side cache correctly.

## Dependencies
- Independent. `repl003` and `shutdown002` touch the same file; sequence this one last to avoid churn.

## Unresolved Questions
- Is `AgentREPL._turn_active` kept intentionally as a public surface for tests or tooling? Needs confirmation
  before deletion.

## AI Implementation Instruction
Verify each named path exists before writing it. Delete unused state rather than documenting it.

## Traceability
- **Workflow phase**: `python-code-review` (REPL core-loop review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/repl.py`, `scripts/shared/tool_executor_helpers.py`
