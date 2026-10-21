# `execute` stage retry re-runs turn entry work, duplicating user messages and turn counters

## Priority
High

## Summary
Make one user turn enter the conversation exactly once, independently of how many times the workflow
`execute` stage retries.

## Background
`config/workflows/default.json` declares `{"id": "execute", "timeout_sec": 120, "retryable": true}` with
`retry_policy.max_attempts = 3` and `backoff_sec = 1`. `WorkflowEngine._run_stage_with_retry`
(`scripts/agent/workflow/workflow_engine.py:134-176`) re-invokes the stage callback on every
`Exception` and raises `WorkflowHaltError` only after `max_attempts`. The stage callback is
`WorkflowEngineAdapter.execute_fn` (`scripts/agent/workflow_engine_adapter.py:161-176`) →
`_process_turn` (`:323-350`).

## Problem
`_process_turn` is not idempotent. Each attempt re-runs, in order:
`clear_previous_turn_ephemeral_messages`, `handle_memory_injection(line)`,
`classify_and_inject_mode(line, ctx)`, `append_user_message(line)`, `handle_history_compression()`
(`workflow_engine_adapter.py:331-336`). `ConversationStateManager.append_user_message`
(`scripts/agent/conversation_state_manager.py:106-119`) appends to `ctx.conv.history`, writes
`ctx.session.save("user", line)` to the session DB, and increments `ctx.stats.stat_turns`.
A turn that needs 3 attempts therefore stores the same user message up to 3 times in both the sent
history and the persisted history, inflates `stat_turns` by 3, repeats memory injection and mode
classification, and feeds the inflated turn number into the task idempotency key (`turn001`).

## Reason for Change
History duplication changes what the LLM sees, what is persisted, and every per-turn statistic — a
correctness and context-budget problem that appears exactly when a model/tool call fails, i.e. when the
system is already degraded.

## Implementation Intent
Move the turn-entry side effects outside the retried stage, or make the entry step idempotent per turn
(guard on the turn id). Keep the retry boundary where it is useful (LLM/tool execution), not at the
point where conversation state is mutated.

## Target Files or Areas
- `scripts/agent/workflow_engine_adapter.py` (`execute_fn`, `_process_turn`)
- `scripts/agent/conversation_state_manager.py` (`append_user_message`)
- `scripts/agent/workflow/workflow_engine.py` (retry boundary, for reference)
- `config/workflows/default.json` (stage `retryable` policy)

## Required Changes
- Perform user-message append, memory injection, and mode classification exactly once per turn;
  on retry, resume from the LLM/tool step.
- Make `stat_turns` increment once per user turn regardless of attempts.
- Ensure `handle_history_compression()` is not re-triggered by a retry of the same turn.
- State explicitly in code which part of a turn is retryable and which part is once-only.

## Constraints
- Do not weaken retry for genuinely transient LLM/tool transport failures.
- `stat_turns` is used by `/stats`, session diagnostics, and the task key (`turn001`) — a change here
  must stay consistent with those consumers.
- Retry policy files under `config/workflows/` are validated by `deploy/deploy.sh`; do not change the
  schema.

## Acceptance Criteria
- With a stubbed `_process_turn` that fails twice and then succeeds, the session DB contains exactly one
  `user` row for the turn and `ctx.conv.history` contains exactly one user message.
- `ctx.stats.stat_turns` increases by exactly 1 for a turn that took 3 attempts.
- Memory injection and mode classification run once per turn (assert call counts on real components,
  not on mocks the test configured).

## Testing Expectations
- Regression test that drives the real retry path: a stage callback that raises twice, asserting exactly
  one user message and one `stat_turns` increment.
- Characterization test for the current behavior before the change, so the behavior delta is explicit.
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`.

## Documentation Impact
Document the turn lifecycle contract in the workflow/turn docs: which phase of a turn runs once, which
phase may repeat, and what a retry does and does not re-execute. Note the per-attempt history growth
as failure behavior.

## Out of Scope
- Whether `execute` should remain `retryable` at all (policy question; see Unresolved Questions).
- Task status transitions (`turn003`) and idempotency key scoping (`turn001`).

## Dependencies
- Depends on `turn001` being settled first (the key derivation consumes `stat_turns`).
- `turn003` reviews the same `finally` block; sequence them to avoid conflicting edits.

## Unresolved Questions
- Should the retry apply to the LLM call only, meaning `execute_fn` is restructured into a
  once-only entry step plus a retryable inference step? Needs a design decision.
- Is `max_attempts = 3` on the `execute` stage intended given the stage performs the whole turn?
  Needs confirmation.

## AI Implementation Instruction
Keep the retry mechanism, move or guard the side effects. Do not add a flag that silently skips work —
state which step is once-only, and prove it with a test that counts calls on real components.

## Traceability
- **Workflow phase**: `python-code-review` (turn orchestration review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/workflow_engine_adapter.py`,
  `scripts/agent/conversation_state_manager.py`, `scripts/agent/workflow/workflow_engine.py`,
  `config/workflows/default.json`
