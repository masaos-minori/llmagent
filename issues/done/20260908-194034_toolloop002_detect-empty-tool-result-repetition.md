# Add a ToolLoopGuard check for repeated empty tool results (varying arguments evade existing guards)

## Priority
Medium

## Summary
`ToolLoopGuard` (`scripts/agent/tool_loop_guard.py`) has four working guards (`check_dedup`, `check_retry`, `check_cycle`, `check_error_limit`) plus a fifth, unimplemented one (`_check_progress_stagnation`), all of which key off the LLM's tool-call *arguments* or actual execution *errors*. None of them look at whether the tool's *result content* is empty. When the LLM keeps calling the same tool with slightly different arguments each round (e.g. rephrasing a search query) and the tool keeps returning an empty string, no existing guard fires — the loop runs unchecked until the unrelated `max_tool_turns` hard cap (default 5) ends it.

## Background
Confirmed by direct code reading of `scripts/agent/tool_loop_guard.py`:
- `check_dedup` (line 205) and `check_retry` (line 227) key on `_canonical_key(name, arguments_str)` — an MD5 hash of the tool name plus parsed arguments (line 106). Different arguments produce a different key, so these two guards do not fire when arguments vary round to round.
- `check_cycle` (line 131) hashes the full round's `(name, arguments)` set and only fires when the exact same round-level fingerprint repeats — also argument-sensitive.
- `check_error_limit` (line 280) counts consecutive rounds where every tool call returned `is_error=True`. An empty-but-successful result (`is_error=False`, `error_type=""`) does not count toward this.
- `_check_progress_stagnation` (line 167) is present but unimplemented (`pass  # TODO: implement proper comparison logic`, then `return None  # Placeholder until full implementation`, lines 201-203). Its actual design intent, confirmed by reading its body, is different from empty-result detection: it collects the *set of distinct tool names* used in a round (line 178-182) and explicitly bails out via `if len(tool_names) < 2: return None` (line 185-186) — i.e. it is designed to detect "the same combination of 2+ different tools keeps being invoked without progress," not "one tool keeps returning nothing." A single tool called repeatedly (with or without varying arguments) never reaches this guard's comparison logic at all, even once implemented as currently designed.
- `ToolConfig` (`scripts/agent/config_dataclasses.py`) already has a `progress_stagnation_window: int = 3` field (line 187) dedicated to `_check_progress_stagnation`, following the same `0 = disabled` convention as the other guard thresholds (`tool_dedup_max_repeats` line 180, `tool_cycle_detect_window` line 182, `tool_error_max_consecutive` line 183, `tool_error_retry_max` line 185).
- Confirmed in `scripts/agent/tool_runner.py`: `execute_one_tool_call()` (line 90) returns `text` (the raw tool output) unchanged except for a length-truncation check (`llm_text`, lines 130-134) — no empty-string check exists. `_collect_tool_result_msgs()` (line 139) appends `llm_text` directly into conversation history via `ctx.conv.append_message({"role": "tool", "tool_call_id": tc_id, "content": llm_text})` (line 164-166) with no empty-content handling either.

## Problem
A tool-calling loop where the LLM varies its arguments each round while the tool keeps returning an empty string is currently undetected by all four working guards, and `_check_progress_stagnation` — even once its own logic is filled in — would not catch this case either, because its design only considers rounds using 2+ distinct tool names. The only thing that eventually stops such a loop today is `max_tool_turns` (`config_dataclasses.py` line 201, default 5), which is a blunt, unrelated ceiling rather than a targeted, early detection of this specific pattern.

## Reason for Change
Left unaddressed, this wastes LLM calls, tokens, and latency on every occurrence, and degrades user experience (the agent visibly "thinks" for several rounds before giving up at the `max_tool_turns` ceiling with a generic failure). It is also inconsistent with the existing guards' design intent — `ToolLoopGuard`'s whole purpose is to stop non-productive tool-call loops early and let the LLM answer with what it already has, and this specific pattern is currently the only one of its kind (single-tool, empty-result loop) that isn't covered by any of the 4 implemented guards or `_check_progress_stagnation`'s design.

## Implementation Intent
Add a new guard method to `ToolLoopGuard` (e.g. `check_empty_result_repeat`) that tracks, per tool name, how many of the most recent consecutive calls to that tool returned an empty (or otherwise degenerate — see Constraints) result, regardless of whether the arguments differed each time. When a configurable threshold is reached, return an exit message following the existing guards' pattern (see `DEDUP_HINT`/`RETRY_HINT`/`CYCLE_HINT`/`STAGNATION_HINT` constants, lines 34-54) and let the existing `_finalize_after_guard()` fallback (in `llm_turn_runner.py`) take over, same as the other guards.

This requires threading tool *results* (not just the LLM's `tool_calls` message) into the guard's per-turn state — `check_all()` (line 249) currently only receives `message: LLMMessage` (the tool-call request), not execution results, so the call site in `llm_turn_runner.py` (where `guard.check_all(...)` is invoked) and the result-collection path in `tool_runner.py` need a way to report each round's tool results back to the guard before the next round starts.

Add a new `ToolConfig` field (e.g. `tool_empty_result_max_repeats: int`, `0 = disabled`) following the exact convention of the existing threshold fields — do NOT repurpose `progress_stagnation_window`, which belongs to the unrelated `_check_progress_stagnation` guard (see Constraints).

Secondary, smaller improvement to consider in the same change: when a tool result is an empty string, replace it with an explicit placeholder (e.g. `"(tool returned no output)"`) before appending it to conversation history in `_collect_tool_result_msgs()`, so the LLM can distinguish "the tool ran and found nothing" from a truncated/malformed response. This does not by itself stop a loop, but complements the new guard by making empty results more legible to the LLM in the rounds before the guard fires.

## Target Files or Areas
- `scripts/agent/tool_loop_guard.py` — new guard method, per-tool empty-result tracking state
- `scripts/agent/tool_runner.py` — `execute_one_tool_call()`/`_collect_tool_result_msgs()`, to report results to the guard and (optionally) apply the empty-result placeholder
- `scripts/agent/llm_turn_runner.py` — `LLMTurnRunner.run()`, wiring results into `guard.check_all()`'s per-turn state
- `scripts/agent/config_dataclasses.py` — new `ToolConfig` field
- `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md` — existing design doc enumerating the 4 (5, including the unimplemented one) guards; needs a new entry
- `tests/integration/test_rag_llm_integration.py` — existing `test_c07_tool_loop_guard_fires_on_dedup`/`test_c08_tool_loop_guard_allows_different_args` establish the test pattern to follow for the new guard

## Required Changes
- Add a new `ToolLoopGuard` method that detects N consecutive empty (or degenerate) results for the same tool name, independent of argument differences.
- Add a corresponding `ToolConfig` field with the `0 = disabled` convention, distinct from `progress_stagnation_window`.
- Wire tool execution results into the guard's per-turn state (a plumbing change, since `check_all()` currently only sees the outgoing tool-call request, not the result of the previous round).
- Add a `HINT` constant and `_save_guard_hint(...)` call matching the existing 4 guards' pattern.
- Update `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md` to document the new guard.
- (Optional, smaller, same change) Replace an empty-string tool result with an explicit placeholder before it enters conversation history.

## Constraints
- Do NOT implement or complete `_check_progress_stagnation()`'s own tool-name-set-based logic as part of this work — it is a separate, independent concern with a different detection target (see Out of Scope). Do not repurpose its `progress_stagnation_window` config field for the new guard; add a distinct field.
- Do not change the behavior of the 4 existing working guards (`check_dedup`, `check_retry`, `check_cycle`, `check_error_limit`).
- Define "empty or degenerate result" precisely before implementing (e.g. exact empty string only, vs. also whitespace-only, vs. also near-duplicate non-empty results) — this Plan should not assume byte-identical empty strings are the only case worth detecting, but must not over-broaden to flag legitimately short-but-different results as "stagnant" either.
- Avoid full-text comparison across many rounds for performance — prefer a lightweight signal (e.g. tracking only whether each round's result was empty, or a short hash/length comparison) rather than storing and diffing full result text every round.

## Acceptance Criteria
- [ ] A new `ToolLoopGuard` method detects when the same tool name returns an empty result N consecutive times (N configurable, `0` disables the check), independent of whether arguments varied between calls
- [ ] A new `ToolConfig` field controls the threshold, following the existing fields' `0 = disabled` convention, and is distinct from `progress_stagnation_window`
- [ ] The new guard does not fire when a tool's results differ meaningfully between calls, even if some individual results happen to be empty
- [ ] The new guard integrates with `check_all()`'s existing return-first-hit-or-None pattern and reuses `_finalize_after_guard()`'s existing fallback path (no new fallback mechanism)
- [ ] All 4 existing guards' current tests continue to pass unchanged
- [ ] `docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md` documents the new guard
- [ ] `_check_progress_stagnation()` remains unimplemented and unchanged by this work (tracked separately — see Out of Scope)

## Testing Expectations
- Unit/integration tests, following the existing pattern in `tests/integration/test_rag_llm_integration.py` (`test_c07_tool_loop_guard_fires_on_dedup`, `test_c08_tool_loop_guard_allows_different_args`):
  - same tool name, N consecutive empty results with varying arguments → guard fires
  - same tool name, N consecutive empty results with identical arguments → guard fires (should not depend on `check_dedup` firing first from the same evidence)
  - same tool name, results are non-empty (even if short) → guard does not fire
  - different tool names interleaved, each individually below the threshold → guard does not fire for either
  - threshold set to `0` → guard is disabled entirely
- Regression: existing `ToolLoopGuard` test suite passes unchanged
- Type check: `uv run mypy scripts/agent/tool_loop_guard.py scripts/agent/tool_runner.py scripts/agent/llm_turn_runner.py scripts/agent/config_dataclasses.py`

## Documentation Impact
`docs/05_agent_03_02_turn-processing-flow-llm-tool-loop.md` currently documents the 4 working guards (and, per the earlier investigation, likely does not yet document `_check_progress_stagnation` as it's unimplemented). This Plan should add an entry for the new guard describing its trigger condition, configuration field, and fallback behavior — following the same level of detail as the existing 4 guards' entries.

## Out of Scope
- Implementing `_check_progress_stagnation()`'s own tool-name-set-based stagnation logic — this is a separate, already-scaffolded feature with a different detection target (2+ distinct tools repeated across rounds, not single-tool empty results) and should be tracked as its own issue if pursued.
- Changing `max_tool_turns` or any of the 4 existing guards' thresholds or logic.
- Handling empty *LLM response content* (as opposed to empty *tool result* content) — `shared/json_utils.py::extract_llm_content()` already has an explicit, documented design decision that empty LLM content is valid and out of scope here.
- Any change to how Anthropic/OpenAI API request payloads are constructed beyond what's needed to insert the (optional) empty-result placeholder string.

## Dependencies
N/A: none

## Unresolved Questions
- Exact definition of "empty or degenerate result" for the new guard's detection (see Constraints) — whitespace-only and very-short-but-technically-non-empty results may also warrant detection, but this needs a design decision before implementation, not an assumption.
- Whether the optional empty-result-placeholder change (replacing `""` with an explicit message before appending to history) should ship in the same change as the new guard, or be split into a smaller, separate follow-up — both are small enough to combine, but they are logically separable.
- Default threshold value for the new `ToolConfig` field — the existing guards default to small values (2-3); an appropriate default for this new field should be chosen with the same reasoning (balance false-positive risk against how many wasted rounds are acceptable before stopping).

## AI Implementation Instruction
- Do NOT modify or attempt to complete `_check_progress_stagnation()` as part of this work — it is explicitly out of scope (see Out of Scope); a future implementer might otherwise be tempted to "finish" it while touching this area of the file.
- Do NOT reuse `progress_stagnation_window` for the new guard's threshold — add a distinct `ToolConfig` field.
- Follow the existing guard pattern exactly: a `_HINT` string constant near the top of the file, a `_save_guard_hint(...)` call recording the event to `ctx.diagnostics`, and a short string return value consistent with the existing guards' style (e.g. `"Repeated tool call detected."`).
- Confirm the exact plumbing needed to pass tool results into the guard's per-turn state before writing the guard logic — `check_all()`'s current signature only receives the outgoing `message: LLMMessage`, not the previous round's results; do not guess at this without reading `llm_turn_runner.py`'s `LLMTurnRunner.run()` loop first.
- Do not rewrite unrelated parts of `tool_loop_guard.py`, `tool_runner.py`, or `llm_turn_runner.py`.
