## Goal

Move the partial-completion tests onto the live runner path so they verify
`LLMTurnRunner._handle_llm_error` against a real `RuntimeStats` instead of the deleted
handler module.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The file currently imports `agent.llm_transport_errors` in nine tests and builds a
  `SimpleNamespace` context with a client counter.
- The helper `_make_transport_error` already exists and can construct
  `LLMTransportError` with `partial_text`.

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

- Each test constructs an `LLMTransportError` via `_make_transport_error`, runs
  `_handle_llm_error`, and asserts on `ctx.conv.history`, the diagnostic store, and
  `ctx.stats.stat_partial_completions`.

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

## Completion criteria

- All four behaviors verified against the runner; no reference to the deleted module.

## Out of Scope

- Adding tests for non-partial transport handling beyond the counter-at-zero case.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

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
