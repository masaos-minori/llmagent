# Add a regression test for tools/check_no_compat.py's default-scan ROOT_DIR path

## Goal
`tests/tools/test_check_no_compat.py` has a test that would fail if `ROOT_DIR` is ever
miscomputed again (e.g. by a future file move), covering the code path that the existing
test suite currently does not exercise at all.

## Scope
- In scope: one new test function in `tests/tools/test_check_no_compat.py` asserting
  `ROOT_DIR` resolves to a directory that actually contains `scripts/`, `docs/`, `tests/`,
  and `tools/`.
- Out of scope: testing `main()`'s full CLI argument handling or its `IsADirectoryError`
  crash on directory positional arguments (tracked separately in
  `issues/20260807-101021_risks.md`); changes to the existing `TestPatternDetection` /
  `TestWorkflowEnforcementPatterns` classes.

## Assumptions
- The corrected `ROOT_DIR = Path(__file__).resolve().parent.parent` (from the companion
  `check_no_compat.py` fix) is already applied before this test is added, so the test
  documents the fixed behavior rather than the bug.
- `ROOT_DIR` remains importable as a module-level attribute of `tools.check_no_compat`
  (it already is — no encapsulation change is planned in the companion fix).

## Design decisions
- Assert on `ROOT_DIR`'s resolved value directly (importing the module and checking
  `(ROOT_DIR / "scripts").exists()` etc.) rather than invoking `main()` end-to-end via
  subprocess — this isolates the regression to the specific computation that broke,
  matching the existing test file's style of calling into the module directly rather than
  shelling out.
- Check all four expected subdirectories (`scripts`, `docs`, `tests`, `tools`) rather than
  just one, since `main()`'s `dirs_to_scan` depends on all four existing.

## Alternatives considered
- Running `python -m tools.check_no_compat` as a subprocess and asserting on stdout/exit
  code: rejected as heavier and slower than a direct attribute assertion, and less
  precise — a subprocess-level test could pass or fail for unrelated reasons (e.g. a
  genuine compat-pattern finding elsewhere in the repo) rather than isolating the
  `ROOT_DIR` computation itself.

## Implementation

### Target file
`tests/tools/test_check_no_compat.py`

### Procedure
1. Add `from tools.check_no_compat import ROOT_DIR` (or `import tools.check_no_compat as
   check_no_compat` matching the existing import style already used in this file) if not
   already imported.
2. Add a new test function (e.g. `test_root_dir_resolves_to_repository_root`) asserting:
   - `(ROOT_DIR / "scripts").exists()` is `True`
   - `(ROOT_DIR / "docs").exists()` is `True`
   - `(ROOT_DIR / "tests").exists()` is `True`
   - `(ROOT_DIR / "tools").exists()` is `True`
3. Fix this file's own docstring (line 1), which currently reads the stale
   `tests/test_check_no_compat.py` instead of its real path `tests/tools/test_check_no_compat.py`,
   while this file is open for edit.

### Method
One new pytest test function using plain `assert` statements (matching the existing file's
style — no new fixtures or parametrization needed for four static existence checks).

### Details
- Placement: add alongside `TestPatternDetection` (either as a new standalone function or
  a new small test class, whichever matches the existing file's dominant style — confirm by
  reading the file's current class/function mix before inserting).
- No `tmp_path` or synthetic-content fixture needed, since this test checks the real
  repository's on-disk layout via the real `ROOT_DIR`, not synthetic input.

## Compatibility considerations
N/A — test-only addition, no production code or public interface change.

## Security considerations
N/A — no security-sensitive logic touched.

## Rollback considerations
Single new test function; revert via `git revert` with no cleanup needed.

## Validation plan
| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/tools/test_check_no_compat.py` | Unit | `uv run pytest tests/tools/test_check_no_compat.py -v` | New test passes; all existing tests still pass |
| Regression check | Manual | Temporarily revert the companion `ROOT_DIR` fix and re-run the new test | New test fails, confirming it actually catches the regression it targets |
| Changed file | Lint/type | `uv run ruff check tests/tools/`, `uv run mypy tests/tools/` | No new errors |
| Coverage | Diff-scoped | `uv run coverage run -m pytest tests/tools/test_check_no_compat.py && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master` | New test lines covered |

## Out of scope
- `main()` CLI argument handling and its directory-argument crash.
- Any change to `TestPatternDetection` / `TestWorkflowEnforcementPatterns`.
- The `ROOT_DIR` / `DEFAULT_ALLOWLIST` source fix itself — covered by the companion
  implementation procedure for `tools/check_no_compat.py`.

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-100914_plan.md
- Source implementation procedure: N/A
- Generated at: 20260807-102151
- Related target files: tests/tools/test_check_no_compat.py
