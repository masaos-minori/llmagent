# Implementation Procedure: scripts/agent/cli_view.py — share the module reader

## Goal

Wire `CLIView` to the process-shared `StdinReader` exposed by `scripts/agent/stdin_reader.py`
(seq 01), so a line typed during a multiline timeout is delivered to the next read wherever it
arrives (REQ-002: one shared reader instance).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the reader construction site in the `CLIView` constructor and one import line; the
  timeout branch and every `read(prompt=..., timeout=...)` call shape stay as they are.
- Out of scope: the accessor itself (seq 01), the other consumers (seq 03, seq 04).

## Assumptions

- `CLIView` currently builds its own `StdinReader` instance in the constructor and passes
  `prompt="... "` per call (confirmed: constructor call site and the `read_multiline` call both
  use that shape), so switching to the shared instance preserves prompt behavior.
- Test fixtures in the companion file construct `CLIView` directly and will call
  `reset_stdin_reader()` in their fixtures after this wiring lands (Plan Assumptions, extended
  this cycle).

## Design decisions

- Keep the `self._stdin_reader` attribute and change only its source of construction (chosen):
  smallest diff, every existing `self._stdin_reader.read(...)` call site stays untouched, and the
  per-call `prompt` argument remains the place where `... ` is set.
- Import direction unchanged: the consumer still imports from `agent.stdin_reader`, so the
  `lint-imports` contract is untouched.

## Alternatives considered

- Constructor injection from the composition root — rejected by the Plan: the composition site is
  `scripts/agent/repl.py`, out-of-scope.

## Implementation
### Target file
`scripts/agent/cli_view.py`

### Procedure
Replace the reader construction in the `CLIView` constructor with the shared accessor call
`get_stdin_reader()` (declared by sibling seq 01), and change the module's import from
`agent.stdin_reader` accordingly:

```python
# After (constructor body):
self._stdin_reader = get_stdin_reader()
```

No other statement changes; `prompt="... "` stays a per-call argument at every
`self._stdin_reader.read(...)` call site.

### Method
- Constructor: the expression that assigned a privately constructed reader instance becomes the
  accessor call `get_stdin_reader()`; the attribute name and type stay identical.
- Import: `from agent.stdin_reader import get_stdin_reader` (new) replaces the previous import
  name from the same module.

### Details
- Do not touch `_INPUT_TIMEOUT_S` or the partial-input fallback in `read_multiline` (REQ-003).
- The class docstring and method signatures are unchanged.
- Follow `rules/coding.md`: no new annotations needed (the accessor call returns the typed
  instance).

### Companion test files
- `tests/test_cli_view.py`
  - Procedure: add a regression test that the shared reader delivers a line typed during a
    multiline timeout to the next fresh `CLIView` read. Reuse the existing sync style of
    `TestReadMultilineTimeout` (a `threading.Event`-based `release.wait` sync, no timing
    assumptions): the timed-out read must release before the follow-up read starts, so the test
    is deterministic even if another suite leaves a line pending. Patch a sub-second
    `_INPUT_TIMEOUT_S` via `monkeypatch` to keep the suite fast. Fixture calls
    `reset_stdin_reader()` before each test to guarantee fresh-reader isolation (Plan Test plan).
  - Validation: `uv run pytest tests/test_cli_view.py -v` — new and existing tests pass.

### Implementation Checklist
| # | Target File(s) | Action Summary | Acceptance Criteria | Status |
|---|----------------|----------------|---------------------|--------|
| 1 | scripts/agent/cli_view.py | Constructor uses `get_stdin_reader()`; import updated to the accessor. | `CLIView` shares the module reader; prompt behavior unchanged. | Pending |
| 2 | tests/test_cli_view.py | Add the timeout-then-fresh-read regression test with fixture isolation. | New test passes deterministically; existing tests pass unchanged. | Pending |

## Compatibility considerations

- REQ-003/REQ-004: all existing `read_multiline` unit tests keep passing; the new test only
  exercises the shared-instance path (Plan Test plan).
- `CLIView.__init__` signature is unchanged, so every existing construction site (including
  `scripts/agent/repl_input_loop.py`) keeps working.
- After this change, `CLIView` no longer constructs its own reader instance; tests that want an
  isolated reader construct one locally instead (Plan Test plan).

## Security considerations

N/A: no new trust boundary.

## Rollback considerations

Revert the commit; the constructor reverts to a privately constructed reader, restoring the
pre-change isolation at the cost of the hand-off behavior.

## Validation plan

- `uv run pytest tests/test_cli_view.py -v` — all pass.
- `uv run pytest tests/agent/test_stdin_reader.py tests/agent/test_repl.py -v` — consumer suites
  still pass after the wiring (Plan Test plan).
- Static gates per `rules/toolchain.md`: `uv run ruff format scripts/`, `uv run ruff check
  scripts/ tests/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`,
  `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`.

## Completion criteria

- A line typed after a `read_multiline` timeout is delivered to the next `CLIView` read in the
  same process (the Plan's repro sequence passes end-to-end once all consumers are wired).
- `tests/test_cli_view.py` and the reader unit tests pass unchanged or with only the new test
  added.

## Out of Scope

- The accessor implementation (seq 01) and the other consumers (seq 03, seq 04).
- `_INPUT_TIMEOUT_S` value and timeout semantics (REQ-003: unchanged).
- Constructor injection from the composition root (Plan Constraint).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewire the constructor and import per Implementation > Procedure/Method | Completed | 20261105-101500 | 20261105-101500 | adversarial verification: all doc claims confirmed against source (ctor L115 'StdinReader(prompt="... ")' single construction site; single read call site L287 passes per-call prompt; import L20 used only for ctor; companion class TestReadMultilineTimeout exists, same-view second-read case already covered by test_timeout_then_second_read); stale_detector clean Changed files: scripts/agent/cli_view.py, tests/test_cli_view.py |
| 2 | Add the regression test and fixture reset in the companion test file | Completed | 20261105-101500 | 20261105-101655 | 60 passed incl. new hand-off test; deterministic x3; consumer suites test_stdin_reader+test_repl 99 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261105-101655 | ruff/mypy/lint-imports/bandit/pyright/check_mock_patch_targets/gates pass; testmon 60 selected; F401 fix: identity assertion now uses get_stdin_reader() |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261105-101655 | N/A: docs carried by sibling procedure seq 07 N/A: docs carried by sibling procedure seq 07 (docs/00_index.md row 'CLI view / readline') |

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
- **Requirement ID**: REQ-002 (shared reader wiring), REQ-003/REQ-004 (unchanged contracts and tests)
- **Source issue**: issues/20261104-112115_cliview002_stdin-line-lost-after-multiline-timeout.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-223334_cliview002_stdin-line-lost-after-multiline-timeout.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-090427
- **Related target files**: `scripts/agent/cli_view.py`, `tests/test_cli_view.py`