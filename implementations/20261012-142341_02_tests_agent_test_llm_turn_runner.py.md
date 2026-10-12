# Implementation Procedure

<!-- This is a generated file. Do not edit by hand — regenerate from the plan via tools/generate_workitem.py. -->

## Goal

Add/adjust a unit test that verifies the guard-triggered final-answer path streams to a non-empty LLM URL and fails if the URL is reverted to `""`, locking in the fix implemented in `scripts/agent/llm_turn_runner.py` (doc 01).

## Scope

Modify `tests/agent/test_llm_turn_runner.py` only. In `TestStreamLlmFinalAnswer`:
- Set a non-empty `runner.llm_url` in the existing `test_streams_without_tool_defs` so its `assert_awaited_once_with` checks a real URL instead of the default `""`.
- Add a dedicated test that runs the unpatched `_stream_llm_final_answer()` against a non-empty URL and asserts `llm.stream` is awaited with that exact URL.

## Assumptions

- Doc 01 assigns `self.llm_url = llm_url` in `run()`, so `_stream_llm_final_answer()` reads the current turn's real URL. This test locks in that `_stream_llm_final_answer` reads `self.llm_url`.
- The `runner` fixture (`tests/agent/test_llm_turn_runner.py` lines 44-48) yields a fresh `LLMTurnRunner` whose `llm_url` defaults to `""`; tests set it explicitly.

## Design decisions

- Minimal, direct-call coverage: exercise the real `_stream_llm_final_answer()` (do not patch it) and assert the awaited URL. This catches a revert where the method reads `""`.
- Distinct assertions per test to avoid redundancy:
  - Updated `test_streams_without_tool_defs` asserts `runner.llm_url` (whatever the caller set) — verifies the method reads the instance attribute.
  - New test asserts the literal configured URL string — verifies the value flows through unchanged.
- Both tests keep `llm.stream` patched with an `AsyncMock(return_value=...)` so only the URL argument is observed.

## Alternatives considered

- End-to-end `runner.run("http://llm", workflow_id=..., task_id=..., stage_id=..., attempt_id=...)` with unpatched `_stream_llm_final_answer`: strongest guard, exercises the full `run()` → `_finalize_after_guard()` → `_stream_llm_final_answer()` chain and would catch a revert of doc 01's `run()` assignment. Noted as a recommended enhancement below; the plan's REQ-002 scope is the direct-call approach.
- Patching `_stream_llm_final_answer` (as `TestFinalizeAfterGuard` does): would NOT observe the URL. Rejected for these tests.

## Implementation
### Target file
`tests/agent/test_llm_turn_runner.py`

### Procedure
1. Open `tests/agent/test_llm_turn_runner.py`.
2. Locate `class TestStreamLlmFinalAnswer` (lines 72-96) and its `test_streams_without_tool_defs` (lines 73-88).
3. In `test_streams_without_tool_defs`, set a non-empty URL before calling the method under test. Insert `runner.llm_url = "http://llm"` after the stream patch (line 79) and before `response = await runner._stream_llm_final_answer()` (line 81). The existing assertion at lines 84-88 (`assert_awaited_once_with(runner.llm_url, ...)`) then checks `"http://llm"` instead of `""`.
4. Add a new test method `test_streams_final_answer_to_configured_url` immediately after `test_streams_without_tool_defs` (before `test_propagates_transport_error` at line 90). It sets `runner.llm_url = "http://llm"`, patches `llm.stream` with `AsyncMock(return_value=...)`, awaits the unpatched `_stream_llm_final_answer()`, and asserts `assert_awaited_once_with("http://llm", runner._ctx.conv.history, [])`.
5. Leave `TestFinalizeAfterGuard` tests unchanged — they set `runner.llm_url = "http://llm"` but patch `_stream_llm_final_answer`, so they do not observe the URL and are unaffected.

### Method
- `TestStreamLlmFinalAnswer.test_streams_without_tool_defs` currently leaves `runner.llm_url` at its `""` default, so `assert_awaited_once_with(runner.llm_url, ...)` passes even when the production code passes `""` (the bug). Setting `runner.llm_url = "http://llm"` makes the assertion check the real URL.
- The new test uses the literal `"http://llm"` in its assertion (not `runner.llm_url`) so it verifies the configured value propagates verbatim, complementing the updated test.
- Keep `llm.stream` patched in both tests; only the URL argument is asserted.

### Details
- Root cause locked in: doc 01 makes `_stream_llm_final_answer()` read the real `self.llm_url` (see `scripts/agent/llm_turn_runner.py` line 236). These tests assert that read is non-empty.
- Existing `test_propagates_transport_error` (lines 90-96) already runs the unpatched method but only checks the exception, not the URL — leave it as-is; it complements the new URL assertions.
- Do not modify `TestStreamLlm`, `TestFinalizeAfterGuard`, or any production code.

## Compatibility considerations
N/A — test-only change. No production contract impact.

## Security considerations
N/A — no new input handling or credential path.

## Rollback considerations
Revert the test edits (remove the `runner.llm_url` assignment and the new test method).

## Validation plan
- Run the affected class: `uv run pytest tests/agent/test_llm_turn_runner.py::TestStreamLlmFinalAnswer` — `llm.stream` is awaited with a non-empty URL; both tests pass.
- Verify the guard works: temporarily revert doc 01's `self.llm_url` assignment (or set `runner.llm_url = ""`) and confirm the new/updated test fails.
- Regression: full `uv run pytest tests/agent/test_llm_turn_runner.py` suite passes (AC-3).

## Completion criteria
- Updated `test_streams_without_tool_defs` sets a non-empty `runner.llm_url` and asserts `llm.stream` awaited with that URL.
- New `test_streams_final_answer_to_configured_url` runs the unpatched `_stream_llm_final_answer()` against `"http://llm"` and asserts the awaited URL.
- Full `tests/agent/test_llm_turn_runner.py` suite passes; reverting the URL to `""` fails the new/updated test.

## Out of scope
Production code (`scripts/agent/llm_turn_runner.py` is covered by doc 01), other test classes' behavior, and the `run()` call chain.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Out of scope |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/done/20261012-130542_NC-001_llmturnrunner-final-answer-uses-empty-llm-url.md (archived to issues/done/)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-131924_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-142341
- **Related target files**: tests/agent/test_llm_turn_runner.py
