# Implementation: Dependency-Aware Tool Scheduling (Default DAG Mode + Intra-Round Concurrency)

## Goal

Replace the coarse "serialize entire round on any side-effect" heuristic with the existing DAG scheduler as the default, and refine the DAG so non-conflicting groups run concurrently rather than sequentially within a round.

## Scope

**In-Scope:**
- Change `use_tool_dag` default from `False` to `True` in `config_dataclasses.py` and `config/agent.toml`
- Refine `_execute_with_dag()` in `tool_runner.py`:
  - Resource-scoped write groups with different scopes run concurrently
  - Resource-scoped write groups run concurrently with the parallel (read) group
  - `write_first` (unscoped writes) remain sequential before reads — conservative: no scope info
  - `serial_barrier` tools remain absolute barriers
- Add `scheduling_mode: str` to the audit log round event so operators can see which execution path was used per round
- Update debug log: emit concurrency decision per group pair

**Out-of-Scope:**
- Removing `_execute_standard` (retained for `serial_tool_calls=True` and DAG-disabled configs)
- Making unscoped writes (`write_first`) concurrent with reads (unsafe: undefined resource)
- Replacing the workflow engine or adding distributed orchestration

## Assumptions

1. `asyncio.gather` already runs tools within a group concurrently — the only change is to allow multiple GROUPS to gather concurrently.
2. "Independent" in the require context = different `resource_scope` values (or read-only). Two groups with different resource scopes have no declared conflict.
3. Making `use_tool_dag=True` the default does not break existing behavior for tools without `ToolSpec` metadata — they fall into `write_first` or `parallel` via `WRITE_TOOLS`/`DELETE_TOOLS` membership, same as before.
4. `serial_barrier` groups must still run as absolute barriers — no concurrent execution with others.

## Unknowns & Gaps

| ID | Unknown | Evidence Missing | Resolution | Blocking |
|---|---|---|---|---|
| UNK-01 | Are there tests that assert sequential group ordering that will fail with concurrent groups? | No grep hit for "sequential" in test_tool_scheduler or test_tool_runner | Run tests after change; update order-sensitive assertions to use set equality | False |
| UNK-02 | Can two resource-scoped groups with the SAME scope appear in different scope groups? | `build_execution_groups` uses `resource_groups.setdefault(scope, [])` — no | No, same-scope tools are already merged into one group | False |
| UNK-03 | What happens to `tool_timings` dict in `_execute_with_dag` if groups run concurrently? | `tool_timings` is computed in `_execute_standard` only | No issue — `_execute_with_dag` does not use `tool_timings` | False |

## Implementation

### Target files

- `scripts/agent/config_dataclasses.py` — change `use_tool_dag: bool = True`
- `config/agent.toml` — change `use_tool_dag = true`
- `scripts/agent/tool_runner.py` — refine `_execute_with_dag()` for concurrent non-conflicting groups
- `scripts/agent/tool_scheduler.py` — add `concurrent_groups: list[list[list[dict]]]` to `_GroupMetadata`
- `tests/test_tool_runner.py` or `test_tool_scheduler.py` — add concurrency tests

### Procedure

#### Step 1: Change default `use_tool_dag = True`

- `config_dataclasses.py`: `use_tool_dag: bool = True`
- `config/agent.toml`: `use_tool_dag = true`

#### Step 2: Refine `build_execution_groups()` for concurrent group metadata

Add `concurrent_groups: list[list[list[dict]]]` to `_GroupMetadata`. Each element is a list of groups that CAN run concurrently.

Logic:
- `serial_barrier` groups: one barrier per tool, all in their own `concurrent_groups` entry
- `write_first` group: own entry (sequential before reads, conservative)
- Resource scope groups + `parallel` group: one concurrent entry containing all of them (different resource scopes + reads → no declared conflict)

Example output for [write(scope=fs), write(scope=db), read_a, read_b]:
```
concurrent_groups = [
  [[write_scope_fs], [write_scope_db], [read_a, read_b]]  # run concurrently
]
```

#### Step 3: Refine `_execute_with_dag()` to run concurrent groups in parallel

Replace `for group in groups: await asyncio.gather(...)` with:
```python
for concurrent_batch in metadata.concurrent_groups:
    batch_results = await asyncio.gather(
        *(asyncio.gather(*(execute_one_tool_call(ctx, tc, turn) for tc in group))
          for group in concurrent_batch)
    )
    results.extend(r for group_res in batch_results for r in group_res)
```

Preserve original order for `_collect_tool_result_msgs`.

#### Step 4: Add scheduling trace to audit log

In `write_round_exec()` call: pass `scheduling_mode="dag_concurrent"` or `"dag_sequential"` based on whether concurrent groups had > 1 member.

#### Step 5: Add tests

- Test: `build_execution_groups` with [write(scope=A), read] → same concurrent batch
- Test: `build_execution_groups` with serial_barrier tool → own barrier batch
- Test: `_execute_with_dag` with two scope groups + reads → all started concurrently

### Method

- Default change from `False` to `True` for `use_tool_dag`
- Additive `concurrent_groups` field to `_GroupMetadata`
- New concurrent execution path in `_execute_with_dag()`
- Audit log enhancement for scheduling mode visibility

### Details

- Result ordering changes when groups run concurrently — sort results back to original `approved_calls` order before `_collect_tool_result_msgs`
- Operators are responsible for declaring `ToolSpec.resource_scope` correctly; document in release notes

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `build_execution_groups` output | Unit | `uv run pytest tests/ -k scheduler -v` | all pass |
| `_execute_with_dag` concurrency | Unit — mock execute with timing | `uv run pytest tests/ -k tool_runner -v` | all pass |
| Default `use_tool_dag=True` | Integration — any tool round test | `uv run pytest -q` | no new failures |
| Lint | Static | `uv run ruff check scripts/` | 0 errors |
| Type check | Static | `uv run mypy scripts/` | no new errors |
| Full suite | Regression | `uv run pytest -q` | no new failures |

## Risks

- **Risk:** Changing default `use_tool_dag=True` changes behavior for tests that mock the standard path
  → **Mitigation:** check `test_tool_runner.py` and update mocks; set `use_tool_dag=False` in tests that specifically test `_execute_standard`
- **Risk:** Concurrent write+read groups cause race conditions if a read-only tool has undeclared write side effects
  → **Mitigation:** this is operator responsibility via `ToolSpec.resource_scope`; document in release notes
- **Risk:** Result ordering changes when groups run concurrently
  → **Mitigation:** sort results back to original `approved_calls` order before `_collect_tool_result_msgs`
