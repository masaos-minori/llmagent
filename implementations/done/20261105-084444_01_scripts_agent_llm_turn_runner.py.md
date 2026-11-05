## Goal

Give the partial-completion counter a single owner: the live runner increments
`ctx.stats.stat_partial_completions`, which every reader already reads, so `/stats`,
the REPL warning, and the exit session summary all report the same value.

## Scope
**Release unit**: partial-counter-owner (plan Release units: Phases 2, 3 — validated and released together)

## Assumptions

- `RuntimeStats.stat_partial_completions` already exists on the context and is the
  field every reader consumes.
- The diagnostic-row persistence and best-effort logging inside
  `_handle_llm_error` are unchanged; only the increment target moves.

## Design decisions

- Own the counter on `RuntimeStats`, not on the LLM client attribute, so the writer
  and all readers share one field (`REQ-001`).
- Change only the increment expression; leave the partial/non-partial branching and
  diagnostic writes intact.

## Alternatives considered

- Incrementing the client attribute and keeping a parallel `RuntimeStats` field:
  rejected; two owners reintroduce the drift this Plan removes.
- Adding a new `RuntimeStats` field: rejected; the field already exists.

## Implementation
### Target file
`scripts/agent/llm_turn_runner.py`

### Procedure

- In `_handle_llm_error`, replace
  `ctx.services_required.llm.stat_partial_completions += 1`
  with `ctx.stats.stat_partial_completions += 1`.

### Method

- The change is a single-target swap at `scripts/agent/llm_turn_runner.py` L239, which
  sits inside the `if e.partial_text:` branch as a sibling statement after the
  `if ctx.diagnostics is not None:` block (the two diagnostic `try/except` blocks at
  L206-238), not inside any `try/except` wrapper. Only the increment target changes.

### Details

- `RuntimeStats.stat_partial_completions` is defined on `AgentContext.stats`
  (`scripts/agent/context.py`); all four readers read `ctx.stats.stat_partial_completions`.
- Keep the `await ctx.diagnostics.save(...)` calls and the `logger.warning` guard
  unchanged.

## Compatibility considerations

- Readers are unaffected; they already read `ctx.stats`. The removed client attribute
  is deleted in the companion `scripts/shared/llm_client.py` document.

## Security considerations

- N/A: no auth, secret, or input-handling change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Run the runner-path partial-completion tests and the orchestrator partial tests.
- Confirm `/stats`, the REPL warning, and the exit summary still report the count.

## Completion criteria

- `_handle_llm_error` increments `ctx.stats.stat_partial_completions`; no remaining
  writer touches the client attribute.

## Out of Scope

- Any change to how partial text is stored, shown, or retried.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-05T14:20 | 2026-11-05T14:25 | Step 3b verification 2026-11-05: clean (L239 increment confirmed; stale_detector: not stale). Corrections: Method row corrected (increment is a sibling after the diagnostics if-block L206-238, not inside a try/except wrapper); Scope extended to unit partial-counter-owner. L239 changed to ctx.stats.stat_partial_completions += 1; single-line swap as corrected in Method row. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-05T14:25 | 2026-11-05T14:30 | test_llm_partial_completion.py 4 passed after the move; test_llm_turn_runner.py green; test_orchestrator.py 3 failed / 127 passed = allowed red state (Failure Log, resolved by companion 05). Step 3e: ruff clean; mypy --no-namespace-packages scripts/ tests/eventbus clean (491 files); generate_reference_table.py --check: no drift; skipped: lint-imports, bandit — no import or security-relevant change in a single-line expression swap. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-05 | 2026-11-05 | End-of-unit full-suite run 1: 11565 passed / 2 failed (mdq flaky per Failure Log + manifest-drift test). Allowed re-run 2: 11566 passed / 1 failed = test_live_docs_have_no_drift = allowed-red manifest drift (Failure Log), cleared by companion 08. diff-cover: scripts/agent/llm_turn_runner.py 100% (Total 1 line, Missing 0); coverage.xml written. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-05 | 2026-11-05 | N/A: no docs/00_index.md task-scope row naming llm_turn_runner.py; counter prose in agent_03_03 already cites ctx.stats; stale-name corrections are companions 07/08 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Failure Log
| Step | Approach attempted | Error received | Reason / allowed-red attribution |
|------|--------------------|----------------|----------------------------------|
| 4 | Run tests/agent/test_orchestrator.py after the writer moved (3 failed, 127 passed) | Assertion `ctx.services_required.llm.stat_partial_completions == 1` fails in test_partial_completion_increments_stat, test_read_timeout_with_partial_increments_stat, test_malformed_sse_with_partial_saves_llm_transport_diagnostic | Allowed red state (batch mode): the writer no longer touches the client attribute; the assertions themselves are switched by companion 05. The two `== 0` sites stay green. Resolved by 05; green confirmed in the end-of-unit full-suite run |
| 4 | End-of-unit full-suite run 1: tests/mcp_servers/mdq/test_mdq_index_serialization.py::test_is_indexing_warning_visible_during_active_index failed under suite load | Failure occurred only inside the full-suite run | Flaky classification: passes 4/4 when the file is run standalone; did not reproduce in the full-suite re-run (run 2: 1 failed, a different test). Unrelated to this unit's files; evidence recorded, no fix attempted |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-084444_01_scripts_agent_llm_turn_runner.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 — give the partial-completion counter one owner
- **Source issue**: issues/20261031-180511_partialcount001_partial-completion-counter-dead.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115736_partialcount001_partial-completion-counter-dead.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-084444
- **Related target files**: scripts/agent/llm_turn_runner.py
