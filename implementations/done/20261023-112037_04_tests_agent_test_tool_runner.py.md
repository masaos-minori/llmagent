## Goal

Migrate every direct call of the two changed entry points in `tests/agent/test_tool_runner.py`
to pass a real `ToolLoopGuard`, and add recording assertions next to the paths they cover, so
the file keeps the direct-call coverage of both signatures after the parameter becomes
required (`REQ-003`, `REQ-004`, `REQ-007`, `AC-2`, `AC-3`).

## Scope

Only `tests/agent/test_tool_runner.py`. Two kinds of edit:

- Call-site migration: add `guard=<real ToolLoopGuard>` to each direct call of
  `execute_all_tool_calls` and `execute_one_tool_call`.
- Recording assertions: for at least one call on each group shape and each execution path,
  assert the guard saw the result (the mid-batch / turn-level visibility the issue needs).

Reference reads only: the fixture shapes reused from `tests/agent/test_llm_turn_runner.py`
(row 2's sibling) and the option/default assertions in `tests/agent/test_tool_loop_guard.py`
(`:360-413`).

## Assumptions

- At HEAD there are 16 direct `execute_all_tool_calls` calls and 10 direct
  `execute_one_tool_call` calls in this file (plan-listed at `:535`, `:565`, `:579`, `:606`,
  `:640`, `:670`, `:699`, `:734`, `:787`, `:880`, `:911`, `:933`, `:959`, `:984`, `:1020`,
  `:1074` and `:456`, `:472`, `:487`, `:511`, `:1122`, `:1140`, `:1164`, `:1187`, `:1215`,
  `:1242`). Verify the current set with `rg`/mypy before editing — the repo has moved since
  the plan was frozen, so enumerate rather than trust the numbers.
- A real `ToolLoopGuard` can be constructed the same way the unit suite does
  (`tests/agent/test_tool_loop_guard.py`).

## Design decisions

- **Construct one real `ToolLoopGuard` per test** and pass it by keyword; do not mock the
  entry point (mocking is what hid this gap in the first place, `REQ-007`).
- **Record by construction**: because `execute_one_tool_call` now records inside itself
  (`tool_runner.py`, row 1), a guard passed into a passing test already shows the result was
  seen — assert on the guard's `_empty_result_counts` for the empty-result case.

## Alternatives considered

- Patching `agent.tool_runner.execute_one_tool_call` / `execute_all_tool_calls` with an
  `AsyncMock` — rejected by `REQ-007`/`AC-6`: the acceptance surface runs the unmocked path;
  patching would again hide the wiring.

## Implementation

### Target file

`tests/agent/test_tool_runner.py`

### Procedure

1. For each of the direct `execute_all_tool_calls` calls, add `guard=<guard>` as a keyword
   argument.
2. For each of the direct `execute_one_tool_call` calls, add `guard=<guard>` as a keyword
   argument.
3. In one sequential-group test and one gathered-group test, and on both the gateway and
   gateway-bypass execution paths, assert the passed guard recorded the result.

### Method

- Build the guard with the same constructor/fixture pattern the existing unit suite uses.
- Insert `, guard=my_guard` into each call site; mypy will flag any site still missing it —
  that list is the completeness check.
- For the recording assertion, drive a `""`-returning stub through `execute_one_tool_call`
  and assert `my_guard._empty_result_counts[tool_name]` increments (`REQ-004`).

### Details

- Keep the `is_error=False` recording semantics: assert recording for a non-error empty
  result; an error result must not record.
- Do not edit any of the file's existing 34-test assertions beyond adding the parameter and
  the new recording assertions.

## Compatibility considerations

### Corrections found while implementing

- Plan scope gap: `tests/agent/test_tool_runner.py` also calls `_execute_with_dag` directly (9 sites), which now needs `guard` too; those were migrated together with the 26 entry-point calls (35 call sites in total). Added `TestExecuteOneToolCallRecordsOnGuard` (gateway-bypass and gateway paths, error result not recorded, untruncated output, both group shapes, collector no longer reads `ctx.guard`). Mutation check (recording removed) fails 9 tests.


- Every migrated call must supply a concrete `ToolLoopGuard`; a missing argument fails mypy,
  which is the safety net for completeness.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run mypy --no-namespace-packages scripts/ tests/` reports zero missing-`guard` sites.
- `uv run pytest tests/agent/test_tool_runner.py -q` passes with the new recording assertions.
- `uv run pytest tests/agent -q` — full suite green; the 7 permanent skips unchanged.

## Completion criteria

All direct `execute_all_tool_calls` and `execute_one_tool_call` calls pass a real guard;
mypy is clean; recording asserted on both group shapes and both execution paths; the full
`tests/agent` suite passes.

## Out of Scope

- The production parameter/threading (`scripts/agent/tool_runner.py`, row 1).
- The production caller (`scripts/agent/llm_turn_runner.py`, row 2).
- The three DAG-evaluation sites in `tests/agent/test_agent_repl_tool_exec.py` (row 5).
- The two direct sites in `tests/agent/test_tool_approval_preflight.py` (row 6).
- The new wiring module `tests/agent/test_tool_loop_guard_wiring.py` (row 7).
- Reference regeneration (row 8).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate 16 `execute_all_tool_calls` call sites to pass a real guard | Completed | 20261023-163752 | 20261023-163752 | REQ-007; enumerate via mypy, do not trust frozen line numbers implemented; full suite 9909 passed |
| 2 | Migrate 10 `execute_one_tool_call` call sites | Completed | 20261023-163752 | 20261023-163752 | REQ-007 |
| 3 | Add recording assertions on both group shapes and both execution paths | Completed | 20261023-163752 | 20261023-163752 | REQ-003, REQ-004, AC-2, AC-3 |
| 4 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-163752 | 20261023-163752 | mypy clean; full suite green |

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
- **Requirement ID**: `REQ-003`, `REQ-004`, `REQ-007`
- **Source issue**: `issues/20261021-093421_tool001_empty-result-loop-guard-is-never-wired.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-092413_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-112037
- **Related target files**: `tests/agent/test_tool_runner.py`