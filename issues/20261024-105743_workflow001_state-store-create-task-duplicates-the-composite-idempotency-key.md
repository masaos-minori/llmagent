# `StateStore.create_task()` duplicates the composite task idempotency key

## Priority
Medium

## Summary
`StateStore.create_task()` in `scripts/agent/workflow/state_store.py` builds `idempotency_key` from
`f"{session_id}:{turn_number}"` in its own copy of the task-insert code. The plan
`plans/done/20261023-084918_plan.md` and its procedures `implementations/20261024-074027_01` to `_05`
remove that derivation only from `agent.workflow.task_ops.create_task()`, which is the function the
production path calls. The wrapper keeps a second, uncalled copy of the defect, so a future caller of
`StateStore.create_task()` reintroduces the restart collision the closed plan removed.

## Background
Measured at HEAD `2044b0ad1` (2026-10-24), re-verified on the tree rebased onto `f18e1a6fe`:

- `scripts/agent/workflow/state_store.py:48` `def create_task(...)`, with the composite branch at
  `:56-59` (the f-string is `:57`) and its own `INSERT INTO tasks` at `:65`. It does not call
  `agent.workflow.task_ops`; the file imports only `agent.workflow.models` (`:17`).
- `scripts/agent/workflow/task_ops.py:21-24` holds the same derivation; `task_ops.py` is the module the
  production path uses (`scripts/agent/workflow_engine_adapter.py:37` imports it, `:269` calls it).
- No caller of the wrapper exists: `grep -rn "\.create_task(" scripts/ tests/ --include="*.py"` returns
  only `asyncio.create_task` hits, and `grep -rn "store\.create_task" tests/ scripts/` is empty.
- `StateStore` re-implements task and attempt SQL inline in general (`:65`, `:97`, `:119`, `:126`, `:166`,
  `:190`, `:198`), so this issue is about the duplicated key derivation only, not about the pattern.
- `plans/done/20261023-084918_plan.md` treats `state_store.py` as a Reference Files row (`:98`) and records this
  residual in its `Corrections from re-measurement`. `plans/20261023-093153_plan.md` targeted it as its
  own row 2 and recorded it as known debt (`UNK-03`); that plan is closed as a duplicate and archived to
  `plans/done/20261023-093153_plan.md`.

## Problem
Two functions write `tasks` rows with different key rules after the closed plan lands. The plan's own
scope guard is file-scoped: `grep -n 'f"{session_id}' scripts/agent/workflow/task_ops.py` returns nothing
while `scripts/agent/workflow/state_store.py:57` still composes a key from values that are not unique
across processes (`session_id` is the literal `""` and `turn_number` is a process-local counter,
`scripts/agent/conversation_state_manager.py:111`). Nothing in the test suite covers the wrapper, so no
gate detects the divergence.

## Reason for Change
The closed plan's stated intent is that the composite form no longer exists in the task-write path.
Leaving a second copy means the removed defect is one added call away from returning, and the follow-up
is small: one branch and one test.

## Implementation Intent
Make `StateStore.create_task()` stop deriving a key. Two candidate forms, to be chosen by the plan:

- Delegate to `agent.workflow.task_ops.create_task()` and return its `TaskRecord`, removing the duplicated
  `INSERT` block.
- Keep the inline insert and replace only the branch with the same unconditional `str(uuid.uuid4())` the
  closed plan applied.

Add the missing test coverage for the wrapper either way.

## Target Files or Areas
- `scripts/agent/workflow/state_store.py` (`create_task`, `:48-92`)
- `tests/agent/workflow/test_workflow_state_store.py` (a `TestCreateTask`-level case for the wrapper)
- `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` only if the delegation wording
  changes what `StateStore` owns

## Required Changes
- Remove the composite derivation from `StateStore.create_task()`.
- Keep the method signature and the `TaskRecord` return type unchanged.
- Add a test that calls `store.create_task("X", 1, "1.0.0", "wf-test")` twice against the same retained
  fixture database and asserts no `sqlite3.IntegrityError` and two distinct UUID-parsable keys.
- Extend the closed plan's scope guard so it is not file-scoped: `grep -rn 'f"{session_id}' scripts/agent/workflow/`
  must return no match.

## Constraints
- No schema change: `tasks.idempotency_key TEXT UNIQUE NOT NULL` (`scripts/db/schema_sql.py:178`) and
  `WORKFLOW_SCHEMA_VERSION` (`scripts/db/schema_sql.py:25`) stay as they are.
- No signature or public-API change; `StateStore` is exported by `scripts/agent/workflow/__init__.py`.
- If the delegation form is chosen, a new `agent.workflow.state_store` to `agent.workflow.task_ops` import
  must keep `PYTHONPATH=scripts uv run lint-imports` green (`.importlinter`).
- `scripts/agent/workflow/state_store.py` is 12174 B, under the 20480 B gate
  (`tools/check_module_size.py:38`); `create_task` is A-rank in `radon cc`.
- Sequencing: land after `implementations/20261024-074027_01` and `_02` are implemented. `_01` removes the
  composite derivation from the live path, which is what makes the residual in this wrapper visible as the
  last copy, and `_02` owns `tests/agent/workflow/test_workflow_state_store.py`, the file this issue adds a
  test to.

## Acceptance Criteria
- No composite key derivation remains anywhere under `scripts/agent/workflow/`.
- Two `StateStore.create_task()` calls with identical `(session_id, turn_number)` do not raise and produce
  distinct keys.
- `tests/agent/workflow` passes with the new case added and no existing assertion changed.
- `scripts/agent/workflow/task_ops.py` and `scripts/db/schema_sql.py` diffs are empty.

## Testing Expectations
- One new unit test in `tests/agent/workflow/test_workflow_state_store.py` using the existing `tmp_path`
  `store` fixture (`:57`).
- Mutation check: restore the composite branch in a scratch copy of `state_store.py` and confirm the new
  test fails.
- `uv run pytest tests/agent/workflow -q` before and after (baseline 90 passed, re-measured on the tree
  rebased onto `f18e1a6fe`).

## Documentation Impact
None expected if the wrapper only stops deriving a key: `docs/41_db/db_02_architecture_and_schema-schema-reference.md`
section 7 and `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` already state the
contract after rows 4 and 5 of the closed plan. Run the docs checkers listed in `routing.md` only if a
wording change is actually made.

## Out of Scope
- Merging `StateStore` with the `agent/workflow/*_ops` modules, or removing the other inline SQL copies.
- Deleting `StateStore.create_task()` or `StateStore.get_task_by_idempotency_key()` (`:124`).
- `StateStore`'s attempt, artifact, and diagnostic methods.
- Any change to `workflow_engine_adapter.py` or the resume path.

## Dependencies
Depends on the implementation of `implementations/20261024-074027_01_scripts_agent_workflow_task_ops.py.md`
and `implementations/20261024-074027_02_tests_agent_workflow_test_workflow_state_store.py.md`; both are
generated and not yet executed. Sibling check: the closed duplicate plan
`plans/done/20261023-093153_plan.md` was the only other work item targeting this file.

## Unresolved Questions
- Delegate or inline replacement: the delegation form removes duplicated SQL but adds a cross-module
  import; the inline form keeps the current structure and leaves two `INSERT` copies. Undecided.
- Should the uncalled wrapper be deleted instead? No caller was found, but `StateStore` is a documented
  public class (`scripts/agent/workflow/__init__.py` public API list), so external use cannot be ruled out.
- Is the same divergence present in `StateStore.start_attempt` / `finish_attempt` versus
  `agent/workflow/attempt_ops.py`? Not inspected; out of scope unless it turns out to share the key defect.

## AI Implementation Instruction
Change only `StateStore.create_task()` and its test. Do not touch `task_ops.py`, `schema_sql.py`, or the
adapter. Do not delete the wrapper without a decision on the unresolved question above. Keep the first
docstring line of `create_task` unchanged so the generated-reference guard stays inert. Run
`rules/toolchain.md`'s sequence plus `PYTHONPATH=scripts uv run lint-imports`.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261023-084918_plan.md` (residual recorded in its `Corrections from re-measurement`),
  `plans/done/20261023-093153_plan.md` target row 2 and `UNK-03`
- **Source implementation procedure**: N/A: not filed from an implementation procedure
