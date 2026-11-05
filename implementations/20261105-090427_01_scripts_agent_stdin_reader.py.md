## Goal

Expose one process-shared `StdinReader` instance through a module-level accessor in
`scripts/agent/stdin_reader.py`, so every interactive stdin call site shares the single
worker thread that already implements cancelled-request line hand-off (REQ-002: one shared
reader instance; REQ-004: direct coverage of the new accessor surface).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: a lazily created module-level accessor and a test reset hook; the `StdinReader`
  class semantics are unchanged.
- The wiring of the consumer modules is carried by sibling procedures (seq 02 `cli_view.py`,
  seq 03 `repl_input_loop.py`, seq 04 `tool_approval.py`).

## Assumptions

- REPL stdin reads are sequential (no two genuinely concurrent stdin requests), so one shared
  instance does not newly trip the "already pending" refusal (Plan Assumptions).
- The shared instance is created with the default empty prompt, and every caller passes its prompt
  per call via `read(prompt=...)`: the CLI view and the approval helper already do so (confirmed),
  and the two REPL read call sites gain it via sibling seq 03. One instance can therefore serve the
  `> `, `... `, and approval prompts.
- Consumer test suites that construct `CLIView` directly will call the reset hook in their
  fixtures after seq 02-04 wiring lands (Plan Assumptions, extended this cycle).

## Design decisions

- Module-level lazy singleton inside `agent.stdin_reader` (chosen): keeps the composition site
  `scripts/agent/repl.py` (out-of-scope per the Plan) unchanged, and the import direction stays
  within the `agent` layer — consumers already import `StdinReader` from this module, so no
  `lint-imports` contract change is needed.
- `reset_stdin_reader()` drops the module reference without joining the worker thread: the
  worker is a daemon thread that starts lazily, so a dropped instance neither blocks exit nor
  leaks a running thread (matches the class docstring's process-exit guarantee).

## Alternatives considered

- Constructor injection of one reader from the composition root — rejected by the Plan: the
  composition site is `scripts/agent/repl.py`, out-of-scope.
- Per-request reader creation/teardown — rejected by the Plan: the abandoned thread stays
  blocked in `input()` and still swallows the next tty line.

## Implementation
### Target file
`scripts/agent/stdin_reader.py`

### Procedure
Add three module-level names after the `StdinReader` class definition; do not touch the class
body, `_deliver`, or `_Waiter`.

### Method
Module-level state plus two functions with minimal typed signatures:

- `_shared_reader: StdinReader | None = None` (new) — module state holding the shared instance.
- `get_stdin_reader() -> StdinReader` (new) — when the module-level `_shared_reader` (new) is
  `None`, assign a newly constructed `StdinReader()` (default empty prompt), then return it.
- `def reset_stdin_reader() -> None:` (new) — set `_shared_reader` (new) to `None`.

### Details
- Thread-safety: the accessor is called from single-threaded REPL/approval setup paths; a plain
  lazy assignment is sufficient — no lock is added (YAGNI; the class itself owns all locking).
- Keep the existing module docstring; extend it only if the accessor needs a one-line mention.
- Follow `rules/coding.md`: type annotations on all three names, no suppression comments needed.

### Companion test files
- `tests/agent/test_stdin_reader.py`
  - Procedure: add a new test class covering accessor identity (two `get_stdin_reader()` calls
    return the same object), reset isolation (`reset_stdin_reader()` then a new call returns a
    different object), and that a reset instance starts no thread before its first read.
  - Validation: `uv run pytest tests/agent/test_stdin_reader.py -v` — all tests pass.

### Implementation Checklist
| # | Target File(s) | Action Summary | Acceptance Criteria | Status |
|---|----------------|----------------|---------------------|--------|
| 1 | scripts/agent/stdin_reader.py | `StdinReader` class unchanged; add `_shared_reader` (new) state, `get_stdin_reader()`, `reset_stdin_reader()` after the class definition. | Shared accessor returns one reader instance; per-call `prompt` arguments still override. | Pending |
| 2 | tests/agent/test_stdin_reader.py | Add a test class for accessor identity and reset isolation. | New tests pass; existing `TestRequestDrivenRead` / `TestCancelledRequestDelivery` tests unchanged. | Pending |

## Compatibility considerations

- `StdinReader.read()` contract unchanged (REQ-002/REQ-003): one read per worker, "already
  pending" refusal, daemon-thread exit guarantee, no read-ahead.
- Code that constructs its own `StdinReader` instance (existing unit tests) is unaffected: the
  accessor adds new names and changes nothing existing.

## Security considerations

N/A: no new trust boundary — the change stays inside the existing stdin reader path.

## Rollback considerations

Revert the commit; the accessor has no call sites until sibling procedures (seq 02-04) wire it,
so reverting this document's change alone is self-contained.

## Validation plan

- `uv run pytest tests/agent/test_stdin_reader.py -v` — accessor identity/isolation tests pass,
  existing `TestRequestDrivenRead` / `TestCancelledRequestDelivery` tests unchanged.
- Static gates per `rules/toolchain.md`: `uv run ruff format scripts/`, `uv run ruff check
  scripts/ tests/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`,
  `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`.

## Completion criteria

- `get_stdin_reader()` returns the identical instance across repeated calls within one process.
- `reset_stdin_reader()` restores isolation: the next accessor call yields a fresh instance.
- All tests in `tests/agent/test_stdin_reader.py` pass and the static gates are clean.

## Out of Scope

- Any change to `StdinReader` class behavior, its docstring semantics, or `read()`'s contract.
- Wiring of `scripts/agent/cli_view.py`, `scripts/agent/repl_input_loop.py`,
  `scripts/agent/tool_approval.py` (sibling procedures seq 02-04).
- `_INPUT_TIMEOUT_S` and the timeout branch in `read_multiline` (unchanged per REQ-003).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the shared accessor and reset hook per Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add accessor identity/isolation tests in the companion `tests/agent/test_stdin_reader.py` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docs carried by sibling procedure seq 07 |

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
- **Requirement ID**: REQ-002 (one process-shared reader instance), REQ-004 (accessor test coverage)
- **Source issue**: issues/20261104-112115_cliview002_stdin-line-lost-after-multiline-timeout.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-223334_cliview002_stdin-line-lost-after-multiline-timeout.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-090427
- **Related target files**: `scripts/agent/stdin_reader.py`, `tests/agent/test_stdin_reader.py`
