# LLMTurnRunner final-answer fallback streams to an empty LLM URL

## Priority
Medium

## Summary
When ToolLoopGuard blocks a turn, the final-answer fallback (`_finalize_after_guard`) calls `_stream_llm_final_answer`, which streams using the instance attribute `self.llm_url`. That attribute is initialized to `""` and never assigned a real value anywhere in the codebase, so the fallback streams to a blank URL instead of the configured endpoint. This issue makes the fallback use the turn's actual LLM URL.

## Background
`LLMTurnRunner` (scripts/agent/llm_turn_runner.py) has two ways of streaming an LLM response during one turn:
- `_stream_llm(llm_url, turn)` — used by the main tool-call loop in `run()`. It takes `llm_url` as a parameter and passes it to `ctx.services_required.llm.stream(...)`.
- `_stream_llm_final_answer()` — used only by `_finalize_after_guard()`, the graceful-degradation path when `ToolLoopGuard.check_all()` returns a block message (dedup / cycle / retry / stagnation / empty-result / error-limit). It calls `ctx.services_required.llm.stream(self.llm_url, ...)`.

`self.llm_url` is set to `""` in `LLMTurnRunner.__init__` and is never reassigned. The real URL is available as the `llm_url` parameter to `run()` and as `ctx.conv.llm_url` (set at startup in scripts/agent/startup_component_init.py).

## Problem
The guard-triggered final-answer path does not have access to the turn's real `llm_url`: it reads the stale, empty `self.llm_url`. Streaming to an empty URL fails with `LLMTransportError` (see `LlmReconnectHandler.stream` -> `LlmSseStreamHandler.stream_once(http, "", ...)`), so instead of producing a best-effort final answer the turn surfaces a transport error to the operator.

## Reason for Change
The guard fallback exists precisely so a turn can degrade gracefully to a final answer when the LLM keeps requesting the same/failed tool calls. With the empty URL, that degradation path is broken: every guard block currently ends in a surfaced transport error rather than a final answer. This is a correctness defect on a live runtime path. It is not caught by existing tests because `tests/agent/test_llm_turn_runner.py` asserts `stream.assert_awaited_once_with(runner.llm_url, ...)` — which passes even when `runner.llm_url` is `""`.

## Implementation Intent
Ensure the final-answer fallback uses the same LLM URL as the normal turn. Prefer one of these minimal approaches and do not introduce a second code path:
- Pass the turn's `llm_url` into `_stream_llm_final_answer` (and thus into the final stream call), OR
- Assign `self.llm_url = llm_url` at the start of `run()` so the instance attribute reflects the current turn, OR
- Read the configured URL directly via `ctx.conv.llm_url` in `_stream_llm_final_answer`.

Choose the approach that most closely mirrors how `_stream_llm` already obtains its URL, and keep the change confined to scripts/agent/llm_turn_runner.py.

## Target Files or Areas
- scripts/agent/llm_turn_runner.py (`LLMTurnRunner._stream_llm_final_answer`, `LLMTurnRunner.run`, `LLMTurnRunner.__init__`)
- tests/agent/test_llm_turn_runner.py (add a test that exercises the real method with a non-empty URL)

## Required Changes
- Make `_stream_llm_final_answer` stream to the turn's real LLM URL instead of the empty `self.llm_url`.
- Ensure `self.llm_url` is either assigned the real URL in `run()`/`__init__` callers, or no longer referenced by `_stream_llm_final_answer` (depending on chosen approach).
- Add/adjust a test so the final-answer path is verified against a non-empty URL and would fail if the URL were empty again.

## Constraints
- Do not change the normal-turn streaming path (`_stream_llm`) behavior — it already uses the correct parameter.
- Preserve the existing `_finalize_after_guard` contract: it must still return a `TurnResult(action="continue", answer=...)` on success and `action="fail"` when the final response still contains tool calls or validation fails.
- Keep the change minimal and confined to scripts/agent/llm_turn_runner.py; do not touch the workflow engine, orchestrator, or LLM client.
- Type safety must remain intact (no new casts or `Any` leaks).

## Acceptance Criteria
- `_stream_llm_final_answer` no longer passes an empty string to `llm.stream()` when a real URL is available.
- A unit test asserting the final-answer stream is called with a non-empty URL passes, and the same test fails if the URL is reverted to `""`.
- Existing `test_llm_turn_runner.py` cases still pass unchanged (no behavioral regression in the mocked paths).
- `ruff` and `bandit` remain clean on the touched file.

## Testing Expectations
- Unit test: exercise the real `_stream_llm_final_answer` (not patched) with a non-empty URL and assert `llm.stream` is awaited with that URL.
- Regression: run the full `tests/agent/test_llm_turn_runner.py` suite.
- Lint/type: `ruff check` and the repo type check on scripts/agent/llm_turn_runner.py.

## Documentation Impact
N/A: no user-facing or design documentation describes this internal URL resolution; the fix restores intended behavior without changing documented contracts.

## Out of Scope
- Changing how `self.llm_url` is used elsewhere (it is otherwise unused).
- Modifying the guard rules in scripts/agent/tool_loop_guard.py.
- Any change to LLM transport/reconnect logic in scripts/shared/.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Do not rewrite unrelated files. Inspect how `_stream_llm` obtains its URL in scripts/agent/llm_turn_runner.py, then make `_stream_llm_final_answer` use the same source (the `llm_url` parameter of `run()`, or `ctx.conv.llm_url`). Keep the change to scripts/agent/llm_turn_runner.py only. Add a test that runs the unpatched `_stream_llm_final_answer` against a non-empty URL and confirm it fails when the URL is empty. Run `ruff check` and the repo type check before finishing.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261012-130542
- **Related target files**: scripts/agent/llm_turn_runner.py, tests/agent/test_llm_turn_runner.py
