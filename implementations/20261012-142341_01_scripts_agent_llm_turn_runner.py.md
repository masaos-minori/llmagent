# Implementation Procedure

<!-- This is a generated file. Do not edit by hand — regenerate from the plan via tools/generate_workitem.py. -->

## Goal

Make the ToolLoopGuard-triggered final-answer fallback stream to the turn's real LLM URL instead of the uninitialized empty `self.llm_url`, so a guard-blocked turn degrades to a final answer instead of surfacing an `LLMTransportError`.

## Scope

Modify `scripts/agent/llm_turn_runner.py` only. Assign `self.llm_url = llm_url` at the start of `LLMTurnRunner.run()`, immediately after the workflow-context guard, so the instance attribute tracks the current turn's URL. Leave `_stream_llm()` unchanged.

## Assumptions

- The `llm_url` passed to `run()` equals the turn's configured URL (threaded from `handle_llm_turn` / `ctx.conv.llm_url`).
- A fresh `LLMTurnRunner` is instantiated per turn, so assigning `self.llm_url` cannot leak across turns.
- `self.llm_url` is otherwise unused elsewhere in the class.

## Design decisions

- Chosen approach (single, per plan REQ-001): assign `self.llm_url = llm_url` once at the start of `run()`, right after the workflow-context guard. This makes the existing `self.llm_url` read inside `_stream_llm_final_answer()` resolve to the current turn's real URL without touching any signature.
- No second URL-resolution code path is introduced; the fix is one assignment.
- No change to `run()`'s signature, return type, or the normal-turn path.

## Alternatives considered

- Option A — thread `llm_url` through `_finalize_after_guard(llm_url)` into `_stream_llm_final_answer(llm_url)`: correct but requires two extra signature changes and a call-site update. Superseded by Option B (plan).
- Option C — read `ctx.conv.llm_url` directly inside `_stream_llm_final_answer()`: decouples the final-answer path from the `run()` parameter and diverges from `_stream_llm()`'s URL source. Superseded by Option B.

## Implementation
### Target file
`scripts/agent/llm_turn_runner.py`

### Procedure
In `LLMTurnRunner.run()`, add exactly one assignment — `self.llm_url = llm_url` — immediately after the workflow-context guard block and before `ctx = self._ctx`. Leave every other method unchanged, including `_stream_llm()`.

### Method
1. Open `scripts/agent/llm_turn_runner.py`.
2. Locate `LLMTurnRunner.__init__` — confirm `self.llm_url: str = ""` at line 59 (the uninitialized default that causes the bug).
3. Locate `async def run(self, llm_url: str, *, workflow_id, task_id, stage_id, attempt_id)` starting at line 63.
4. Locate the workflow-context guard at lines 73–78 (raises `RuntimeError` when any of `workflow_id/task_id/stage_id/attempt_id` is empty).
5. Insert `self.llm_url = llm_url` between the guard's closing line (78) and `ctx = self._ctx` (line 79). Resulting order: guard → `self.llm_url = llm_url` → `ctx = self._ctx` → `state = TurnLoopState()`.
6. Confirm the call chain reaches the fixed field: `run()` → `_finalize_after_guard()` (line 241) → `_stream_llm_final_answer()` (line 231), which reads `self.llm_url` at line 236 when calling `ctx.services_required.llm.stream(self.llm_url, ctx.conv.history, [])`.
7. Confirm `_stream_llm(llm_url, turn)` (lines 277–295) still receives its URL as a parameter and is untouched.

### Details
- Root cause: `self.llm_url` is initialized to `""` in `__init__` (line 59) and never reassigned, so `_stream_llm_final_answer()` passes `""` to `llm.stream()`. An empty URL flows through `LlmReconnectHandler.stream(http, url)` → `LlmSseStreamHandler.stream_once(http, url)` and surfaces as an `LLMTransportError` on a guard-blocked turn.
- After the fix: `run()` receives the real `llm_url` parameter (line 65) and threads it into `self.llm_url`, so both the normal-turn path (`_stream_llm`, line 84/291) and the guard-triggered final-answer path (`_stream_llm_final_answer`, line 236) use the same, non-empty URL.
- No cross-turn leak risk: `handle_llm_turn` (`scripts/agent/llm_turn_executor.py`) instantiates a fresh `LLMTurnRunner` per turn.
- Complexity note: `run()` is already the most complex method in the class (radon C≈13); this change adds one statement and does not increase control-flow complexity.

## Compatibility considerations
N/A — private method (`_stream_llm_final_answer`) and an instance attribute only. No public/runtime-facing interface change; `run()`'s signature and return type are unchanged.

## Security considerations
N/A — no new input handling or credential path. The URL source is unchanged; the fix only ensures the existing source value is used rather than a hardcoded empty string.

## Rollback considerations
Revert the single added assignment (`self.llm_url = llm_url`) in `run()`. The rest of the file is unchanged.

## Validation plan
- Unit: the updated test in `tests/agent/test_llm_turn_runner.py` (`TestStreamLlmFinalAnswer`) asserts `llm.stream` is awaited with a non-empty URL, so a revert of this assignment fails the suite.
- Lint: `ruff check scripts/agent/llm_turn_runner.py` clean.
- Security scan: `bandit -r scripts/agent/llm_turn_runner.py` reports 0 issues.
- Type: repo type check on `scripts/agent/llm_turn_runner.py` passes.
- Regression: full `tests/agent/test_llm_turn_runner.py` suite passes.

## Completion criteria
- `self.llm_url = llm_url` is assigned at the start of `run()` after the workflow-context guard.
- `_stream_llm_final_answer()` no longer passes `""` to `llm.stream()` when a real URL is available; a guard-blocked turn produces a final answer.
- `ruff` and `bandit` clean on the touched file; full test suite passes.

## Out of scope
`_stream_llm()` (normal-turn path already correct), `ToolLoopGuard` rules (`scripts/agent/tool_loop_guard.py`), LLM transport/reconnect logic in `scripts/shared/`, other uses of `self.llm_url`, and any `docs/*.md` / `deploy.sh` updates.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by `tests/agent/test_llm_turn_runner.py` (doc 02) |
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
- **Requirement ID**: REQ-001
- **Source issue**: issues/done/20261012-130542_NC-001_llmturnrunner-final-answer-uses-empty-llm-url.md (archived to issues/done/)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-131924_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-142341
- **Related target files**: scripts/agent/llm_turn_runner.py
