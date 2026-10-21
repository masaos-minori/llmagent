# History compression reorders messages by importance and duplicates the summary block

## Priority
High

## Summary
Make compressed history preserve conversation order and tool-call adjacency, and keep exactly one
conversation-summary message.

## Background
`HistorySelectionPolicy.select()` partitions history and builds the retained set
(`scripts/agent/history_selection_policy.py:136-163`); `HistoryManager._build_compressed_result()`
assembles the new history (`scripts/agent/history.py:380-399`) using `_build_summary_msg()`
(`:240-261`).

## Problem
- Order is replaced by importance. `compressible = self.sort_by_importance(temporary +
  temporary_reasoning + history_msgs)` and then `remaining = compressible[n_compress:] +
  protected_tail; remaining = factual + remaining` (`history_selection_policy.py:146-157`). The retained
  history is therefore "all factual-class messages, then importance-ordered messages, then the protected
  tail" — not chronological. An `assistant` message carrying `tool_calls` and the `tool` messages that
  answer it are placed in different groups, so the request built from the compressed history can contain
  a `tool` result with no preceding `tool_calls` (and vice versa).
- Equality-based filtering silently drops messages: `[m for m in compressible if m not in
  protected_tail]` (`:151`, `:155`) compares dict contents, so a message equal to a protected one is
  removed even when it is a different, later occurrence (e.g. repeated identical user text or an
  identical empty tool result).
- The summary block is duplicated and grows without bound. `system_msgs` keeps the previous
  `[Conversation summary]` message (`:136`), `_build_summary_msg` returns a new message whose content is
  `f"{existing.content}\n\n{summary_text}"` (`history.py:245-261`), and `_build_compressed_result`
  returns `system_msgs + [summary_msg] + remaining` (`:398`) — so both the old summary message and a new
  message containing the old text plus the new summary are sent, on every compression.
- `_check_limits` estimates the size instead of using measured prompt tokens
  (`scripts/agent/history.py:346-353`; `ctx.services_required.llm` token counters are not consulted), so
  the growth is not detected until the provider rejects the request. Needs-confirmation for how often
  this is reached in practice.

## Reason for Change
Compression is the mechanism that keeps long sessions inside the context window. Duplicated summaries and
reordered tool traffic make it the cause of overflow and of provider-side request errors instead of the
fix.

## Implementation Intent
Keep the protected tail in conversation order, keep `assistant.tool_calls` adjacent to its `tool` results
as an atomic group, and replace the previous summary message instead of appending a copy beside it.

## Target Files or Areas
- `scripts/agent/history_selection_policy.py` (`select`, `sort_by_importance`, `partition_by_class`)
- `scripts/agent/history.py` (`_build_summary_msg`, `_build_compressed_result`, `_check_limits`)
- `tests/agent/` history/compression tests

## Required Changes
- Preserve chronological order in `remaining`; if importance ordering is wanted, apply it only within a
  group that stays in order relative to its own tool results.
- Treat an assistant message with `tool_calls` and its matching `tool` messages as one unit when
  selecting, compressing, and reordering.
- Replace selection by identity (`m not in protected_tail`) with index/identity-based selection that
  cannot drop a distinct later message.
- Emit exactly one `[Conversation summary]` message: replace the existing one rather than keeping it and
  adding a cumulative copy.
- Add a guard that reports summary-block size so the growth is observable.

## Constraints
- Ephemeral and memory-injected system messages must never be summarized
  (`history_selection_policy.py:128-135` cites `requires/20260716_15_require.md`) — that rule is
  preserved.
- `_protect_turns`/`_compress_turns` configuration semantics stay.
- Do not change the `SelectionResult` public shape without updating all consumers.

## Acceptance Criteria
- For a history containing assistant `tool_calls` plus their `tool` results, the compressed history keeps
  each call and its results adjacent and in original order.
- Compressing twice produces exactly one `[Conversation summary]` message, and its length does not
  re-include the previous summary verbatim.
- Two distinct messages with identical content are both retained when both are in scope.
- A test asserts the compressed history's message count against an expected count (no silent drops).

## Testing Expectations
- Structural tests on constructed histories (tool-call groups, duplicate content, repeated compression)
  asserting order, adjacency, count, and single summary.
- Add a "compress 3 times" case asserting the summary block does not grow per compression cycle.
- Keep assertions independent of real token counting; stub the token counter.
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`.

## Documentation Impact
Document the compression contract in the history/context docs: ordering guarantee, tool-call atomicity,
one summary message, what is protected, and what is dropped. State whether `elapsed`/token-based limits
are estimated or measured.

## Out of Scope
- Changing token estimation to provider-reported `prompt_tokens` (see Unresolved Questions).
- Compression tuning configuration and thresholds.
- Message schema changes.

## Dependencies
- Related to `turn002` (duplicate user messages inflate what compression must handle).
- Independent of `turn001`/`turn003`/`turn004`.

## Unresolved Questions
- Should `sort_by_importance` be kept at all, or only as a tiebreaker inside a contiguous window? Needs a
  design decision.
- Should compression use the LLM-reported prompt token count for the trigger instead of character/estimate
  counting? Needs confirmation.

## AI Implementation Intent is to preserve conversation semantics; keep the change inside the selection
policy and the result builder, and do not change summarization prompt text.

## AI Implementation Instruction
Never re-sort messages that participate in a tool-call exchange. Use indexes, not content equality. Prove
"exactly one summary message" with a repeated-compression test.

## Traceability
- **Workflow phase**: `python-code-review` (turn orchestration / history review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/history_selection_policy.py`, `scripts/agent/history.py`,
  `tests/agent/`
