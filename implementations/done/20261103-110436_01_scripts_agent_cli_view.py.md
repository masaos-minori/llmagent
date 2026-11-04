## Goal

Make `CLIView.read_multiline` return the accumulated text when the 30-second continuation
read times out, by replacing the uncaught `raise KeyboardInterrupt` with the EOF-style
`break` (REQ-001; AC-1), keeping every other branch and the method contract unchanged
(REQ-002; AC-3). Companion regression tests prove the graceful return and the follow-up
read (REQ-003; AC-1, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit

Covers both `scripts/agent/cli_view.py` (seq 01) and its companion test row
`tests/test_cli_view.py` (seq 02, companion-eligible, no document of its own) of
`plans/20261101-142849_cliview001_multiline-input-timeout-crashes-repl.md`. Execution
order within this document: write the red companion tests first (Procedure 1), confirm
they fail against the unmodified method, then apply the code change (Procedure 2-3), then
run the validation sequence.

## Assumptions
- Verified against current source (20261103): the `except TimeoutError:` branch logs
  "Multiline input timed out" then `raise KeyboardInterrupt` (`scripts/agent/cli_view.py`
  289-291); the sibling `except (EOFError, KeyboardInterrupt): break` (292-293); the
  `while True` loop (284) ends at the shared `return "\n".join(parts)` (301); the
  continuation variable is `cont` (286); the docstring states "On TimeoutError, raises
  KeyboardInterrupt to allow user interruption" (280-281).
- The sole caller `ReplInputLoop._read_input` awaits `read_multiline` outside any `try`
  (`scripts/agent/repl_input_loop.py:198`), and `_repl_loop`'s per-turn handlers cover only
  `TimeoutError`, `ConversationPersistenceError` and `Exception` (311-318), so the raw
  `KeyboardInterrupt` (`BaseException`) escapes to `asyncio.run(AgentREPL().run())`
  (`scripts/agent/repl.py:162`) — the Plan's Problem statement holds.
- Plan Design verification confirmed: `TestCancelledRequestDelivery` exists
  (`tests/agent/test_stdin_reader.py:86`), and `tests/agent/test_repl.py` mocks
  `read_multiline` with `AsyncMock` (77, 492, 626), so no other test depends on the raise
  contract.
- Static baselines confirmed: `radon cc` ranks `CLIView.read_multiline` B(6); bandit
  reports exactly two assert_used findings in `cli_view.py` unrelated to
  `read_multiline`; module size 11020 B (gate 20480 B).
- UNK-01 (non-blocking): `CLIView` and `ReplInputLoop` each own a separate `StdinReader`
  (`... ` and `> `), so after a timeout the stale `... ` thread stays blocked in `input()`
  and could consume and discard a line typed at the next prompt; whether this occurs on a
  real terminal is unknown. Per the Plan: settle with a pty-driven check (not the
  production REPL) during execution, file a separate Issue if lines are lost, and amend
  this Plan only if a target file must change.
- UNK-02: submitting the partial text as a turn after a timeout is the accepted contract
  (same degradation the EOF path already gives).

## Design decisions
- Replace `raise KeyboardInterrupt` with `break` so the timeout branch behaves exactly like
  the sibling EOF/interrupt branch: control exits the loop to the one existing
  `return "\n".join(parts)` shared by all three exits (Plan Design Decision: fall through
  to the existing return rather than adding a new `return` inside the clause).
- Keep the warning log line untouched so the observable timeout signal is unchanged.

## Alternatives considered
- A new `return "\n".join(parts)` statement inside the `except TimeoutError:` clause:
  rejected by the Plan's Design Decision (a second return point where one shared return
  exists).
- Catch `KeyboardInterrupt` around the `read_multiline` call in `ReplInputLoop._read_input`
  (Plan alternative): rejected — misleading raise-as-signal contract, `BaseException`
  crossing an `await`, and outside the Issue's scope.

## Implementation
### Target file
`scripts/agent/cli_view.py`

### Procedure
1. Write the red companion tests (see Companion test files) and confirm they fail against
   the unmodified `read_multiline`.
2. In `CLIView.read_multiline`, replace `raise KeyboardInterrupt` (cli_view.py:291) in the
   `except TimeoutError:` branch with `break`, keeping the `logger.warning` line (290)
   unchanged.
3. Rewrite the docstring sentence "On TimeoutError, raises KeyboardInterrupt to allow user
   interruption rather than silently swallowing the error." (cli_view.py:280-281) to state
   that on timeout the accumulated text is returned (REQ-001).

### Method
One statement substitution inside the `except TimeoutError:` clause plus its docstring
sentence; no structural change to the loop or the other clauses.

### Details
- `break` exits the `while True` loop (cli_view.py:284) to the existing
  `return "\n".join(parts)` (301); `cont` is never referenced after the except clause, so
  no unbound-variable path exists.
- Do not touch the sibling `except (EOFError, KeyboardInterrupt): break` (292-293),
  `_INPUT_TIMEOUT_S` (24), or the success path (294-300) (REQ-002; AC-3 limits the diff to
  the branch and its docstring statement).
- Neither `raise` nor `break` is a decision in McCabe terms: `radon cc` must stay at B(6)
  (the Plan's Design requires no rank increase).
- The cancelled `asyncio.wait_for` request leaves `StdinReader` accepting the next read
  (Plan Design verification); companion test 2 below pins this through `CLIView`.

### Companion test files
- `tests/test_cli_view.py` (companion of the `scripts/agent/cli_view.py` row; Plan
  `Implementation Target Files` seq 02 covered here per the companion rule)
  - Procedure: replace `TestReadMultilineTimeout.test_input_timeout_raises_keyboard_interrupt`
    (test_cli_view.py:141-166) with `test_input_timeout_returns_partial` (new): reuse the
    existing fixture pattern (`agent.cli_view._INPUT_TIMEOUT_S` monkeypatched to 0.2;
    `builtins.input` patched with `lambda p: (release.wait(5), "x")[1]` on a
    `threading.Event`; `release.set()` and `loop.close()` in a `finally`) and assert
    `read_multiline(loop, "hello\\")` returns `"hello"` without raising, the "Multiline
    input timed out" warning is logged, and the non-daemon thread set is unchanged
    (REQ-003 (a), (c); AC-1).
  - Procedure: add `test_timeout_then_second_read` (new) in the same fixture style: after
    the timeout return, start a second `read_multiline` on the same `CLIView`, release the
    blocked read with a line, and assert the second call completes with no `RuntimeError`
    (no "a stdin read is already pending") and no other error; assert on the absence of an
    error and on termination, not on a second `input()` call — the late line is delivered
    to the newest request per `StdinReader`'s contract (REQ-003 (b); AC-4; mirrors
    `TestCancelledRequestDelivery`).
  - Procedure: keep every `TestReadMultiline` case (joins, empty line, chained
    continuation, `test_stops_on_eof`, `test_stops_on_keyboard_interrupt`) unchanged as the
    AC-2 regression guard.
  - Flakiness mitigation (Plan Risks): reuse the existing Event-release pattern with the
    generous 5 s wait and release in `finally`.
  - Validation: `uv run pytest tests/test_cli_view.py -q` — new tests red before Procedure
    2, green after.

## Compatibility considerations
- `read_multiline` signature, return type, and the `Reader` protocol are unchanged (AC-3);
  the single runtime caller treats the returned string like any input line
  (`repl_input_loop.py:198-200`).
- No `docs/` update: the Plan's Documentation Impact is N/A — no `docs/*.md` describes the
  multiline timeout (CLIView and reference chapters mention `read_multiline` by name only);
  grep of the `docs/00_index.md` CLI rows (`agent_07_02`, `agent_07_05`) confirms no
  timeout-raise text (verified 20261103).

## Security considerations
N/A: no new input handling or trust-boundary change.

## Rollback considerations
- Single-file change plus tests; revert the commit restores prior behavior. No config or
  schema change to unwind.

## Validation plan
1. `uv run pytest tests/test_cli_view.py -q` (red before Procedure 2, green after).
2. `uv run pytest tests/agent/test_stdin_reader.py tests/agent/test_repl.py -q` — no
   regression in the reader and caller tests (AC-2).
3. Static: `uv run ruff check scripts/agent/cli_view.py tests/test_cli_view.py`,
   `uv run mypy scripts/agent/cli_view.py` — no findings.
4. Complexity / security / size: `radon cc scripts/agent/cli_view.py -s` (`read_multiline`
   stays at B(6)); `uv run bandit -r scripts/agent/cli_view.py -c pyproject.toml` (no new
   finding; the two existing assert_used findings are unrelated); `uv run python
   tools/check_module_size.py` (under 20480 B; currently 11020 B).
5. UNK-01: settle with a pty-driven scripted or manual session (not the production REPL):
   trigger a mid-continuation timeout, then type a follow-up line at the next `> ` prompt;
   if lines are lost, file a separate Issue per the Plan's UNK-01 resolution path.
6. Full validation sequence per `rules/toolchain.md`, including the diff-cover sequence
   (baseline recording without `--fail-under` first, then the threshold gate; Plan
   Implementation steps Phase 3).
7. Deploy is a hand-off to `skills/deploy/SKILL.md` after commit and push; deploying is the
   user's decision (Plan Implementation steps Phase 3).

## Completion criteria
- AC-1: with `_INPUT_TIMEOUT_S` shortened and a blocked read, `read_multiline` returns
  `"hello"` for first line `"hello\\"` without raising, and the warning is logged.
- AC-2: `test_stops_on_eof`, `test_stops_on_keyboard_interrupt`, and the success,
  empty-line and chained-continuation tests pass unchanged.
- AC-3: the diff is limited to the `except TimeoutError` branch and its docstring
  statement; the timeout constant, `Reader` protocol and signature are untouched.
- AC-4: a second `read_multiline` on the same `CLIView` after a timeout completes with no
  `RuntimeError`, and no non-daemon thread remains.

## Out of Scope
- `_INPUT_TIMEOUT_S` value, the `EOFError`/`KeyboardInterrupt` branch, the success path,
  and the `read_multiline` signature/return type (REQ-002).
- `scripts/agent/stdin_reader.py`, `scripts/agent/repl_input_loop.py`, `scripts/agent/repl.py`
  (read-only references; an amendment is required only if the follow-up test fails, per the
  Plan's Out-of-Scope note and UNK-01).
- `ReplInputLoop` shutdown-event wiring (Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write red companion tests, confirm they fail (Procedure 1; Companion test files) | Completed | 20261104-145610 | 20261104-145610 | stale-detector: Pass, all constructs found |
| 2 | Replace `raise KeyboardInterrupt` with `break` + docstring sentence (Procedure 2-3) | Completed | 20261104-145700 | 20261104-150100 | Red run aborted with KeyboardInterrupt from cli_view.py:291 pre-fix; equivalent tests committed in 2de5ab698, HEAD re-verified 59 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. UNK-01 pty check; deploy hand-off is the user's decision | Completed | 20261104-150100 | 20261104-165630 | Full suite 11469 passed / 7 skipped / 15 deselected under coverage; ruff/mypy/import-linter/bandit/pre-commit OK; changed-file count 2; radon cc B unchanged; ast-grep Not run (not installed); UNK-01 resolved via live pty check in 2de5ab698, follow-up filed as cliview002 |

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
- **Requirement ID**: REQ-001 (timeout returns accumulated text instead of raising),
  REQ-002 (sibling branches, timeout constant and method contract unchanged),
  REQ-003 (regression tests: graceful return, follow-up read, no non-daemon thread left)
- **Source issue**: issues/20261003-180327_cliview001_multiline-input-timeout-crashes-repl.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-142849_cliview001_multiline-input-timeout-crashes-repl.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-110436
- **Related target files**: `scripts/agent/cli_view.py`, `tests/test_cli_view.py`