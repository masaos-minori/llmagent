## Goal

Move the partial-completion tests onto the live runner path so they verify
`LLMTurnRunner._handle_llm_error` against a real `RuntimeStats` instead of the deleted
handler module.

## Scope
**Release unit**: partial-counter-owner (plan Release units: Phases 2, 3; this Phase 1 test file gates and is validated with the unit)

## Assumptions

- The file currently imports `agent.llm_transport_errors` inline in nine tests and builds a
  `SimpleNamespace` context with a client counter.
- Existing helpers are reused: `_make_transport_error` (L11) constructs
  `LLMTransportError` with `partial_text`; `_make_diagnostic_store` (L43) provides the
  diagnostic stub. `_make_ctx` (L24) is replaced with a runner-shaped context.
- `_handle_llm_error` is an async method of `LLMTurnRunner`, so every rewritten test is
  `@pytest.mark.asyncio` and calls `await runner._handle_llm_error(e, turn=1)` directly;
  the increment happens inside the handler and no `run_turn` is needed.

## Design decisions

- Drive `LLMTurnRunner._handle_llm_error` directly with a real context carrying
  `RuntimeStats`, so the counter, history invariant, and diagnostic writes are all
  exercised on the code path under test.
- Keep the four required assertions: history invariant, diagnostics saved, counter
  incremented once, non-partial error leaves the counter at zero.

## Alternatives considered

- Editing the existing handler-module tests in place: rejected; the module is deleted
  (companion document), so the tests must target the runner.

## Implementation
### Target file
`tests/agent/test_llm_partial_completion.py`

### Procedure

- Remove every `from agent.llm_transport_errors import ...` statement.
- Build a real context with `RuntimeStats` (`ctx.stats.stat_partial_completions`)
  instead of the `SimpleNamespace` client counter.
- Rewrite the tests to call `LLMTurnRunner._handle_llm_error`:
  - `test_partial_completion_does_not_append_to_history` (new) — partial text is
    persisted to diagnostics, not appended to `ctx.conv.history`.
  - `test_partial_completion_saved_to_diagnostic_channel` (new) — exactly one
    `diagnostics.save` call with the `[INCOMPLETE: {kind}]` suffix.
  - `test_partial_completion_increments_stat` (new) — `ctx.stats.stat_partial_completions`
    is `1` after a partial error.
  - `test_non_partial_error_leaves_stat_at_zero` (new) — a non-partial error leaves
    the counter at `0`.

### Method

- Each test constructs an `LLMTransportError` via `_make_transport_error`, builds the
  runner as `LLMTurnRunner(ctx, MagicMock())`, and awaits `runner._handle_llm_error(e,
  turn=1)`. The context is a `SimpleNamespace` with `stats=RuntimeStats()`,
  `diagnostics=_make_diagnostic_store()`, `session.session_id`, `conv.history`, and
  `services_required` deliberately absent (the rewritten writer must not need it).
  Assert on `ctx.conv.history`, the diagnostic store, and
  `ctx.stats.stat_partial_completions`; the handler returns
  `TurnResult(action="fail")` and never raises. The five old handler-module tests that
  duplicate these four behaviors are deleted, leaving exactly the four new tests.

### Details

- Reuse the existing `_make_transport_error` helper; no new shared helper is needed.

## Compatibility considerations

- N/A: test-only file; no production impact.

## Security considerations

- N/A: test-only file.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Run `tests/agent/test_llm_partial_completion.py` and confirm all cases pass.
- Confirm no remaining import of `agent.llm_transport_errors`.
- Expected red state before companion document 01 lands: `test_partial_completion_increments_stat`
  fails (`AttributeError`: the current writer reads `ctx.services_required.llm`, absent on the
  new context). This failure is the Phase 1 red-state evidence the plan requires.

## Completion criteria

- All four behaviors verified against the runner; no reference to the deleted module.

## Out of Scope

- Adding tests for non-partial transport handling beyond the counter-at-zero case.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-05T14:10 | 2026-11-05T14:10 | Step 3b verification 2026-11-05: clean (helpers L11/L24/L43 and 9 inline imports confirmed; stale_detector: not stale). Corrections: async contract added (await runner._handle_llm_error(e, turn=1), LLMTurnRunner(ctx, MagicMock()), services_required deliberately absent); 4-test inventory explicit, 5 duplicate old tests deleted; unit line extended; pre-01 red state = Phase 1 AC-4 evidence. File rewritten: 4 async tests on LLMTurnRunner._handle_llm_error; 5 duplicate handler-module tests deleted; _make_ctx now carries a real RuntimeStats and no services_required. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-05T14:12 | 2026-11-05T14:15 | Targeted run 1 passed / 3 failed; failures are the allowed red state in the Failure Log (Phase 1 AC-4 evidence, resolved by companion 01). Step 3e: ruff format+check clean after --fix import sort; check_mock_patch_targets: no findings; skipped: mypy — tests/agent not in mypy scope. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-05 | 2026-11-05 | End-of-unit full-suite run 1: 11565 passed / 2 failed (mdq flaky per Failure Log + manifest-drift test). Allowed re-run 2: 11566 passed / 1 failed = test_live_docs_have_no_drift = allowed-red manifest drift (Failure Log), cleared by companion 08. diff-cover: scripts/agent/llm_turn_runner.py 100% (Total 1 line, Missing 0); coverage.xml written. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-05 | 2026-11-05 | N/A: no docs/00_index.md task-scope mapping for tests/agent/test_llm_partial_completion.py |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Failure Log
| Step | Approach attempted | Error received | Reason / allowed-red attribution |
|------|--------------------|----------------|----------------------------------|
| 4 | Run rewritten tests before companion 01 lands (3 failed, 1 passed) | `AttributeError: 'types.SimpleNamespace' object has no attribute 'services_required'` at `llm_turn_runner.py` L239 on all three partial tests | Allowed red state (batch mode): the current writer still increments the client attribute; the plan Phase 1 requires these tests to fail before Phase 2 (AC-4 evidence). Resolved by companion 01; green confirmed in the end-of-unit full-suite run |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-084444_04_tests_agent_test_llm_partial_completion.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004 — move the partial-completion tests onto the runner path
- **Source issue**: issues/20261031-180511_partialcount001_partial-completion-counter-dead.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115736_partialcount001_partial-completion-counter-dead.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-084444
- **Related target files**: tests/agent/test_llm_partial_completion.py
