## Goal

Delete `tests/agent/test_signal_handler_race.py` (8 tests, 3 permanently skipped) rather than rewrite it, making `tests/agent/test_signal_handler.py` the sole home of signal coverage (REQ-007).

## Scope

Only `tests/agent/test_signal_handler_race.py` is removed. No other file changes in this row; the replacement coverage lives in row 2 (`tests/agent/test_signal_handler.py`). No production file under `scripts/` changes.

## Assumptions

- The file has no `scripts/` mirror and no workspace/tooling reference (`grep -rn "test_signal_handler_race" docs/ tools/ skills/ prompts/` → empty), so deleting it leaves no dangling import or expectation.
- Its assertions depend on no production code (`MagicMock(spec=AgentREPL)` self-assertions), so removal does not break any other test.
- Line numbers below are current-HEAD values from the file itself.

## Design decisions

- **Deletion, not migration.** After removing the mock-self-asserting bodies, nothing left in the file calls production code, so rewriting it would duplicate `test_repl.py:1191-1232` (the `services may be None` guards) and `test_signal_handler.py:36-49` (the `NotImplementedError` fallback). The surviving contract (Windows success path) is restated in the mirror file's module docstring (row 2), not kept as a skipped test.
- **A scope decision, not a coverage loss.** The file's 8 tests are 5 net-new assertions over mock state plus 3 permanent skips; neither shape is regression protection on this matrix.

## Alternatives considered

- Merging the file into `test_signal_handler.py` — rejected: its classes assert on `MagicMock(spec=AgentREPL)` state the body assigned and call `_on_first_turn` (absent from `AgentREPL`), so they add nothing the mirror file's real-transport cases already cover; REQ-007 mandates deletion.
- Keeping the file and un-skipping the OS-signal class — rejected: those tests patch `signal.signal` and never touch `loop.add_signal_handler` (`signal_handler.py:51-63`), and CI runs only `ubuntu-latest` (`.github/workflows/ci.yml:11,:46`), so they can never run meaningfully.

## Implementation

### Target file

`tests/agent/test_signal_handler_race.py` (deleted)

### Procedure

1. Delete the file with a single-target `git rm tests/agent/test_signal_handler_race.py` (per `AGENTS.md` Execution policy: deleting one file needs no extra confirmation).
2. Confirm no workspace/tooling reference remains: `grep -rn "test_signal_handler_race" docs/ tools/ skills/ prompts/` returns no match. A full-repo `grep -rn "test_signal_handler_race" .` still matches the source issue `issues/done/20261021-093421_repl003_repl-shutdown-behavior-untested-in-real-wiring.md` (which names the file as the defect being fixed) and the row-2 impl procedure (which names it as the deletion target); those are expected references, not stray ones.
3. Confirm the suite is green without it: `uv run pytest tests/agent -q`.

### Method

```bash
git rm tests/agent/test_signal_handler_race.py
grep -rn "test_signal_handler_race" docs/ tools/ skills/ prompts/   # expect no match
uv run pytest tests/agent -q                                       # expect green
```

### Details

The file holds 8 collected tests, 3 permanently skipped: the two methods of the `@pytest.mark.skipif(True)` class `TestCrossPlatformSignalHandlerConsistency` (`:48`) and the single `@pytest.mark.skipif(True)` method `test_ctypes_console_ctrl_handler_registered_when_pywin32_unavailable` (`:106`). The other 5 (`TestTurnActiveFlagCheck` ×3, `TestShutdownCompleteness` ×2) assert on `MagicMock(spec=AgentREPL)` state the body assigned (`:17`, `:25`, `:34`, `:39-45`) and call `_on_first_turn`, an attribute absent from `AgentREPL`. None depend on production code, so removal is coverage-neutral on this matrix.

## Compatibility considerations

N/A: test-only deletion; the deleted file's real equivalent already lives against production code (`test_repl.py:1191-1232`, `test_signal_handler.py:36-49`).

## Security considerations

N/A: no process, signal, or I/O boundary touched by removal.

## Rollback considerations

N/A: revert the commit; the deletion is a single-target `git rm`, reversible with `git checkout HEAD -- tests/agent/test_signal_handler_race.py`.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| file removed | proof by execution | `uv run pytest tests/agent -q` | Green |
| no stray reference | grep | `grep -rn "test_signal_handler_race" docs/ tools/ skills/ prompts/` | Empty |

Static gates: none (no file remains to lint).

## Completion criteria

- `tests/agent/test_signal_handler_race.py` does not exist (AC-7).
- `grep -rn "test_signal_handler_race" docs/ tools/ skills/ prompts/` empty (AC-7, REQ-009).
- `uv run pytest tests/agent -q` green with the file gone (REQ-007).

## Out of Scope

`tests/agent/test_signal_handler.py` (row 2); the Windows-success contract restated in that file's module docstring (REQ-007); any `scripts/` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `tests/agent/test_signal_handler_race.py`; confirm no stray reference and green suite | In Progress | — | — | Order-independent; safe at HEAD |
| 2 | Add/update tests per Validation plan | N/A | — | — | deletion, no new test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | test-only deletion |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-01 | Step 1 / REQ-003 | Record-keeping | Open | implementer | record collected-test delta (-8) against baseline |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-007, REQ-009
- **Source issue**: `issues/done/20261021-093421_repl003_repl-shutdown-behavior-untested-in-real-wiring.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-043008_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-081341
- **Related target files**: `tests/agent/test_signal_handler_race.py`
