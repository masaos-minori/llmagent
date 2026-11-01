## Goal

Add a regression test to `tests/agent/test_tool_loop_guard.py` proving that
`ToolLoopGuard._save_guard_hint` does not propagate a `RuntimeError` when
`DiagnosticStore.save()` hits the sensitive-pattern refusal, and that it emits a warning
log record. Implements `REQ-001`, `REQ-002`, and the regression acceptance criterion of the
source plan.

## Scope

- Append new test(s) to `tests/agent/test_tool_loop_guard.py`. No existing test modified.
- The test drives `_save_guard_hint` (the single choke point all six guard events funnel
  through) with a `save()` that raises, and asserts containment + a warning record.

## Assumptions

- Existing `_make_ctx()` builds a `MagicMock` `ctx`; `ctx.diagnostics` is an auto-mock, so
  `ctx.diagnostics.save.side_effect = ...` installs the raising behavior.
- `_save_guard_hint` is a `@staticmethod` with signature
  `_save_guard_hint(ctx, guard_type, **fields)`; it is called as
  `ToolLoopGuard._save_guard_hint(ctx, <guard_type>, ...)`.
- The module logger is `agent.tool_loop_guard`; `caplog` captures warnings propagated to
  the root logger.
- The raising exception uses the literal message from
  `diagnostic_store.py` line 173 ("Sensitive information detected in diagnostic content
  without encryption enabled.") so the test binds the real refusal contract.

## Design decisions

- Assert against behavior (no escape + a warning record), not against call arguments: the
  property under test is containment, that the `RuntimeError` is swallowed.
- Drive `_save_guard_hint` directly for determinism; the "all six callers inherit" property
  is structural (one wrapper, six callers) and needs no per-caller test.

## Alternatives considered

- Testing via a full guard method (e.g. `check_dedup`) that reaches `_save_guard_hint`:
  rejected — the guard's trigger state adds setup noise; the direct static call pins the
  containment contract deterministically.

## Implementation
### Target file

`tests/agent/test_tool_loop_guard.py`

### Procedure

1. Add `import logging` to the test file imports (alongside the existing
   `from unittest.mock import MagicMock, patch`).
2. Append a test method (place it in an existing guard-test class or a new small class):

   ```python
   def test_save_guard_hint_does_not_propagate_on_sensitive_refusal(self) -> None:
       """A DiagnosticStore.save() sensitive-pattern refusal must not escape _save_guard_hint."""
       ctx = _make_ctx()
       ctx.diagnostics.save.side_effect = RuntimeError(
           "Sensitive information detected in diagnostic content without encryption enabled."
       )

       with caplog.at_level(logging.WARNING):
           ToolLoopGuard._save_guard_hint(ctx, "dedup", tool="write_file")

       # REQ-001: no exception propagated
       # REQ-002: a warning was logged
       assert any(r.levelno >= logging.WARNING for r in caplog.records)
   ```

3. Optionally add a second assertion that a recorded warning references the session id or
   the `guard_hint` kind, matching the procedure's log payload.

### Method

Append new test methods; add the `logging` import. No production code touched.

### Details

- Deterministic; no DB, no wall-clock dependency.
- The `caplog` fixture is provided by pytest (function-scoped); annotate the test
  parameter `caplog: pytest.LogCaptureFixture` if the file's mypy config types fixtures.
- Keep the raising message identical to `diagnostic_store.py` line 173.

## Compatibility considerations

- Existing guard tests pass unmodified; the new test is purely additive.
- The added `import logging` must not conflict with existing imports.

## Security considerations

- N/A: test-only change; the raised exception is a harmless literal string.

## Rollback considerations

- Deleting the added test method(s) reverts the file to its pre-change state; no production
  dependency.

## Validation plan

- `uv run pytest tests/agent/test_tool_loop_guard.py -x -q` then
  `uv run pytest tests/agent -x -q` (321-agent baseline + new).
- Full sequence per `rules/toolchain.md`: `ruff check`, `ruff format --check`,
  `uv run mypy` (test type-checking is enabled), `bandit`, `vulture`, `radon cc -nc`.
- Mutation spot-check: remove the `try/except` wrapper (row 1) and confirm the new test
  fails — the test must actually bind the containment behavior, per `rules/testing.md`.

## Completion criteria

- The new regression test passes; all pre-existing tests in the file pass unmodified.
- `REQ-001`: no `RuntimeError` escapes `_save_guard_hint`.
- `REQ-002`: a warning log record is produced.
- Lint/type/security gates clean.

## Out of Scope

- The production change in `scripts/agent/tool_loop_guard.py` (row 1).
- `scripts/agent/diagnostic_store.py` (reference; unchanged under option a).
- `tests/agent/test_llm_turn_runner.py` (row 4).

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
- **Related target files**: tests/agent/test_tool_loop_guard.py
