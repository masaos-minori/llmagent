## Goal

Add three real-wiring regression tests to `tests/agent/test_repl.py` that exercise the actual `AgentREPL.__init__` construction and the now-bounded mid-turn race, so the defect this Plan fixes can no longer regress silently. Every existing fixture and case stays unchanged.

## Scope

Only `tests/agent/test_repl.py`: append the three new test classes described below. No existing test is modified, renamed, or removed; no other file changes.

## Assumptions

- Tests are written first and confirmed failing against HEAD before the production change (mutation guard: each must fail if the corresponding wiring or bound is removed).
- `pytest-asyncio` is configured (existing tests use `@pytest.mark.asyncio`).
- The two ad-hoc reproduction probes used during verification are not added to the repo (their stable form is `TestSignalDuringPromptEndsLoop` plus `repl002`'s own test, per `AGENTS.md` rule 7).

## Design decisions

- One behavior per test class, each asserting a single attributable fact: event ownership (`TestAgentREPLOwnsOneShutdownEvent`), prompt-wait interruption (`TestSignalDuringPromptEndsLoop`), mid-turn bound (`TestMidTurnSignalIsBounded`).
- The ownership test patches only the three heavy collaborators (`AgentContext`, `CLIView`, `DiagnosticStore`) so `ReplInputLoop` and `SignalHandler` stay real — this is what makes the defect visible (the existing fixtures bypass `__init__`).
- The two behavioral tests drive `ReplInputLoop.run()` end to end with a blocking `input()` stub, mirroring the pattern already in `TestReadInputShutdownRace` (`:658-671`).

## Alternatives considered

- Reusing `_make_repl_for_shutdown()` for the ownership assertion: rejected — it hand-wires `ReplInputLoop(ctx, view, shutdown_event)` directly (`:636`), exactly the path that hides the defect. The ownership test must construct `AgentREPL()` through `__init__`.

## Implementation
### Target file
`tests/agent/test_repl.py`

### Procedure
1. Locate a good insertion point after `TestReadInputShutdownRace` (`:640-706`) / before `TestRunBindsStartupResultsToInputLoop` (`:712`), or append at end of file — keep the existing classes byte-identical.
2. Add `TestAgentREPLOwnsOneShutdownEvent` (REQ-001; AC-1, AC-2).
3. Add `TestSignalDuringPromptEndsLoop` (REQ-002, REQ-007; AC-3).
4. Add `TestMidTurnSignalIsBounded` (REQ-003, REQ-004; AC-4).
5. Run all three against HEAD to confirm they fail, then against the fixed tree to confirm they pass.

### Method
- Model the new classes on the existing patterns: `_make_bare_repl()` (`:28-83`) for manual attribute assignment, `TestReadInputShutdownRace` (`:640-706`) for the blocking-input + timer pattern, and `TestRunBindsStartupResultsToInputLoop` (`:712-728`) for patching heavy collaborators around `run()`.
- Confirm the current failure mode before the fix: `grep -rn "AgentREPL()" tests/` returns nothing (no test constructs `__init__`), and the mid-turn race branch (`repl_input_loop.py:255-284`) is never entered, so `TestMidTurnSignalIsBounded` cannot pass until the bound lands.
- Use `@pytest.mark.asyncio` on every async test, matching the file convention.

### Details
- `TestAgentREPLOwnsOneShutdownEvent`:
  - Patch `agent.repl.AgentContext`, `agent.repl.CLIView`, `agent.repl.DiagnosticStore` (only these three), so `ReplInputLoop` and `SignalHandler` are constructed for real inside `AgentREPL.__init__`.
  - Construct `repl = AgentREPL()`. Assert `repl._input_loop._shutdown_event is repl._signal._shutdown_event` and `repl._input_loop._shutdown_event is not None` (AC-1).
  - Stub `repl._input_loop.run`, `repl._shutdown.close_resources`, and patch `agent.repl.StartupOrchestrator` so `await repl.run()` completes; assert the same identity holds afterward — i.e. `run()` neither re-creates the event nor rebinds `_signal` (AC-1, AC-2).
  - Also assert exactly one `asyncio.Event()` is created: `grep -cn "asyncio.Event()" scripts/agent/repl.py` returns `1` (this is a repo-level grep, run outside the test).
- `TestSignalDuringPromptEndsLoop`:
  - Drive `repl._input_loop.run(banner_callback, persister_callback)` end to end with `builtins.input` stubbed to block on a `threading.Event` that is never released, and the shared `_shutdown_event` set from a `threading.Timer`/`asyncio.sleep(0.05)` after 50 ms.
  - Assert `run()` returns within 1 s and `view.write_turn_end()` (or the `_abort_input` view call) is invoked exactly once; no keyboard input is supplied (AC-3).
  - Keep `TestReadInputShutdownRace` and `test_no_shutdown_event_fallback` (`:674-680`) unchanged as the `None`-fallback regression guard (REQ-006).
- `TestMidTurnSignalIsBounded`:
  - Two variants on one class: (a) non-cooperative `handle_turn` stub held behind `asyncio.shield(...)` so it ignores cancellation, with `_GRACEFUL_TIMEOUT_S` monkeypatched to `0.2` on the class — assert `run()` returns within 1 s, the view receives the `Graceful shutdown timed out after …s` warning, the dispatch task is in a cancelled state, and the loop does not start another turn; (b) cooperative `handle_turn` stub — assert the same assertions hold but WITHOUT the graceful-timeout warning (AC-4).
  - Monkeypatch `_GRACEFUL_TIMEOUT_S` on the `ReplInputLoop` class (REQ-004 leaves the real constant at `10.0`).

## Compatibility considerations
The three new classes are additive; no existing class, fixture, or case is touched. `TestReadInputShutdownRace` (`:640-706`) and `test_no_shutdown_event_fallback` (`:674-680`) remain the `None`-fallback guards (REQ-006). Existing `TestRunBindsStartupResultsToInputLoop` (`:712-730`) still guards the `_cmds`/`_orchestrator` rebinding.

## Security considerations
N/A: adding tests carries no security impact.

## Rollback considerations
Delete the three new classes; the suite returns to its pre-change state exactly.

## Validation plan
- Against HEAD (before the production change): `uv run pytest tests/agent/test_repl.py::TestAgentREPLOwnsOneShutdownEvent tests/agent/test_repl.py::TestSignalDuringPromptEndsLoop tests/agent/test_repl.py::TestMidTurnSignalIsBounded -q` fails (mutation guard) (AC-1, AC-3, AC-4).
- After the production change: the same three pass; `uv run pytest tests/agent/test_repl.py -q` passes; `uv run pytest tests/ -q` passes with no skipped or renamed existing case (AC-8).
- `git diff --stat tests/agent/test_repl.py` lists only this file among the target rows.

## Completion criteria
`TestAgentREPLOwnsOneShutdownEvent`, `TestSignalDuringPromptEndsLoop`, and `TestMidTurnSignalIsBounded` exist in `tests/agent/test_repl.py`, each fails against HEAD and passes against the fixed tree, and every existing fixture and case is unchanged.

## Out of Scope
`scripts/agent/repl.py`, `scripts/agent/repl_input_loop.py`, `scripts/agent/signal_handler.py` (production changes in their rows), `deploy/start_agent.sh` (operator hint, re-checked not edited), and all `docs/*.md` — byte-identical except the rows that correct them.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the three new tests and confirm they fail against HEAD | Pending | — | — | REQ-001, REQ-002, REQ-003; AC-1, AC-3, AC-4 |
| 2 | Add or update tests per Validation plan | Pending | — | — | REQ-001..REQ-004; AC-1..AC-4 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | full-suite pytest, git diff --stat |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No `docs/*.md` edit in scope (REQ-008) |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-006, REQ-007
- **Source issue**: `issues/20261021-093421_repl001_sigint-sigterm-never-reach-repl-input-loop.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-030840_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-071921
- **Related target files**: `tests/agent/test_repl.py`
