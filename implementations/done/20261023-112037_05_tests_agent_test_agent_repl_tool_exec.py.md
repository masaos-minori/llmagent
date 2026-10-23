## Goal

Migrate the three DAG-evaluation call sites in `tests/agent/test_agent_repl_tool_exec.py`
to pass a real `ToolLoopGuard`, so they keep exercising `execute_all_tool_calls` after its
parameter becomes required (`REQ-007`, `AC-1`).

## Scope

Only `tests/agent/test_agent_repl_tool_exec.py`. Three edits: add `guard=<real
ToolLoopGuard>` to the direct `execute_all_tool_calls` calls at `:417`, `:461`, `:504`
(`await execute_all_tool_calls(ctx, [...], turn=1)`). These tests patch
`agent.tool_runner.execute_one_tool_call`, so recording (which lives inside that function,
`tool_runner.py` row 1) is outside their scope — assert nothing about recorded counts here.

Reference reads only: the existing DAG-evaluation fixtures these tests already build.

## Assumptions

- The three direct calls are the only `execute_all_tool_calls` call sites in this file
  (verified at `:417`, `:461`, `:504`); other references are patch targets or comments.
- A real `ToolLoopGuard` can be constructed the same way `tests/agent/test_tool_loop_guard.py`
  does.

## Design decisions

- **Pass a real guard by keyword** even though `execute_one_tool_call` is patched: the entry
  point still requires the parameter, and supplying a real instance keeps the test honest
  without adding a recording assertion it cannot observe.

## Alternatives considered

- Mocking the guard — rejected by `REQ-007`: the batch-ordering proof needs the real entry
  point to run; a mocked guard would not exercise ordering.

## Implementation

### Target file

`tests/agent/test_agent_repl_tool_exec.py`

### Procedure

Add `guard=<real ToolLoopGuard>` as a keyword argument to each of the three
`await execute_all_tool_calls(...)` calls at `:417`, `:461`, `:504`.

### Method

Construct one `ToolLoopGuard` in each test (reuse the unit-suite construction pattern) and
insert `, guard=my_guard` before the closing paren of each call. mypy flags any site still
missing it.

### Details

- Do not add recording assertions: these tests patch `execute_one_tool_call`, so no result is
  ever recorded through the unmocked path.
- Keep the DAG-evaluation assertions (batch ordering) unchanged.

## Compatibility considerations

### Corrections found while implementing

- The three call sites were migrated with a module-level `ToolLoopGuard` import; the three `fake_execute_one(ctx, pc)` stubs patched over `execute_one_tool_call` needed the new `guard` parameter too (not listed in the procedure).


- The three migrated calls must each supply a real guard; mypy is the completeness check.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run mypy --no-namespace-packages tests/` reports zero missing-`guard` sites.
- `uv run pytest tests/agent/test_agent_repl_tool_exec.py -q` — the three DAG-evaluation
  cases pass, proving batch ordering still works with the explicit parameter.
- `uv run pytest tests/agent -q` — full suite green.

## Completion criteria

All three `execute_all_tool_calls` calls pass a real guard; mypy is clean; the three
DAG-evaluation cases pass.

## Out of Scope

- The other `tests/agent/test_tool_runner.py` migrations (row 4) and the two
  `tests/agent/test_tool_approval_preflight.py` sites (row 6).
- Production threading/recording (rows 1-2), the docstring (row 3), the new wiring module
  (row 7), reference regeneration (row 8).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate the 3 DAG-evaluation `execute_all_tool_calls` calls (:417, :461, :504) | Completed | 20261023-163753 | 20261023-163753 | REQ-007; patch execute_one_tool_call, so no recording assertion implemented; full suite 9909 passed |
| 2 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-163753 | 20261023-163753 | mypy clean; DAG cases green |

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
- **Requirement ID**: `REQ-007`
- **Source issue**: `issues/20261021-093421_tool001_empty-result-loop-guard-is-never-wired.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-092413_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-112037
- **Related target files**: `tests/agent/test_agent_repl_tool_exec.py`