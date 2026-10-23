## Goal

Thread the per-turn `ToolLoopGuard` into `scripts/agent/tool_runner.py` as an explicit
parameter instead of the `getattr(ctx, "guard", None)` read that no code can satisfy, and
record each produced tool result at the point it is produced. This removes the dependency
that never resolved (`REQ-001`, `REQ-002`) and makes the empty-result counts visible to the
guard while a batch is still executing (`REQ-003`, `REQ-004`, `AC-1`, `AC-2`, `AC-3`).

## Scope

Only `scripts/agent/tool_runner.py`. Three edits inside it:

- Add the required keyword-only `guard: ToolLoopGuard` parameter to `execute_all_tool_calls`
  (`:347-391`) and thread it through `_execute_with_dag` (`:301-344`), `_run_plan_batches`
  (`:274-298`), `_run_group_calls` (`:63-74`), and `execute_one_tool_call` (`:147-184`).
- Delete the `getattr(ctx, "guard", None)` read (`:200-201`) and the recording block it
  guards (`:208-210`) from `_collect_tool_result_msgs`; record inside `execute_one_tool_call`
  instead (`:180`–`:182`).
- Import `ToolLoopGuard` under the existing `if TYPE_CHECKING:` block (`:54-55`); add no
  runtime import edge and no field to `AgentContext`.

Reference reads only: `_record_transport_failure` (`:122` def, called at `:180`),
`_truncate_for_llm` (`:140` def, called at `:182`), `_execute_prepared_call` (`:167`),
`audit_tool_exec` (`:169`). Consumer: `scripts/agent/llm_turn_runner.py` (row 2).

## Assumptions

- `ToolLoopGuard` is importable at type-check time from `agent.tool_loop_guard` (the same
  module `scripts/agent/llm_turn_runner.py:20` imports it under `TYPE_CHECKING`).
- The six-tuple return shape of `execute_one_tool_call` (`:150`) is unchanged; the recording
  call is added beside the existing `_record_transport_failure` call, not instead of it.
- `AgentContext` carries no `guard` attribute today (`scripts/agent/context.py` has none), so
  removing the read has no other reader.

## Design decisions

- **Make the parameter required and keyword-only**, not optional: the plan requires the
  producer and consumer to share one object (`REQ-002`); an optional param would let a caller
  omit it and silently re-introduce the dead path. Every internal caller can always supply
  the guard it already holds.
- **Record at production, inside `execute_one_tool_call`, between `_record_transport_failure`
  (`:180`) and `_truncate_for_llm` (`:182`)**: this is the only location on both execution
  paths (gateway `:105-107` and gateway-bypass `:108-119`, via `_execute_prepared_call` at
  `:167`) and both scheduling shapes (sequential/gathered groups through `:63-74`). Recording
  here sees the raw `result.output` before truncation, matching `REQ-004`.

## Alternatives considered

- Recording in the batch collector `_collect_tool_result_msgs` (`:187-222`) — rejected by
  `REQ-003`/`tool002`: it runs after the whole batch completes, so it cannot observe a result
  mid-batch, which is the visibility the issue needs.
- Storing the guard on `AgentContext` — rejected by `REQ-001`/`REQ-006`: it adds mutable
  turn-scoped state where the per-turn guard instance already owns it, and nothing assigned
  the attribute before.

## Implementation

### Target file

`scripts/agent/tool_runner.py`

### Procedure

1. Add `guard: ToolLoopGuard` as a required keyword-only parameter to
   `execute_all_tool_calls` and thread it through the four internal functions down to
   `execute_one_tool_call`.
2. Delete the `getattr` read and the guarded recording block in `_collect_tool_result_msgs`.
3. Add the recording call inside `execute_one_tool_call` after `_record_transport_failure`
   (`:180`) and before `_truncate_for_llm` (`:182`).
4. Import `ToolLoopGuard` under the existing `TYPE_CHECKING` block; delete the now-unused
   `guard` local.

### Method

- `execute_all_tool_calls(ctx, tool_calls, turn, out_failed_keys, *, guard)` passes
  `guard` to `_execute_with_dag`, `_run_plan_batches`, `_run_group_calls`, and
  `execute_one_tool_call` in order.
- Inside `execute_one_tool_call`, after line `:180` insert
  `guard.record_tool_result(name, result.output)` guarded by the existing `not is_error`
  condition carried from `:209`.
- Remove lines `:200-211` (comment, `getattr`, and the `if guard is not None` block).

### Details

- `record_tool_result(tool_name, result)` expects the raw `ToolCallResult`; pass
  `result.output` (typed `str`, `transport_dto.py:11`), not the truncated `text`, so
  `_is_empty_result` (`tool_loop_guard.py:146`) sees the untruncated value (`REQ-004`).
- Keep the `is_error=False` filter exactly as at `:209`; record neither error results nor
  any new emptiness rule (`REQ-004`).
- `name` is `pc.name` (`:163`), the same identifier the collector passed at `:210`.

## Compatibility considerations

### Corrections found while implementing

- Implemented as written: required keyword-only `guard` on `execute_all_tool_calls`; `execute_one_tool_call(ctx, pc, guard)` takes it positionally so the internal `_run_group_calls`/`_run_plan_batches`/`_execute_with_dag` pass it through; recording sits after `_record_transport_failure` and before truncation under `not is_error`; the `getattr(ctx, "guard", None)` read and block are deleted from `_collect_tool_result_msgs`. Phase 1 (record in the collector) and Phase 2 (record at production) were combined in one change; the plan allows it and the end state is identical.
- Behavior note found in review: `record_tool_result` resets a tool's count on a non-empty result and increments on an empty one. Recording at production time makes the order within a gathered group follow completion order, not call order, so a batch of the same tool mixing empty and non-empty results can end with a different count than before. Nothing consults the count mid-batch (`check_empty_result_repeat` runs after the batch), so the observable change is limited to that mixed, concurrent case and to results that were produced before an exception aborted the batch.


- `execute_all_tool_calls` gains a required parameter, so every caller — including the 28
  test call sites across `tests/agent/test_tool_runner.py`,
  `tests/agent/test_agent_repl_tool_exec.py`, `tests/agent/test_tool_approval_preflight.py`
  (row 4-6) — must pass `guard=`. `scripts/agent/llm_turn_runner.py` (row 2) is the only
  production caller and passes `guard=self._guard` (`:115`).
- The generated signature table in
  `docs/23_agent/agent_13_reference-api-generated.md` (row 8) is regenerated to match.

## Security considerations

- No new secret, credential, or permission path. The recorded value is the tool result name
  and its raw text, already present in the audit log (`audit_tool_exec`, `:169`); recording
  it into the guard introduces no additional data exposure.

## Rollback considerations

- Revert the single commit touching `scripts/agent/tool_runner.py` and `llm_turn_runner.py`;
  the required parameter reverts every migrated test call site together with it. Measure
  `check_module_size.py --top 5` after the revert if the added parameters approach the
  16384 B ceiling (`UNK-02`).

## Validation plan

- `uv run mypy --no-namespace-packages scripts/` enumerates any call site still missing
  `guard`; the empty list is the proof Phase 3 migrated them all.
- `uv run ruff check scripts/agent/tool_runner.py`.
- `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_tool_loop_guard_wiring.py -q`
  asserts recording on both group shapes and both execution paths.
- `uv run python tools/check_mock_patch_targets.py` reports no new invalid patch target for
  the existing `patch("agent.tool_runner.execute_all_tool_calls")` sites.

## Completion criteria

`execute_all_tool_calls` and the four internal functions carry the required keyword-only
`guard: ToolLoopGuard`; `execute_one_tool_call` records `guard.record_tool_result(name,
result.output)` between `:180` and `:182` on both paths; `_collect_tool_result_msgs` no
longer reads `ctx.guard` or records; mypy is clean; the `TYPE_CHECKING` import is the only
import change.

## Out of Scope

- The production caller change (`scripts/agent/llm_turn_runner.py`, row 2).
- The docstring correction (`scripts/agent/tool_loop_guard.py`, row 3).
- The 28 test call-site migrations and the new wiring module (rows 4-7).
- Regenerating the API reference table (row 8).
- *When* the guard is checked (`tool002`); failed/preparation-failed recording semantics
  (`tool003`/`tool004`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add required keyword-only `guard` param and thread through the four internal functions | Completed | 20261023-163749 | 20261023-163749 | REQ-001, REQ-002; import under existing TYPE_CHECKING implemented; full suite 9909 passed |
| 2 | Delete getattr read + recording block in `_collect_tool_result_msgs` | Completed | 20261023-163749 | 20261023-163749 | removes the unreachable path at :200-211 |
| 3 | Record inside `execute_one_tool_call` after :180, before :182 | Completed | 20261023-163749 | 20261023-163749 | REQ-003, REQ-004; raw result.output, keep is_error filter |
| 4 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-163749 | 20261023-163749 | mypy must report zero missing-guard sites |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261021-093421_tool001_empty-result-loop-guard-is-never-wired.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-092413_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-112037
- **Related target files**: `scripts/agent/tool_runner.py`