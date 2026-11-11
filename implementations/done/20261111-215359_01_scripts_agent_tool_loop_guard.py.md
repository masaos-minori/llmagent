## Goal

Delete the redundant turn-start `check_empty_result_repeat(message)` call inside
`ToolLoopGuard.check_all` in `scripts/agent/tool_loop_guard.py`, and update its
docstring so the single post-execution evaluation point is explicit. Behavior-preserving
cleanup; observable behavior when the guard is enabled or disabled stays identical.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The turn-start call is inert in both states: when enabled, the post-execution
  `check_empty_result_repeat` in `LLMTurnRunner.run` fails the turn before any
  `_empty_result_counts` value can persist past a threshold crossing, so at the next
  turn start the count is strictly below the limit and `scan_empty_result_repeat`
  returns `None`; when disabled (`tool_empty_result_max_repeats = 0`),
  `scan_empty_result_repeat` returns `None` immediately. Verified against current
  source in adversarial verification.
- `tool_runner.py:execute_one_tool_call` → `record_tool_result` is the sole in-turn
  writer of `_empty_result_counts`, so removing the turn-start call cannot change what
  the post-execution check observes.

## Design decisions
- Delete only the single `if msg := self.check_empty_result_repeat(message): return msg`
  line from `check_all` and drop "empty result" from its ordered docstring list. This
  leaves cycle/stagnation/dedup/retry ordering untouched and keeps the post-execution
  check in `LLMTurnRunner.run` as the one real evaluation point.
- Add a one-line docstring note pointing to the post-execution evaluation in
  `LLMTurnRunner.run` so a maintainer does not assume the turn-start check is meaningful.

## Alternatives considered
- Leaving the call in place: rejected; it performs no useful work and its docstring
  entry misleads maintainers into thinking the turn-start empty-result check matters.
- Moving the check into `check_all` position after retry: rejected; the single
  evaluation point must stay post-execution in `LLMTurnRunner.run` (out of scope).

## Implementation
### Target file
- `scripts/agent/tool_loop_guard.py`

### Procedure
1. Delete the turn-start `if msg := self.check_empty_result_repeat(message): return msg`
   line from `ToolLoopGuard.check_all` (REQ-001).
2. Update `check_all`'s docstring: remove "empty result" from the ordered guard list
   and add a one-line note that the empty-result guard is evaluated once per turn, after
   execution, in `LLMTurnRunner.run` (REQ-002).

### Method
- In `ToolLoopGuard.check_all`, remove the two lines (the walrus `if` and its
  `return msg`) that call `self.check_empty_result_repeat(message)`. The remaining
  calls (`check_cycle`, `_check_progress_stagnation`, `check_dedup`, `check_retry`) keep
  their order and structure.
- Edit the module-level docstring on `check_all` from
  `"Run cycle, stagnation, dedup, retry, and empty result guards in order; return first
  hit or None."` to drop "empty result" from the list and append the post-execution
  note. Do not touch `check_empty_result_repeat`, `scan_empty_result_repeat`,
  `record_tool_result`, or any counting/early-break machinery.

### Details
- REQ-001: delete the turn-start `check_empty_result_repeat` invocation so
  `check_all` no longer calls it.
- REQ-002: docstring becomes
  `"Run cycle, stagnation, dedup, and retry guards in order; return first hit or None.
  The empty-result guard is evaluated once per turn, after execution, in
  LLMTurnRunner.run."`
- REQ-003: preserve behavior exactly. The post-execution check in
  `LLMTurnRunner.run` still detects an empty-result repeat and fails the turn with
  `reason="empty_result_repeat"`; with the guard disabled (`0`) no detection occurs.

## Compatibility considerations
N/A: no public or runtime interface change. `check_all` still returns `str | None`;
callers in `LLMTurnRunner.run` are unchanged.

## Security considerations
N/A: no security impact. Removing an inert dead-code branch does not alter access or
guard enforcement.

## Rollback considerations
N/A: revert the commit. The change is a single-line deletion plus a docstring edit.

## Validation plan
- Format + lint: `uv run ruff format scripts/` and `uv run ruff check scripts/` — clean.
- Type check: `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` — no
  new errors.
- Unit — empty-result sequence crossing threshold still detected; disabled guard
  performs no detection: `uv run pytest tests/agent/test_tool_loop_guard.py` — passes.
- Unit — post-execution detection and disabled-guard behavior unchanged:
  `uv run pytest tests/agent/test_llm_turn_runner.py` — passes.

## Completion criteria
- `ToolLoopGuard.check_all` no longer calls `check_empty_result_repeat` (AC-1).
- Empty-result repeat is still detected via the post-execution check in
  `LLMTurnRunner.run` and fails the turn with `reason="empty_result_repeat"` (AC-2).
- With the guard disabled (`0`), no empty-result detection occurs (AC-3).
- `ruff`, `mypy`, and the affected test trees pass (AC-4).

## Out of Scope
`record_tool_result`, `scan_empty_result_repeat`, `check_empty_result_repeat`,
`observe_availability` (counting and post-execution-check machinery), the
post-execution empty-result check in `LLMTurnRunner.run`, the disabled-by-default policy
(`tool_empty_result_max_repeats = 0`), the `max_tool_turns` loop bound, and any change to
`_empty_result_counts` or the early-break scan. No `docs/*.md` update.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the turn-start `check_empty_result_repeat` call in `check_all` | Completed | 20261111-221455 | 20261111-221455 | — |
| 2 | Update `check_all` docstring (drop "empty result", add post-execution note) | Completed | 20261111-221455 | 20261111-221455 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261111-221455 | 20261111-221455 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261111-221455 | 20261111-221455 | N/A: no docs update required |

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
- **Requirement ID**: `REQ-001` (delete the turn-start call), `REQ-002` (update the docstring), `REQ-003` (behavior preserved)
- **Source issue**: `issues/20261111-212552_tlg001_redundant-empty-result-guard.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261111-214106_tlg001_redundant-empty-result-guard.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-215359
- **Related target files**: `scripts/agent/tool_loop_guard.py`
