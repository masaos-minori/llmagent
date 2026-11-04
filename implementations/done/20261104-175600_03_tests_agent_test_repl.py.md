## Goal

Add the three entry-function tests to `tests/agent/test_repl.py`: interrupted startup returns from `main`, a genuine failure propagates, and `agent.__main__` delegates to `agent.repl.main` (REQ-004; the first test MUST fail on the pre-change code and pass after it — AC-4).

## Scope
**Release unit**: N/A: not part of a release unit

In-scope: new entry-function tests added next to `TestRunStartupInterrupted`, following the Plan `Tests` section.

## Assumptions

- The `run()` contract itself stays pinned by the existing `test_startup_interrupted_warns_and_reraises` and `test_genuine_startup_failure_still_reports_startup_failed`; this document adds entry-level tests only (verified in this cycle: no existing test calls `main` or the `__main__` module).
- Overlap judgment (`tools/check_plan_target_overlaps.py`): the partial-completion counter Plan `plans/20261104-115736_partialcount001_partial-completion-counter-dead.md` also targets this file with `_dispatch_line` warning tests in a separate class; judged compatible with this Plan's entry-function tests, no ordering needed.
- No real services start; mocks only (Plan `Tests`). `repl.py` stays in `pyproject.toml`'s coverage omit list — the new tests assert the behavior directly instead.
- Caveat (non-blocking, Needs confirmation): the delegation test must import or run `agent.__main__` while the patch on `agent.repl.main` is active, so the freshly executed module binds the patched attribute; confirm `tools/check_mock_patch_targets.py` reports no finding for the new patches (it runs as a pre-commit hook).

## Design decisions

- Patch `agent.repl.AgentREPL` so `run` raises, and call `main()` directly: the test drives the entry function, not the REPL startup path, so it needs no fixtures or services.
- Run the `agent.__main__` module through Python's runpy with `run_name="__main__"` so the delegation test executes the module exactly as `python -m agent` would.

## Alternatives considered

- Subprocess integration test spawning `python -m agent` with a signal — rejected: the Plan prescribes mocks only, and signal timing in a subprocess is flaky (Plan `Tests`).

## Implementation
### Target file
`tests/agent/test_repl.py`

### Procedure

- Add a new test class `TestMainEntry` (new) next to `TestRunStartupInterrupted` with three tests:
  1. interrupted-startup returns: patch `agent.repl.AgentREPL` so its `run` raises `StartupInterrupted`; call `main()` and assert it returns `None` (add this test first, on the pre-change code, and record that it fails — Plan Phase 1, AC-4).
  2. genuine failure propagates: patch `agent.repl.AgentREPL` so its `run` raises `RuntimeError`; assert `main()` raises it (Plan Phase 3).
  3. delegation: patch `agent.repl.main`; run the `agent.__main__` module with runpy as `__main__`; assert the patch was called exactly once (Plan Phase 3).

### Method

- Use monkeypatch or the module's existing patch style (`TestRunStartupInterrupted` neighbors show the file's conventions); keep mocks only.
- Test 1 MUST be written and run against the pre-change `repl.py` first so the failing baseline is recorded before the code documents run (Plan Phase 1 ordering); it then passes after they run.

### Details

- `StartupInterrupted` is importable from `agent.startup` (already used by this test file); `main` is imported from `agent.repl` in the test module.
- Do not modify any existing test; tests 2 and 3 pass on the pre-change code too (they pin unchanged behavior and are added in Plan Phase 3, after the entry changes).

## Compatibility considerations

- The existing `TestRunStartupInterrupted` class and all other classes pass unchanged (AC-2); the new class is additive.

## Security considerations

- N/A: test-only change, no trust boundary.

## Rollback considerations

- Revert the commit; the new class disappears with no residue in the file.

## Validation plan

- `uv run pytest tests/agent/test_repl.py -v` — all pass after the code documents run; test 1 fails before them (AC-4).
- `uv run pytest tests/agent/test_startup_rollback.py -v` — regression, all pass.
- `uv run python tools/check_mock_patch_targets.py` — no finding for the new patch targets.
- `uv run ruff format tests/agent/test_repl.py`, `uv run ruff check tests/agent/test_repl.py --fix` — clean.

## Completion criteria

- The three tests exist and pass with the changed `repl.py` and `__main__.py` (AC-1, AC-2, AC-3); test 1 was recorded as failing on the pre-change code (AC-4); no existing test was edited.

## Out of Scope

- `pyproject.toml`'s coverage omit list for `repl.py` (Plan Problem finding 4: the omission is not changed); manual end-to-end signal testing on a development host (Plan `Tests`, optional and UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add test 1 (interrupted-startup entry test) and record it failing on the current code | Completed | 20261104-211132 | 20261104-211132 | Plan step 1 (Phase 1: before the code documents run) AC-4 baseline recorded: test failed on pre-change repl.py with 'agent.startup.StartupInterrupted: shutdown requested' propagation; changed sources then restored |
| 2 | Add tests 2 and 3 (propagation, `__main__` delegation) | Completed | 20261104-211132 | 20261104-211132 | Plan step 3 (Phase 3) 3 tests added in TestMainEntry; all pass with changed repl.py/__main__.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261104-213610 | Caveat from Assumptions applies to the delegation test's patch target ruff pass; check_mock_patch_targets no findings; targeted test_repl 83 passed, test_startup_rollback 14 passed; full suite 11498 passed 7 skipped; diff-cover 100% on __main__.py, exit 0; Not run: mypy(tests/agent outside mypy path set), ast-grep not installed |

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
- **Requirement ID**: `REQ-004` (tests show the return, the propagation, and the delegation)
- **Source issue**: issues/20261031-135544_interruptexit001_startup-interrupt-exits-traceback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-103359_interruptexit001_startup-interrupt-exits-traceback.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-175600
- **Related target files**: tests/agent/test_repl.py