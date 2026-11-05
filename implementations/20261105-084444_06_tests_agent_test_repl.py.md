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
- In the existing warning tests, remove the
  `repl._ctx.services_required.llm.stat_partial_completions = 0` stub lines and keep
  the `ctx.stats.stat_partial_completions` snapshot.

### Method

- Build a bare repl with a real `RuntimeStats`, feed `["hello", "/exit"]` to
  `builtins.input`, and assert on `repl._view.write_warning.call_args_list`.

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
