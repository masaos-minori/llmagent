## Goal

Verify the REPL `_dispatch_line` warning fires exactly once when a turn increments
the partial-completion counter and not for a normal turn, using a real `RuntimeStats`.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `_dispatch_line` (in `scripts/agent/repl_input_loop.py`) snapshots
  `ctx.stats.stat_partial_completions` before `handle_turn` and warns
  "Partial LLM completion stored. Use /stats to see count." when the value increases.
- Existing warning tests set both `ctx.services_required.llm.stat_partial_completions`
  and `ctx.stats.stat_partial_completions`.

## Design decisions

- Add dedicated `_dispatch_line` warning tests that drive a real `RuntimeStats` and
  assert the warning appears once for an incremented turn and never for a normal turn.
- Drop the client-counter stub lines from the existing warning tests.

## Alternatives considered

- Relying only on the existing side-effect-injection warning tests: rejected; a direct
  `_dispatch_line` test pins the exact counter-comparison behavior.

## Implementation
### Target file
`tests/agent/test_repl.py`

### Procedure

- Add `test_dispatch_line_warns_on_partial_increment` (new): after a turn that
  increments `ctx.stats.stat_partial_completions`, `_dispatch_line` emits one
  "Partial LLM completion stored" warning.
- Add `test_dispatch_line_no_warning_without_increment` (new): a normal turn leaves
  the counter unchanged and emits no such warning.
- Remove every `ctx.services_required.llm.stat_partial_completions` stub line in the file, not just the
  two in the warning tests: `_make_bare_repl` (L50), `test_handle_turn_partial_completion_increments_counter`
  (L297), `test_handle_turn_non_partial_completion_no_increment` (L315), `_make_wired_repl` (L494), and
  `test_stats_command_output_includes_llm_fields` (L634). Keep the `ctx.stats.stat_partial_completions`
  snapshot lines in the warning tests.

### Method

- Build a bare repl with `_make_bare_repl()`, set `repl._ctx.stats = RuntimeStats()`
  (new import `from agent.context import RuntimeStats`), raise the counter through a
  side effect on `repl._orchestrator.handle_turn` (normal case: no side effect), and
  call `repl._input_loop._dispatch_line("hello", repl._ctx)` directly — no
  `builtins.input` patch is needed. Assert on
  `repl._view.write_warning.call_args_list` (partial warnings == 1 / none).
  Insert both new tests in `TestReplLoop` after `test_partial_completion_warning_when_llm_is_none`.

### Details

- `_dispatch_line` reads `ctx.stats.stat_partial_completions`
  (`scripts/agent/repl_input_loop.py`); no client attribute is involved.

## Compatibility considerations

- N/A: test-only file.

## Security considerations

- N/A: test-only file.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Run `tests/agent/test_repl.py` and confirm the new and existing warning tests pass.

## Completion criteria

- Warning fires once on increment, never otherwise; no client-counter stub remains.

## Out of Scope

- Changing the warning text or the `/stats` reader.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-05T13:40 | 2026-11-05 | Applied tests/agent/test_repl.py: added RuntimeStats import, removed 5 client-counter stub lines (L50/297/315/494/634), added test_dispatch_line_warns_on_partial_increment and test_dispatch_line_no_warning_without_increment to TestReplLoop. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-05T13:40 | 2026-11-05 | Targeted tests green: test_repl.py 85 passed; testmon impact-selected run 707 passed, 516 deselected. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-05 | 2026-11-05 | Step 3e: run_validation_gates fast pass (check_mock_patch_targets et al.); ruff format+check clean; skipped: mypy — tests/agent not in mypy files scope. Full suite once: 11572 passed, 9 skipped. diff-cover N/A: test-only change, coverage source=scripts, no changed source lines. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-05 | 2026-11-05 | N/A: no docs/00_index.md task-scope mapping for tests/agent/test_repl.py |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-084444_06_tests_agent_test_repl.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 — verify the REPL partial-completion warning
- **Source issue**: issues/20261031-180511_partialcount001_partial-completion-counter-dead.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115736_partialcount001_partial-completion-counter-dead.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-084444
- **Related target files**: tests/agent/test_repl.py
