## Goal

Point the orchestrator partial-completion tests at the single owner
`ctx.stats.stat_partial_completions` instead of the removed client attribute.

## Scope
**Release unit**: partial-counter-owner (plan Release units: Phases 2, 3 — validated and released together)

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

- In all five counter-assertion sites, assert `ctx.stats.stat_partial_completions`
  instead of `ctx.services_required.llm.stat_partial_completions`: three partial tests
  assert `== 1` (`test_partial_completion_increments_stat` L1130,
  `test_read_timeout_with_partial_increments_stat` L1246,
  `test_malformed_sse_with_partial_saves_llm_transport_diagnostic` L1292) and two
  non-partial diagnostic tests assert `== 0`
  (`test_http_retryable_prestream_saves_mid_turn_diagnostic` L1259,
  `test_http_fatal_with_status_code_saves_diagnostic` L1278).
- In `_make_ctx`, add `ctx.stats.stat_partial_completions = 0` alongside the other
  `ctx.stats.*` initializers.
- Remove the stale stub line `llm_svc.stat_partial_completions = 0` from `_make_ctx`.

### Method

- Change all five `assert ctx.services_required.llm.stat_partial_completions == N`
  lines (three `== 1`, two `== 0`, listed in Procedure) to
  `assert ctx.stats.stat_partial_completions == N`. Test behavior (history, diagnostic,
  on_error) is otherwise unchanged.

### Details

- `_make_ctx` (L109) builds a `MagicMock` context; its `ctx.stats.*` initializers sit at
  L125-132 (`ctx.stats.stat_partial_completions = 0` is added there), and the stale stub
  `llm_svc.stat_partial_completions = 0` is at L155.

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

- Behavior changes to the two non-partial (pre-stream) diagnostic tests; only their
  counter assertion lines switch to `ctx.stats` (they read the client attribute today and
  would fail once the attribute is deleted in the companion document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-05T14:35 | 2026-11-05T14:40 | Step 3b verification 2026-11-05: clean (_make_ctx L109, stats initializers L125-132, llm_svc stub L155, five assertion sites L1130/1246/1292 ==1 and L1259/1278 ==0 confirmed; stale_detector: not stale). Corrections: Method corrected to cover all five sites (procedure claimed only one); Out-of-Scope reworded (two ==0 sites must switch); unit line added. All five assertion sites switched to ctx.stats (3 ==1, 2 ==0); ctx.stats.stat_partial_completions = 0 added to _make_ctx initializers; llm_svc stub line removed. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-05T14:40 | 2026-11-05T14:42 | Targeted run 130 passed (the 3 red states from companion 01 resolved). Step 3e: ruff format+check clean; check_mock_patch_targets: no findings; skipped: mypy — tests/agent not in mypy scope. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-05 | 2026-11-05 | End-of-unit full-suite run 1: 11565 passed / 2 failed (mdq flaky per Failure Log + manifest-drift test). Allowed re-run 2: 11566 passed / 1 failed = test_live_docs_have_no_drift = allowed-red manifest drift (Failure Log), cleared by companion 08. diff-cover: scripts/agent/llm_turn_runner.py 100% (Total 1 line, Missing 0); coverage.xml written. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-05 | 2026-11-05 | N/A: no docs/00_index.md task-scope mapping for tests/agent/test_orchestrator.py |

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
