## Goal

Point the orchestrator partial-completion tests at the single owner
`ctx.stats.stat_partial_completions` instead of the removed client attribute.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `_make_ctx` returns a `MagicMock` context and sets several `ctx.stats.*` fields but
  not `stat_partial_completions`; the client stub sets `llm_svc.stat_partial_completions = 0`.
- The five partial-completion tests drive a partial `LLMTransportError` through
  `orch.handle_turn`.

## Design decisions

- Assert on `ctx.stats.stat_partial_completions`; initialize it in `_make_ctx` so the
  assertion reads the real accumulator.
- Drop the now-stale client-counter stub line.

## Alternatives considered

- Leaving the client-counter assertion: rejected; the attribute is deleted (companion
  document), so the assertion would fail.

## Implementation
### Target file
`tests/agent/test_orchestrator.py`

### Procedure

- In the five partial-completion tests, assert `ctx.stats.stat_partial_completions`
  instead of `ctx.services_required.llm.stat_partial_completions`.
- In `_make_ctx`, add `ctx.stats.stat_partial_completions = 0` alongside the other
  `ctx.stats.*` initializers.
- Remove the stale stub line `llm_svc.stat_partial_completions = 0` from `_make_ctx`.

### Method

- The concrete counter assertion is
  `test_partial_completion_increments_stat` (currently
  `assert ctx.services_required.llm.stat_partial_completions == 1`); change it to
  `assert ctx.stats.stat_partial_completions == 1`. The other partial tests already
  assert behavior (history, diagnostic, on_error) and need no counter change.

### Details

- If `_make_ctx` is switched to a real `RuntimeStats` for `ctx.stats`, the field
  already exists; otherwise the `MagicMock` auto-creates it once initialized.

## Compatibility considerations

- N/A: test-only file.

## Security considerations

- N/A: test-only file.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Run `tests/agent/test_orchestrator.py` and confirm the partial-completion suite passes.

## Completion criteria

- No test asserts the client counter; `ctx.stats.stat_partial_completions` is the source of truth.

## Out of Scope

- Changing non-partial (pre-stream) error tests.

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
| implementations/20261105-084444_05_tests_agent_test_orchestrator.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004 — switch orchestrator partial-completion assertions
- **Source issue**: issues/20261031-180511_partialcount001_partial-completion-counter-dead.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115736_partialcount001_partial-completion-counter-dead.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-084444
- **Related target files**: tests/agent/test_orchestrator.py
