# Implementation Procedure: scripts/agent/repl_input_loop.py — share the module reader

## Goal

Wire `ReplInputLoop` to the process-shared `StdinReader` (declared by sibling seq 01) and pass
its `> ` prompt per call, so REPL reads and `CLIView` multiline reads share one worker thread and
a cancelled request's late line reaches the next read (REQ-002: one shared reader instance).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the reader construction in the constructor, the import from `agent.stdin_reader`, and
  the two `self._stdin_reader.read(...)` call sites gaining their `prompt` argument.
  (Verified 20261105: the attribute is `self._stdin_reader`; the earlier `self._reader` spelling in
  this section was a transcription error, corrected here.)
- In scope (expanded 20261105 with owner approval, per the Blocker Log finding): an autouse
  shared-reader reset fixture in `tests/agent/test_repl.py` — an additional target file discovered
  by test execution, not named in the Plan.
- Out of scope: the accessor itself (seq 01), the other consumers (seq 02, seq 04).

## Assumptions

- Neither the class nor `__init__` carries docstring text asserting ownership of a private reader
  instance (confirmed), so this change has no docstring text to update.
- Existing tests construct `ReplInputLoop` and pass unchanged after the switch (the Plan's
  Validation plan states the REPL suites pass unchanged; confirmed as a Plan claim, not yet
  executed). If any REPL-suite fixture needs editing to reset the shared reader, that file is an
  additional target file and must be raised as a Blocked step rather than edited silently.
- Disproved by execution 20261105: the REPL suites do not pass unchanged — a stale line from a
  cancelled read in one test is handed off to the next test's waiter through the shared reader.
  The blocked fixture edit was raised and approved as the scope expansion above.

## Design decisions

- Prompt moved from construction to the call sites (forced by the shared instance: one instance
  cannot carry three different constructor prompts; `read(prompt=...)` is the established override
  path, already used by `read_multiline`).
- Accessor call in the constructor rather than injection (Plan Constraint: the composition site is
  out-of-scope).

## Alternatives considered

- Keeping a private instance here too — rejected: the swallow bug crosses the `CLIView`/REPL
  hand-off, which only a shared instance fixes.

## Implementation
### Target file
`scripts/agent/repl_input_loop.py`

### Procedure
Three coordinated changes in one file:

1. Constructor: the expression that assigns a privately constructed reader instance becomes the
   accessor call `get_stdin_reader()`; the attribute name stays.
2. Import: `from agent.stdin_reader import get_stdin_reader` (new) replaces the previous import
   name from the same module.
3. Both read call sites gain the prompt argument:
   - the shutdown-raced read inside `_input_task` becomes
     `await self._stdin_reader.read(prompt="> ")`;
   - the direct read in the no-shutdown-event branch becomes
     `await self._stdin_reader.read(prompt="> ")`.

### Method
No signatures change. Only the construction expression, the import name, and the two call
expressions above.

### Details
- The exact prompt string `"> "` must match the current constructor prompt so user-visible output
  is unchanged (REQ-003).
- `_approval_read` already forwards to `CLIView` and needs no change here (seq 04 covers the
  approval path).
- Follow `rules/coding.md`; no new annotations needed.

### Companion test files
- `tests/agent/test_repl.py` (additional target file, discovered by test execution and approved
  by the owner 20261105; not named in the Plan)
  - Procedure: add a module-level autouse fixture calling `reset_stdin_reader()` before and after
    each test, restoring the reader isolation the old per-instance readers gave each test.
  - Validation: `uv run pytest tests/agent/test_repl.py tests/agent/test_repl_error_handling.py -q`
    — passes under randomized order (3 runs) and fixed order.

### Implementation Checklist
| # | Target File(s) | Action Summary | Acceptance Criteria | Status |
|---|----------------|----------------|---------------------|--------|
| 1 | scripts/agent/repl_input_loop.py | Constructor uses the shared accessor; import updated; both read call sites pass `prompt="> "`. | REPL reads use the shared instance with identical prompts. | Completed (20261105) |
| 2 | tests/agent/test_repl.py | Add the autouse shared-reader reset fixture (approved scope expansion). | REPL suites pass with test bodies unchanged, randomized and fixed order. | Completed (20261105) |

## Compatibility considerations

- REPL prompt output, shutdown racing, and multiline continuation are unchanged (REQ-003).
- `ReplInputLoop.__init__` signature unchanged.
- REPL test suites pass unchanged after the switch (Plan Test plan); fixture edits would be an
  out-of-scope target-file discovery to report, not to absorb. (Claim disproved 20261105: the
  isolation fixture edit was reported and approved; test bodies remain unchanged.)

## Security considerations

N/A: no new trust boundary.

## Rollback considerations

Revert the commit; a privately constructed reader with the constructor prompt is restored, losing
the cross-component hand-off.

## Validation plan

- `uv run pytest tests/agent/test_repl.py tests/agent/test_repl_error_handling.py -q` — REPL suites
  pass unchanged (Plan Validation plan).
- Static gates per `rules/toolchain.md`: `uv run ruff format scripts/`, `uv run ruff check
  scripts/ tests/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`,
  `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`.

## Completion criteria

- The two REPL read sites deliver prompts identically to before.
- REPL and CLI-view suites pass without modification (Plan Validation plan).

## Out of Scope

- The accessor implementation (seq 01), the `CLIView` and approval consumers (seq 02, seq 04).
- Shutdown-racing logic and input cancellation (unchanged).
- Any REPL test-suite fixture edit — was out of scope; the discovery was reported via the Blocker
  Log and approved by the owner 20261105, then brought into Scope.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewire constructor, import, and the two read call sites per Implementation > Procedure | Completed | 20261105-101800 | 20261105-102500 | adversarial verification: ctor L70 'StdinReader(prompt="> ")', bare reads L145/L192 confirmed; import L16 used only for ctor; no docstring asserts private-reader ownership (Assumption confirmed); one doc transcription error found ('self._reader' -> 'self._stdin_reader') and corrected in Scope; stale_detector clean Changed file: scripts/agent/repl_input_loop.py (ctor+import+2 read sites); static gates pass (ruff/mypy/lint-imports/pyright) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261105-103500 | REPL suites do NOT pass unchanged: 2 order-dependent failures, stale 'never' line handed off to the next test's waiter via the shared reader (baseline without this wiring: 86 pass). Fix requires an autouse reset_stdin_reader() fixture in tests/agent/test_repl.py - an additional target file per the Assumptions rule. Owner decision requested. REPL suites 86 pass (randomized x3 + fixed order) after approved fixture edit in tests/agent/test_repl.py; mypy/check_mock_patch_targets clean; Blocker Log resolved |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261105-103500 | N/A: docs carried by sibling procedure seq 07 N/A: docs carried by sibling procedure seq 07 (docs/00_index.md row 'CLI view / readline') |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | REPL suites fail order-dependently after the wiring (stale 'never' line handed to the next test's waiter through the shared reader). Requires an out-of-scope target file: `tests/agent/test_repl.py` autouse `reset_stdin_reader()` fixture (verified fix: 86 pass, randomized x3 + fixed order; experiment reverted pending owner decision). | Yes | 20261105: owner approved the scope expansion; fixture landed, suites green |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002 (shared reader wiring), REQ-003 (unchanged REPL behavior)
- **Source issue**: issues/20261104-112115_cliview002_stdin-line-lost-after-multiline-timeout.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-223334_cliview002_stdin-line-lost-after-multiline-timeout.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-090427
- **Related target files**: `scripts/agent/repl_input_loop.py`, `tests/agent/test_repl.py`