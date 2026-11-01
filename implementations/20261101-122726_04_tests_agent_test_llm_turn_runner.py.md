## Goal

Add a regression test to `tests/agent/test_llm_turn_runner.py` proving that
`LLMTurnRunner._handle_llm_error` returns a fail `TurnResult` (no propagation) when
`DiagnosticStore.save()` / `save_partial_completion()` hit the sensitive-pattern refusal,
and that it emits a warning log record. Implements `REQ-001`, `REQ-002`, and the regression
acceptance criterion of the source plan.

## Scope

- Append new test(s) to `tests/agent/test_llm_turn_runner.py`, ideally inside the existing
  `TestHandleLlmError` class (which already exercises `_handle_llm_error`). No existing
  test modified.
- Cover the partial-text branch (lines 201-216, containing both the line 202 `save()` and
  the line 209 `save_partial_completion()` raise points) and, optionally, the mid-turn
  branch (line 218).

## Assumptions

- Existing `_make_ctx()` builds a `MagicMock` `ctx`; `ctx.diagnostics` is an auto-mock, so
  `runner._ctx.diagnostics.save.side_effect = ...` and
  `runner._ctx.diagnostics.save_partial_completion.side_effect = ...` install raising
  behavior.
- The `runner` fixture returns `LLMTurnRunner(ctx, guard)` with `ctx.services_required.llm`
  an `AsyncMock`; `_handle_llm_error` is async and returns a `TurnResult`.
- `LLMTransportError(kind, phase, url, ..., partial_text="", detail="")`
  (`scripts/shared/llm_exceptions.py` lines 30-48); passing a non-empty `partial_text`
  selects the partial-text branch (`llm_turn_runner.py` line 199 `if e.partial_text:`).
- The module logger is `agent.llm_turn_runner`; `caplog` captures propagated warnings.
- The raising exception uses the literal message from `diagnostic_store.py` line 173.

## Design decisions

- Assert against behavior (no escape + a warning record + a returned `TurnResult`), not
  against call counts: the property under test is containment, that the `RuntimeError` is
  swallowed and the turn still fails gracefully.
- Exercise the partial-text branch (both raise points) primarily; add a mid-turn-branch
  case for coverage of line 218.

## Alternatives considered

- Asserting `save.assert_called_once()` (as the existing test does): rejected — under a
  raising save the call still happens but then raises; the regression must assert the
  exception did NOT propagate and a warning WAS logged, not just that it was called.

## Implementation
### Target file

`tests/agent/test_llm_turn_runner.py`

### Procedure

1. Add `import logging` to the test file imports (alongside the existing imports at the
   top).
2. Append to `TestHandleLlmError`:

   ```python
   @pytest.mark.asyncio
   async def test_handle_llm_error_does_not_propagate_on_sensitive_refusal(
       self, runner: LLMTurnRunner, caplog: pytest.LogCaptureFixture
   ) -> None:
       """A DiagnosticStore save() sensitive-pattern refusal must not escape _handle_llm_error."""
       runner._ctx.diagnostics.save.side_effect = RuntimeError(
           "Sensitive information detected in diagnostic content without encryption enabled."
       )
       runner._ctx.diagnostics.save_partial_completion.side_effect = RuntimeError(
           "Sensitive information detected in diagnostic content without encryption enabled."
       )
       error = LLMTransportError(
           "STREAMING_FAILED", "in_stream", "http://llm",
           partial_text="leaked token abc", detail="boom",
       )

       with caplog.at_level(logging.WARNING):
           result = await runner._handle_llm_error(error, 1)

       # REQ-001: no exception propagated; a fail TurnResult is still returned
       assert result.action == "fail"
       assert result.exception is error
       # REQ-002: a warning was logged
       assert any(r.levelno >= logging.WARNING for r in caplog.records)
   ```

3. Optionally add a mid-turn-branch case: construct `LLMTransportError("CONNECT_ERROR",
   "pre_stream", "http://llm")` (empty `partial_text`) with only
   `save.side_effect` set, asserting the same containment.

### Method

Append new async test methods; add the `logging` import. No production code touched.

### Details

- Deterministic; no DB, no wall-clock dependency.
- The `caplog` fixture is provided by pytest; annotate its type if the file's mypy config
  types fixtures.
- Keep the raising messages identical to `diagnostic_store.py` line 173.
- Setting both `save` and `save_partial_completion` side effects simulates the real
  `save_partial_completion` → `self.save()` raising at line 209.

## Compatibility considerations

- Existing `TestHandleLlmError` tests pass unmodified; the new test is purely additive.
- The added `import logging` must not conflict with existing imports.

## Security considerations

- N/A: test-only change; the raised exceptions are harmless literal strings.

## Rollback considerations

- Deleting the added test method(s) reverts the file to its pre-change state; no production
  dependency.

## Validation plan

- `uv run pytest tests/agent/test_llm_turn_runner.py -x -q` then
  `uv run pytest tests/agent -x -q` (321-agent baseline + new).
- Full sequence per `rules/toolchain.md`: `ruff check`, `ruff format --check`,
  `uv run mypy` (test type-checking is enabled), `bandit`, `vulture`, `radon cc -nc`.
- Mutation spot-check: remove the `try/except` wrappers (row 2) and confirm the new test
  fails — the test must actually bind the containment behavior, per `rules/testing.md`.

## Completion criteria

- The new regression test passes; all pre-existing tests in the file pass unmodified.
- `REQ-001`: no `RuntimeError` escapes `_handle_llm_error`; a fail `TurnResult` is returned.
- `REQ-002`: a warning log record is produced.
- Lint/type/security gates clean.

## Out of Scope

- The production change in `scripts/agent/llm_turn_runner.py` (row 2).
- `scripts/agent/diagnostic_store.py` (reference; unchanged under option a).
- `tests/agent/test_tool_loop_guard.py` (row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Test-only; no production change |
| 2 | Add or update tests per Validation plan | Pending | — | — | Add regression test here |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/done/20261101-111720_diagstore001_diagnostic-save-crashes-turn.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-120804_diagstore001_diagnostic-save-crashes-turn.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-122726
- **Related target files**: tests/agent/test_llm_turn_runner.py
