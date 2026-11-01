# Partial-completion counter is incremented in one place and read from another, so it is always zero

## Priority
Medium

## Summary
When an LLM stream ends with partial text, `LLMTurnRunner._handle_llm_error` increments `ctx.services_required.llm.stat_partial_completions` (an attribute of the LLM client). Everything that reports partial completions reads a different counter, `ctx.stats.stat_partial_completions`, which no code increments. As a result the REPL's "Partial LLM completion stored. Use /stats to see count." warning never appears, `/stats` always shows zero partial completions, and the session summary written at exit records zero. An unused module, `llm_transport_errors.py`, contains a second copy of the same handling. Give the counter one owner and make every reader use it.

## Background
Found during an adversarial review (`python-code-review`) of the agent REPL runtime.
- Writers: `LLMTurnRunner._handle_llm_error` (live path) and `llm_transport_errors.handle_partial_completion` (no production importer under `scripts/`; the only importer is `tests/agent/test_llm_partial_completion.py`, so the tests exercise this unused copy and not the live runner path). Both increment the LLM client's attribute. The client only initializes it to zero; it never increments it itself.
- Readers of `ctx.stats.stat_partial_completions`: `ReplInputLoop._dispatch_line` (before/after comparison that drives the warning), `commands/cmd_config_stats.py` (`/stats`), `services/context_view.py`, and `SessionPersister.persist_session_diagnostics` (`partial_completions` in the session summary).
- `ctx.stats` is a `RuntimeStats` dataclass, a separate object from the client; other statistics such as token usage are copied into it by an explicit callback (`factory._build_llm_client`), but there is no such bridge for this counter.

## Problem
Reproduction (throwaway script, not committed): run `LLMTurnRunner._handle_llm_error` with a `LLMTransportError` that has partial text, a stub LLM client object, and a real `RuntimeStats`. Observed: the client counter is 1 and `ctx.stats.stat_partial_completions` is 0. The check does not run the full REPL; the reader-side behavior follows from the code paths listed in Background.

Effects: the operator is never told that a partial answer was stored; `/stats` and the persisted summary under-report; the second copy in `llm_transport_errors.py` suggests an earlier refactor moved the logic and left both the dead module and the unbridged counter behind.

## Reason for Change
Partial completions mean the user may have seen an incomplete answer; the counter and the warning exist to make that visible. Both are silently non-functional, so the failure mode they were built to expose is invisible.

## Implementation Intent
Pick one counter as the single source of truth and route every writer and reader through it, in the same style as the token statistics already copied into `ctx.stats` (writer updates `ctx.stats`, or the client counter is the only one and every reader reads it). Remove or wire the unused `llm_transport_errors.py` so exactly one implementation of the partial-completion handling remains.

## Target Files or Areas
- `scripts/agent/llm_turn_runner.py` (`_handle_llm_error`)
- `scripts/agent/llm_transport_errors.py` (unused duplicate; do not confuse it with `scripts/shared/llm_transport_errors.py`, `LlmTransportErrorHandler`, which is a different, used module)
- `llm_turn_runner.py` and `llm_turn_executor.py` now carry the `control_message` parameter (toolexec001); account for it when editing them
- `scripts/agent/repl_input_loop.py` (`_dispatch_line`)
- `scripts/agent/commands/cmd_config_stats.py`, `scripts/agent/services/context_view.py`, `scripts/agent/session_persister.py` (readers)
- `scripts/shared/llm_client.py` (`stat_partial_completions` attribute)
- `tests/agent/` tests for the runner, `/stats`, and the REPL warning

## Required Changes
- Decide the canonical counter and update the writer or the readers so they agree.
- Make the runner and `llm_transport_errors.py` one implementation: either have the runner call the module, or delete the module and move its tests in `tests/agent/test_llm_partial_completion.py` onto the runner path.
- Add tests: a partial completion increments the counter that `/stats` and the REPL warning read; the warning appears once for a turn that ended partially and not for a normal turn.

## Constraints
- Do not change the diagnostic records written for a partial completion (`llm_transport_error`, partial-completion row).
- Keep the `ctx.stats` structure used by other statistics unchanged.
- Do not change the `LLMTransportError` type or its fields.

## Acceptance Criteria
- After a turn that ends with partial text, `/stats` shows a partial completion count of at least one and the REPL prints the warning once.
- The session summary written at exit contains the same count.
- Exactly one implementation of the partial-completion handling remains under `scripts/agent/`.
- The new tests fail on the current code and pass after the change.

## Testing Expectations
- Unit tests as above, using stubs for the LLM client and a real `RuntimeStats`.
- Run the tests for the runner, `/stats`, the input loop, and the session persister; run `ruff` and `mypy --no-namespace-packages` on the touched files; confirm with a repository search that no import of a removed module remains, and that `tests/agent/test_llm_partial_completion.py` covers the code path that production actually runs.

## Documentation Impact
Needs confirmation: check whether the agent documentation describes the `/stats` partial completion field or the REPL warning. If it does, no change is expected after the fix; if it describes a different source for the count, align it.

## Out of Scope
- How partial text is stored, shown, or retried.
- Other statistics counters.
- The streaming logic in the LLM client.

## Dependencies
N/A: none. `issues/20261003-180333_blockio001_sync-sqlite-writes-block-event-loop.md` touches `llm_turn_runner.py` for a different reason (synchronous diagnostics writes) and is independent.

## Unresolved Questions
- Which counter was meant to be canonical: `Needs confirmation`; either works as long as writers and readers agree.
- Whether `llm_transport_errors.py` is kept for a planned production caller: a repository search found no production importer, but its tests and the archived turn plans mention it, so check them before deleting.

## AI Implementation Instruction
Make writers and readers agree on one counter and remove the duplicate implementation, plus tests. Do not alter diagnostics persistence or the transport error type. Stop and report if a production caller of `llm_transport_errors.py` turns up outside the tests.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261031-180511
- **Related target files**: scripts/agent/llm_turn_runner.py, scripts/agent/llm_transport_errors.py, scripts/agent/repl_input_loop.py, scripts/agent/commands/cmd_config_stats.py, scripts/agent/services/context_view.py, scripts/agent/session_persister.py, scripts/shared/llm_client.py
