## Goal

Migrate the two direct `execute_one_tool_call` call sites in
`tests/agent/test_tool_approval_preflight.py` to pass a real `ToolLoopGuard`, so they keep
running the unmocked entry point after its parameter becomes required (`REQ-007`, `AC-1`).

## Scope

Only `tests/agent/test_tool_approval_preflight.py`. Two edits: add `guard=<real
ToolLoopGuard>` to the direct `execute_one_tool_call` calls. At current HEAD these are at
`:721` (`tc_id, name, args, ... = await execute_one_tool_call(...)`) and `:754`
(`await execute_one_tool_call(ctx, pc)`). NOTE: the frozen plan cited `:678`/`:711`; the
calls have shifted ~43 lines due to repo evolution since freeze — enumerate via mypy rather
than trust the frozen numbers.

Reference reads only: the import of `execute_one_tool_call` at the top of the file.

## Assumptions

- Exactly two direct calls exist in this file (verified at `:721`, `:754`); other references
  are the docstring mention (`:6`) or a section header comment (`:697`).
- A real `ToolLoopGuard` can be constructed the same way `tests/agent/test_tool_loop_guard.py`
  does.

## Design decisions

- **Pass a real guard by keyword** so the approval-preflight path exercises the true entry
  point; a mocked guard would hide the wiring again (`REQ-007`).

## Alternatives considered

- Patching `agent.tool_runner.execute_one_tool_call` — rejected by `REQ-007`: preflight must
  run the real function to prove the parameter threads through approval.

## Implementation

### Target file

`tests/agent/test_tool_approval_preflight.py`

### Procedure

Add `guard=<real ToolLoopGuard>` as a keyword argument to each of the two direct
`execute_one_tool_call` calls.

### Method

Construct one `ToolLoopGuard` per test and insert `, guard=my_guard` before each closing
paren. mypy flags any site still missing it — the completeness check.

### Details

- Do not change the approval-preflight assertions; only add the parameter.
- Enumerate the current call sites with `rg -n 'execute_one_tool_call\('` / mypy; the frozen
  plan line numbers (`:678`/`:711`) are stale.

## Compatibility considerations

### Corrections found while implementing

- Both direct `execute_one_tool_call` call sites migrated. `tests/integration/test_rag_turn_integration.py` only patches the function, so it needed no change.


- Both migrated calls must supply a real guard; mypy is the safety net.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run mypy --no-namespace-packages tests/` reports zero missing-`guard` sites.
- `uv run pytest tests/agent/test_tool_approval_preflight.py -q` passes.
- `uv run pytest tests/agent -q` — full suite green.

## Completion criteria

Both direct `execute_one_tool_call` calls pass a real guard; mypy is clean; the preflight
cases pass.

## Out of Scope

- The `tests/agent/test_tool_runner.py` migrations (row 4) and the three
  `tests/agent/test_agent_repl_tool_exec.py` sites (row 5).
- Production threading/recording (rows 1-2), the docstring (row 3), the new wiring module
  (row 7), reference regeneration (row 8).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate the 2 direct `execute_one_tool_call` calls (current :721, :754) | Completed | 20261023-163754 | 20261023-163754 | REQ-007; frozen plan numbers :678/:711 are stale implemented; full suite 9909 passed |
| 2 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-163754 | 20261023-163754 | mypy clean; preflight cases green |

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
- **Related target files**: `tests/agent/test_tool_approval_preflight.py`