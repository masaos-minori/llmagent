## Goal
- Make `CLIView.read_multiline` (`scripts/agent/cli_view.py`) return the already-accumulated continuation text when the 30-second multiline read times out, instead of raising a raw `KeyboardInterrupt` that no caller handles and that terminates the REPL process.

## Priority
High

## Scope
- **In-Scope**:
  - Change the `except TimeoutError` branch of `CLIView.read_multiline` to log the existing warning and fall through to `return "\n".join(parts)`, and update the method docstring that documents the raise.
  - Replace the existing test that asserts the `KeyboardInterrupt` with tests asserting a graceful return, and add a follow-up-read test on the same `CLIView` (`tests/test_cli_view.py`).
- **Out-of-Scope**:
  - The `_INPUT_TIMEOUT_S` value (30), the `EOFError`/`KeyboardInterrupt` branch, the success path and the `read_multiline` signature/return type.
  - `ReplInputLoop`'s shutdown-event wiring (tracked separately) and the multiline continuation syntax (trailing `\`).
  - `scripts/agent/stdin_reader.py` and `scripts/agent/repl_input_loop.py`: no change planned; they are read-only references unless the follow-up test in REQ-003 fails (then an amendment of this Plan is required, see UNK-01).
- **Dependencies**: N/A: none. The Issue lists none; no other Plan in `plans/` has `scripts/agent/cli_view.py` or `tests/test_cli_view.py` as an `Implementation Target Files` row (`plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` only cites `cli_view.py` as a no-change reference).

## Background
Found during an adversarial review of the REPL input loop. `CLIView` reads continuation lines through its own `StdinReader` (`scripts/agent/stdin_reader.py`), a daemon thread that performs one blocking `input()` per request, wrapped in `asyncio.wait_for(..., timeout=_INPUT_TIMEOUT_S)`. An earlier version of the Issue described a starved single-worker executor; that design no longer exists (checked in Step 2).

## Problem
`CLIView.read_multiline` handles `TimeoutError` by logging "Multiline input timed out" and executing `raise KeyboardInterrupt`. Because the raise happens inside the `except TimeoutError` clause, the sibling `except (EOFError, KeyboardInterrupt)` clause does not catch it. The only caller, `ReplInputLoop._read_input`, awaits `read_multiline` outside any `try` (its `_InputAborted` conversion wraps only the first-line read), and `ReplInputLoop._repl_loop` awaits `_read_input` outside the per-turn `try` whose handlers cover `TimeoutError`, `ConversationPersistenceError` and `Exception` only. `KeyboardInterrupt` is a `BaseException`, so it propagates through `ReplInputLoop.run`, `AgentREPL.run` (whose `finally` persists state) and out of `asyncio.run()` in `main()`, ending the process with a traceback (checked in Step 2 and Step 3).

## Reason for Change
A user who types a line ending in `\` and pauses for 30 seconds crashes the whole session; this is ordinary hesitation, not a fault condition.

## Implementation Intent
On timeout, keep the warning log and return the joined `parts` collected so far, the same degradation `EOFError` already gets in the sibling clause. The behavior of the abandoned `StdinReader.read` request on the next read is already specified and tested in `StdinReader`; the new test confirms it through `CLIView` and decides whether any further change is needed.

## Requirements
- `REQ-001`: On `TimeoutError` in `CLIView.read_multiline`, no exception propagates: the existing warning is logged and the text accumulated so far (`"\n".join(parts)`) is returned; the docstring no longer states that a `KeyboardInterrupt` is raised.
- `REQ-002`: The `_INPUT_TIMEOUT_S` value, the `EOFError`/`KeyboardInterrupt` branch (real Ctrl+C/Ctrl+D returns the partial text), the success path and the method's signature and return type stay unchanged.
- `REQ-003`: Regression tests assert that (a) a timed-out multiline read returns the partial text without raising and logs the warning, (b) a following `read_multiline` call on the same `CLIView` completes without `a stdin read is already pending` or any other error, and (c) no non-daemon thread is left behind. The existing test that expects `KeyboardInterrupt` is replaced.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/cli_view.py | Replace `raise KeyboardInterrupt` in the `except TimeoutError` branch of `CLIView.read_multiline` with returning the joined `parts`; update the docstring sentence about raising | The raise escapes the sibling `except (EOFError, KeyboardInterrupt)` clause and is uncaught by `ReplInputLoop._read_input` and `_repl_loop`, so it ends the process | REQ-001, REQ-002; AC-1, AC-2, AC-3 | `read_multiline` `except TimeoutError:` logs "Multiline input timed out" then `raise KeyboardInterrupt`; docstring says "raises KeyboardInterrupt"; `ReplInputLoop._read_input` calls `await self._view.read_multiline(loop, line)` with no enclosing `try` (checked in Step 2 and Step 3) | `tests/test_cli_view.py` (`TestReadMultiline`, `TestReadMultilineTimeout`) | Verified |
| tests/test_cli_view.py | Replace `TestReadMultilineTimeout.test_input_timeout_raises_keyboard_interrupt` with graceful-return and follow-up-read tests; keep `TestReadMultiline` cases as the EOF/Ctrl+C regression guard | The only timeout test asserts the crashing contract (`pytest.raises(KeyboardInterrupt)`); no test covers a read after a timeout | REQ-003, REQ-002; AC-1, AC-2, AC-4 | `TestReadMultilineTimeout.test_input_timeout_raises_keyboard_interrupt` monkeypatches `_INPUT_TIMEOUT_S` to 0.2, patches `builtins.input` with a blocking function and asserts `KeyboardInterrupt`, the log text and the non-daemon thread set; `TestReadMultiline.test_stops_on_eof` and `test_stops_on_keyboard_interrupt` cover the sibling branch (checked in Step 2 and Step 3) | `uv run pytest tests/test_cli_view.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/stdin_reader.py | `StdinReader.read` semantics for a cancelled request: one outstanding read, a late line goes to the newest request or is discarded, a second concurrent read is refused only while the earlier request's future is not done | REQ-003 (follow-up read), UNK-01 |
| scripts/agent/repl_input_loop.py | Only caller of `read_multiline` (`ReplInputLoop._read_input`); confirms the uncaught path and that the returned text is dispatched like any input line; owns a separate `StdinReader` (prompt `> `) | REQ-001, UNK-01, Risks |
| scripts/agent/repl.py | `AgentREPL.run` `finally` persistence and `main()` `asyncio.run(...)` show where the raw exception ends | REQ-001 |
| tests/agent/test_stdin_reader.py | Existing coverage of cancel-then-read and late-line delivery to design the follow-up test consistently | REQ-003 |
| tests/agent/test_repl.py | `_read_input` tests (shutdown race, no executor); run as regression for the caller | REQ-001 (Validation plan) |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-003): With `_INPUT_TIMEOUT_S` shortened and a blocked read, `read_multiline` returns the partial text (for first line `hello\` it returns `hello`) without raising, and the "Multiline input timed out" warning is logged.
- AC-2 (REQ-002, REQ-003): `test_stops_on_eof` and `test_stops_on_keyboard_interrupt` still pass unchanged; the success, empty-line and chained-continuation tests still pass.
- AC-3 (REQ-001, REQ-002): The diff is limited to the `except TimeoutError` branch and its docstring statement; the timeout constant, `Reader` protocol and signature are untouched.
- AC-4 (REQ-003): A second `read_multiline` call on the same `CLIView` after a timeout completes (returns text delivered through the same reader) with no `RuntimeError`, and no non-daemon thread remains.

## Tests
- Replace `test_input_timeout_raises_keyboard_interrupt` with a test that monkeypatches `agent.cli_view._INPUT_TIMEOUT_S` to a small value, patches `builtins.input` with a function that blocks on a `threading.Event`, and asserts the result equals the partial text, the warning is logged and the non-daemon thread set is unchanged (REQ-001, REQ-003).
- Add a follow-up test in the same fixture style: after the timeout, start a second `read_multiline` on the same `CLIView`, release the blocked read with a line, and assert the second call returns without error; the late line is delivered to the newest request per `StdinReader`'s contract, so assert on the absence of an error and on termination rather than on a second `input()` call (REQ-003).
- Keep the existing EOF and `KeyboardInterrupt` tests as the guard for the unchanged branch (REQ-002).

## Documentation Impact
N/A: no `docs/*.md` describes the multiline timeout (the CLIView and runtime-architecture chapters and `agent_12_reference-api.md` mention `read_multiline` only by name; `agent_13_reference-api-generated.md` lists classes only), so no doc is driven by REQ-001 to REQ-003. The docstring change is in the source and is covered by REQ-001 (checked in Step 2).

## Assumptions
- Returning the partial text on timeout is the intended contract, as the Issue states; the caller then treats it as an ordinary input line, exactly as it already does for the `EOFError` path (falsifiable: `_read_input` strips and returns the value, `_repl_loop` dispatches non-empty lines).
- The single-reader behavior after cancellation is as `StdinReader` documents and tests; the follow-up test (REQ-003) confirms it through `CLIView` (falsifiable: the test fails if a `RuntimeError` appears).
- `tools/check_plan_target_overlaps.py` reports no overlap for this Plan (judged in Step 8b).
- The Issue's Testing Expectations name `tests/agent/test_repl_input_loop.py`; that file does not exist. The caller's regression coverage is `tests/agent/test_repl.py`, run as a reference (checked in Step 3).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | `CLIView` and `ReplInputLoop` each own a separate `StdinReader` (prompts `... ` and `> `), so after a multiline timeout the stale `... ` thread stays blocked in `input()` while the next prompt starts a second reader thread; a line typed at the next prompt might be consumed by the stale thread and discarded (`target` is `None` once its request ended). Whether this occurs on a real terminal is unknown | No evidence from a real tty; unit tests with a fake read function cannot show which thread `input()` serves first | During implementation, check with a pty-driven manual or scripted session (not the production REPL); if lines are lost, file a separate Issue (for example sharing one reader) and amend this Plan only if it must change a target file | False |
| UNK-02 | Whether submitting the partial multiline text as a turn after a 30-second idle is the desired product behavior, as opposed to discarding it | The Issue explicitly asks to return the accumulated `parts`; no document states a preference | Accept the Issue's contract; revisit only if the owner objects (the change would be limited to the same branch) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/cli_view.py | Modify | Low: `read_multiline` has one runtime caller, `ReplInputLoop._read_input`; only the timeout path changes (raise becomes return) | 2 commits | 3 author-name spellings of one person (effectively 1) (Path A: no historical tooling) | not applicable (rsynced) |
| tests/test_cli_view.py | Modify | Low: test-only | 2 commits | 3 author-name spellings of one person (effectively 1) | not applicable (rsynced) |

## Design
Task classification: Path A. Two target files (at most 3), no change to the `Reader` protocol, signature or return type, no database or configuration change; the only behavior change is on the internal timeout path of a method with a single internal caller (checked in Step 3).

Decision: the timeout branch falls through to the existing `return "\n".join(parts)` after logging, rather than adding a new `return` inside the clause, so the three exits (empty line, EOF/interrupt, timeout) share one return. This mirrors the `EOFError` degradation and keeps the caller contract (a string) unchanged. Alternative considered: catch `KeyboardInterrupt` in `ReplInputLoop._read_input`; rejected because it leaves a misleading raise-as-signal contract and a `BaseException` crossing an `await`, and the Issue's scope names only `read_multiline`.

Verification of the abandoned read (Issue's open question): `asyncio.wait_for` cancels the wrapped `StdinReader.read` task; its `finally` clears the waiter, so the next `read` is not refused. The worker thread stays inside `input()` with `_reading` set; the next request does not wake a second read, and the eventual line is delivered to the newest request (`TestCancelledRequestDelivery`). The remaining cross-reader question is UNK-01.

Radon baseline: `CLIView.read_multiline` is rank B (6); the change removes no branch and must not raise the rank. `vulture scripts/ --min-confidence 80` reports only unrelated findings; `bandit` reports two `assert_used` findings in `cli_view.py` unrelated to `read_multiline` (checked in Step 5).

## Implementation steps
1. **Phase 1: Core change**
   - [ ] In `CLIView.read_multiline`, replace the `raise KeyboardInterrupt` in the `except TimeoutError` branch with fall-through to the joined return, keep the warning log, and rewrite the docstring sentence about raising (REQ-001, REQ-002; scripts/agent/cli_view.py).
2. **Phase 2: Tests**
   - [ ] Replace `test_input_timeout_raises_keyboard_interrupt` with the graceful-return test and add the follow-up-read test described in Tests; confirm the new tests fail against the unmodified method (REQ-003, REQ-002; tests/test_cli_view.py).
3. **Phase 3: Verification and deployment hand-off**
   - [ ] Run the Validation plan commands, including diff-cover without `--fail-under` to record the baseline and then at the `rules/toolchain.md` threshold; settle UNK-01 with a pty-based check outside the production REPL (REQ-001, REQ-002, REQ-003; scripts/agent/cli_view.py, tests/test_cli_view.py).
   - [ ] Deploy is a hand-off to `skills/deploy/SKILL.md`: the change must be committed and pushed first, and deploying is the user's decision (approval gate); `scripts/agent/cli_view.py` ships through the normal rsync with no new file, config key or service change (REQ-001; scripts/agent/cli_view.py).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/cli_view.py, tests/test_cli_view.py | Unit | `uv run pytest tests/test_cli_view.py` | All existing and new tests pass (AC-1 to AC-4) |
| scripts/agent/stdin_reader.py, scripts/agent/repl_input_loop.py | Unit (regression) | `uv run pytest tests/agent/test_stdin_reader.py tests/agent/test_repl.py` | No regression in the reader and caller tests (AC-2) |
| scripts/agent/cli_view.py, tests/test_cli_view.py | Static | `uv run ruff check scripts/agent/cli_view.py tests/test_cli_view.py` and `uv run mypy scripts/agent/cli_view.py` | No findings |
| scripts/agent/cli_view.py | Complexity / security | `radon cc scripts/agent/cli_view.py -s`; `uv run bandit -r scripts/agent/cli_view.py -c pyproject.toml` | `read_multiline` stays at or below rank B; no new bandit finding (the two existing `assert_used` findings are unrelated) |
| scripts/agent/cli_view.py | Size gate | `uv run python tools/check_module_size.py` | Module stays under the 20480 B gate (currently about 11 KB) |
| scripts/agent/cli_view.py | Coverage | `rules/toolchain.md` section 7 diff-cover sequence | Changed lines meet the Completion checklist threshold |

## Risks
- **Risk**: After a timeout the partial multiline text is returned and `_repl_loop` dispatches it as a normal turn, so an unfinished message (or an unintended slash command) can reach the orchestrator after the user idled → **Mitigation**: this matches the existing `EOFError` behavior and the Issue's explicit contract (UNK-02); the warning is logged; the owner can narrow the behavior later by changing the same branch only.
- **Risk**: A stale `... ` reader thread may swallow the next line typed at the `> ` prompt (UNK-01) → **Mitigation**: non-blocking and pre-existing in design (not introduced by this change; the raise only hid it by ending the process); verify with a pty check in Phase 3 and file a separate Issue if lines are lost.
- **Risk**: The new test depends on real threads and short timeouts and could be flaky → **Mitigation**: reuse the pattern of the existing timeout test (a `threading.Event` release, `_INPUT_TIMEOUT_S` monkeypatched to 0.2 s, generous release wait) and release the event in a `finally`.
- **Risk**: `Reader` protocol documentation or other callers assume the raise → **Mitigation**: `read_multiline` has a single caller and no document describes the raise (checked in Step 2); `tests/agent/test_repl.py` mocks it with `AsyncMock`, so no other test depends on the old contract.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Return the partial text on timeout in `CLIView.read_multiline` (scripts/agent/cli_view.py) | In Progress | — | — |  |
| 2 | Replace the timeout test and add the follow-up-read test (tests/test_cli_view.py) | In Progress | — | — |  |
| 3 | Validation commands, UNK-01 pty check and deploy hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261103-110436_01_scripts_agent_cli_view.py.md | 1, 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261003-180327_cliview001_multiline-input-timeout-crashes-repl.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-142849
- **Related target files**: scripts/agent/cli_view.py, tests/test_cli_view.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Problem, Required Changes (return instead of raise); `read_multiline` `except TimeoutError`; `ReplInputLoop._read_input` caller without `try` | scripts/agent/cli_view.py | Step 1 | AC-1, AC-3 | `uv run pytest tests/test_cli_view.py` (new graceful-return test) | Confirmed by repository evidence |
| REQ-002 | Issue Constraints, Acceptance Criteria (Ctrl+C/Ctrl+D unaffected, timeout value unchanged) | scripts/agent/cli_view.py | Step 1 | AC-2, AC-3 | Existing `TestReadMultiline` cases | Explicit in issue |
| REQ-002 | Issue Constraints; existing EOF/KeyboardInterrupt tests | tests/test_cli_view.py | Step 2 | AC-2 | `uv run pytest tests/test_cli_view.py` | Explicit in issue |
| REQ-003 | Issue Required Changes (regression test, verify next read), Testing Expectations, Unresolved Questions; `StdinReader` cancel semantics and `TestCancelledRequestDelivery` | tests/test_cli_view.py | Step 2 | AC-1, AC-4 | `uv run pytest tests/test_cli_view.py tests/agent/test_stdin_reader.py` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261103-110436 -->