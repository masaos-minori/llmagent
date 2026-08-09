## Goal
Add test coverage in `tests/tools/test_check_no_compat.py` proving that a directory passed as a
positional argument to `tools.check_no_compat`'s `main()` is expanded into its contained files
and scanned, instead of raising `IsADirectoryError`.

## Scope
In scope: one or more new tests in `tests/tools/test_check_no_compat.py` covering the
directory-argument code path added in the companion procedure
(`implementations/20260809-170919_check_no_compat_directory_arg_expansion.py.md`). Out of scope:
any change to `tools/check_no_compat.py` itself (covered by that companion document) or to
unrelated existing tests in this file.

## Assumptions
- No existing test in this file invokes `main()` directly — confirmed by reading the file's
  imports (`from tools.check_no_compat import (COMPAT_PATTERNS, ROOT_DIR,
  check_compat_patterns)`) and its `unittest`/`pytest`-style test classes, none of which
  exercise `main()` or `sys.argv`. This test will be the first to do so.
- The file already uses a `tmp_path`-based pattern (create a file via `tmp_path / "name.py"`,
  `.write_text(...)`, then call the checking function directly) — the new test should follow
  this same fixture style for creating its test directory.

## Design decisions
- Exercise the fix via `monkeypatch.setattr(sys, "argv", [...])` + calling `main()` directly,
  rather than `subprocess.run([...])` — keeps the test fast and in-process, consistent with how
  the rest of the suite avoids subprocess calls, and lets the test assert on `main()`'s return
  code directly.
- Build the test directory with `tmp_path`, containing one file with a known compat-pattern
  violation (reuse an existing pattern already asserted elsewhere in this file, e.g. from
  `TestWorkflowEnforcementPatterns`, to avoid inventing a new pattern) and one clean file, so the
  test proves both that the directory was actually expanded (violation detected) and that clean
  files don't produce false positives.

## Alternatives considered
- **Testing only that no exception is raised, without asserting the violation is found**:
  rejected as insufficient — it would pass even if the directory were silently skipped rather
  than genuinely expanded, so it would not actually prove the fix's intended behavior.
- **Refactoring `main()`'s file-collection logic into a separately unit-tested helper**: left as
  an option in the companion source-fix procedure (Step 5); this test procedure targets `main()`
  end-to-end via `argv` patching either way, so it works whether or not that extraction happens.

## Implementation
### Target file
`tests/tools/test_check_no_compat.py`

### Procedure
1. Add a new test (function or method, matching the file's existing style) that:
   - Creates a directory under `tmp_path` containing one `.py` file with a known
     compat-pattern violation (reuse an existing violation string already used elsewhere in
     this test file) and one clean `.py` file with no violations.
   - Uses `monkeypatch.setattr(sys, "argv", ["check_no_compat", str(tmp_dir)])` (adjust program
     name arg to match `argv[0]` convention used elsewhere if any) then calls `main()`.
   - Asserts `main()`'s return value reflects the violation being found (matching whatever
     exit-code/return-value convention `main()` already uses for "issues found" — confirm this
     convention by reading `main()`'s return statements, do not assume `0`/`1` without checking).
2. Add a second case (can be the same test, parametrized, or a separate test) passing a
   directory containing only clean files, asserting a "no issues" result and — critically — that
   no exception is raised.
3. Do not modify any existing test in the file.

### Method
Two new `pytest` test functions (or one parametrized test), following the file's existing
`unittest`/`pytest` conventions and `tmp_path` fixture usage.

### Details
- Import `sys` if not already imported in the test file.
- Reuse an existing known-violation string/pattern from `COMPAT_PATTERNS` or an existing test's
  fixture content rather than inventing a new one, so the test stays aligned with what the tool
  actually flags.

## Compatibility considerations
Additive only — no existing test is modified or removed.

## Security considerations
N/A — test-only change, no production code path affected.

## Rollback considerations
Additive test file change; revert via `git revert` of the commit with no other side effects.

## Validation plan
- `uv run pytest tests/tools/test_check_no_compat.py -v` — all existing 22 tests plus the new
  test(s) pass (23+ total).
- `uv run mypy tests/tools/test_check_no_compat.py` and `uv run ruff check
  tests/tools/test_check_no_compat.py` — no new errors.
- Confirm the new test fails against the pre-fix code (sanity-check that it actually exercises
  the bug) and passes after the companion source fix is applied.

## Out of scope
- Any change to `tools/check_no_compat.py` (see
  `implementations/20260809-170919_check_no_compat_directory_arg_expansion.py.md`).
- Existing tests in `tests/tools/test_check_no_compat.py`.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260809-170033_plan.md
- Source implementation procedure: N/A
- Generated at: 20260809-170953
- Related target files: tests/tools/test_check_no_compat.py
