# Implementation: H-6 — Delete test_undo_artifact_consistency.py entirely

## Goal

Delete `tests/test_undo_artifact_consistency.py` in full. The behavior it tests (tool_results
rows being marked `undone` by `undo_last_turn()`) no longer exists after H-6/H-7 remove that
capability entirely — there is nothing left in this behavior domain to lock down with a test.

## Scope

**Target**: `tests/test_undo_artifact_consistency.py` (deletion)

**Supersedes**: `implementations/20260708-164530_test_undo_artifact_consistency.py.md` (the H-7
doc for this file, which REWROTE the tests to assert `n_artifacts_marked == 0` and
`undone is False` instead of deleting the file). **H-6's plan explicitly chooses full deletion
over rewriting** (plan Unknowns §3: "テストファイル全体を削除する (behavior自体がなくなるため)"),
which is a stricter/simpler end state than H-7's rewrite. **Implement this doc's deletion
instead of H-7's rewrite** if both are pending. If H-7's rewrite doc was already applied, delete
the rewritten file exactly as it would delete the original — the file's content at that point is
irrelevant since the whole file is being removed either way.

**Depends on**: land together with `implementations/20260708-165242_undo_service_h6.py.md` and
`implementations/20260708-165317_models_h6.py.md` (the source changes this test file exercises).

**Out of scope**: `tests/test_regression_undo_artifact.py` — a DIFFERENT test file that covers
`undo_last_turn()`'s DB-side behavior (history trim, session rollback) without depending on
`tool_result_store`/`n_artifacts_marked` at all (confirmed by grep: zero matches for
`n_artifacts_marked` in that file) — it needs NO changes and continues to provide coverage for
`undo_last_turn()`'s core logic after this deletion.

## Assumptions

1. Every test in `test_undo_artifact_consistency.py` asserts either
   `result.n_artifacts_marked == <N>` or a `row.undone` value that only changes because of the
   now-removed `mark_turn_undone(...)` call — once that call is gone, every test in this file
   either fails outright (asserting `== 1` when it will now always be `0`) or becomes vacuously
   about a value that can never be anything other than the trivial case, providing no real
   signal.
2. `test_regression_undo_artifact.py` provides sufficient continued coverage of
   `undo_last_turn()`'s remaining behavior (history truncation, `stat_turns` decrement,
   `session.undo_last_turn()` invocation) — confirmed by the plan's Validation Plan, which relies
   on this file passing as the regression backstop.

## Implementation

### Target file

`tests/test_undo_artifact_consistency.py` (to be deleted)

### Procedure

#### Step 1: Confirm no other file imports from this test module

```bash
grep -rn "test_undo_artifact_consistency" tests/ scripts/ --include="*.py"
```

Expected: no matches outside the file's own header comment (test files are not typically
imported by other test files in this codebase's convention).

#### Step 2: Delete the file

```bash
rm tests/test_undo_artifact_consistency.py
```

#### Step 3: Confirm `test_regression_undo_artifact.py` still covers the core behavior

```bash
grep -n "def test_" tests/test_regression_undo_artifact.py
```

Read the output and confirm history-trim / stat_turns-decrement / session-rollback assertions
exist somewhere in that file. If any of those specific behaviors turn out to be covered ONLY by
the file being deleted (unlikely, given the plan's explicit reliance on
`test_regression_undo_artifact.py` as the backstop, but worth a final check), port the missing
assertion into `test_regression_undo_artifact.py` before deleting — the plan's Risk table lists
this as a "Low" severity, already-mitigated concern, not an open unknown.

### Method

- File deletion, not modification — `git rm tests/test_undo_artifact_consistency.py` (or
  equivalent) at implementation time.

### Details

- `_FakeSQLiteHelper`, `_SCHEMA_SQL`, and `_make_store()` (helpers defined only in this file) are
  removed along with it — nothing else in the test suite imports them (test helper functions in
  this codebase are file-local by convention, not shared across test modules).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Grep (file gone) | `ls tests/test_undo_artifact_consistency.py 2>&1` | "No such file or directory" |
| Grep (no dangling references) | `grep -rn "test_undo_artifact_consistency" tests/ scripts/` | no matches |
| Tests (regression backstop) | `uv run pytest tests/test_regression_undo_artifact.py -v` | all pass |
| Tests (full) | `uv run pytest -v` | test count decreases by exactly the number of tests that were in the deleted file; no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |

## Risks

- Deleting a test file always reduces raw coverage numbers; the plan's own Risk table classifies
  this as "Low" severity given `test_regression_undo_artifact.py`'s continued coverage of
  `undo_last_turn()`'s core (non-tool-result) behavior. No further mitigation beyond Step 3's
  confirmation check is planned.
