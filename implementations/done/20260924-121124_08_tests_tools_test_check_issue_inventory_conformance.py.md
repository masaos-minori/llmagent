## Goal
Add a real-repo-path regression test class to
`tests/tools/test_check_issue_inventory_conformance.py` asserting
`GOVERNANCE_DOC_PATH.is_file()` against the actual repository tree, mirroring
`tests/tools/test_check_dependency_graph_cycles.py::TestRealGraphIntegration`,
implementing `REQ-004`.

## Scope
In scope: adding one new test class with one test method, and extending this file's
existing `from tools.check_issue_inventory_conformance import (...)` block to also
import `GOVERNANCE_DOC_PATH`. Out of scope: any change to the existing hermetic
`tmp_path`-fixture test classes already in this file.

## Assumptions
- All existing tests in this file use hermetic `tmp_path` fixtures (`doc = tmp_path /
  GOVERNANCE_DOC_NAME`) — confirmed via `grep -n "tmp_path / GOVERNANCE_DOC_NAME"`
  (8+ occurrences) — so there is currently zero coverage of `main()`'s default path
  resolution logic (the subject of seq 07's fix).
- `tests/tools/test_check_dependency_graph_cycles.py::TestRealGraphIntegration`'s
  pattern (a class-level docstring explaining the dependency on a prior implementation
  step, a single test method, `assert doc_path.is_file(), f"{doc_path} not found"`) is
  the established, reusable pattern for this kind of real-repo-path regression test in
  this test suite — this row reuses it rather than inventing a new pattern.
- This test depends on seq 01 and seq 03 (the `git mv` of the 2 files this tool and its
  sibling tools read) and seq 07 (`GOVERNANCE_DOC_PATH`'s definition) having landed
  first — it will fail with a clear assertion message, not silently pass, if run before
  those land, consistent with `TestRealGraphIntegration`'s own documented behavior.

## Design decisions
Name the new class `TestGovernanceDocPathIntegration` and its test method
`test_governance_doc_path_resolves_on_disk`, parallel to
`TestRealGraphIntegration`/`test_real_repo_graph_has_no_cycle`'s naming. Keep the
assertion to existence only (`GOVERNANCE_DOC_PATH.is_file()`) — this row's purpose is to
catch the specific class of bug seq 07 fixes (a defaulted path pointing at a
nonexistent location), not to duplicate this file's existing content-parsing coverage.

## Alternatives considered
- Invoke `main()` directly (e.g. via `subprocess` or by monkeypatching `sys.argv`) and
  assert it exits 0: rejected as the sole test — a full `main()` invocation also
  exercises this tool's vocabulary/field-count/referential-integrity checks against the
  real, current governance document content, which could fail for reasons unrelated to
  path resolution (a genuine, pre-existing inventory finding) and would make this
  regression test flaky for a purpose it isn't meant to guard. The `GOVERNANCE_DOC_PATH.is_file()`
  assertion isolates exactly the path-resolution concern REQ-003/REQ-004 exist to fix,
  matching `TestRealGraphIntegration`'s own scope (existence + section-parseable, not a
  full `main()` exit-code check).

## Implementation
### Target file
`tests/tools/test_check_issue_inventory_conformance.py`

### Procedure
1. Extend the existing import block:
   ```python
   from tools.check_issue_inventory_conformance import (
       GOVERNANCE_DOC_NAME,
       GOVERNANCE_DOC_PATH,
       check_closing_summary,
       check_orphaned_bullets,
       check_referential_integrity,
       check_template_field_count,
       check_vocabulary,
   )
   ```
2. Add, at the end of the file (after the last existing test class):
   ```python
   class TestGovernanceDocPathIntegration:
       """Exercises GOVERNANCE_DOC_PATH against the actual repository tree. Depends on
       docsreorg05's plans/20260924-115855_plan.md seq 01/03 (the governance docs move)
       and seq 07 (this tool's GOVERNANCE_DOC_PATH constant) having already been
       applied; if run before those land, this test fails with a clear assertion
       message rather than silently skipping.
       """

       def test_governance_doc_path_resolves_on_disk(self) -> None:
           assert GOVERNANCE_DOC_PATH.is_file(), f"{GOVERNANCE_DOC_PATH} not found"
   ```

### Method
One new import name added to an existing `from ... import (...)` block; one new class
appended to the file. No change to any existing test class, fixture, or assertion.

### Details
- Place the new class after the last existing class in this file so file structure
  stays append-only for this row — do not reorder existing classes.
- `GOVERNANCE_DOC_NAME` remains imported and used by existing fixtures (e.g. `doc =
  tmp_path / GOVERNANCE_DOC_NAME`) — this row adds `GOVERNANCE_DOC_PATH` alongside it,
  not in place of it.
- No new `pytest` fixture, `monkeypatch`, or `tmp_path` parameter is needed for this
  test — it reads the real repository tree directly, exactly like
  `TestRealGraphIntegration`.

## Compatibility considerations
N/A: a new, additive test class has no compatibility surface with existing tests or
production code.

## Security considerations
N/A: a filesystem-existence assertion against a repository-relative path introduces no
new security-relevant surface.

## Rollback considerations
Revert via `git checkout -- tests/tools/test_check_issue_inventory_conformance.py`, or
`git revert` the commit containing this change if already committed. Rolling back this
row alone (leaving seq 07 landed) simply removes this regression test's coverage with
no other effect — unlike seq 07's own rollback considerations, this row's rollback is
independently safe.

## Validation plan
- `uv run pytest tests/tools/test_check_issue_inventory_conformance.py -q` passes,
  including the new `TestGovernanceDocPathIntegration::test_governance_doc_path_resolves_on_disk`
  (Plan `AC-6`).
- `uv run pytest tests/tools/ -q` (full suite) shows no regression in any other test in
  this file (Plan `AC-2`, `AC-6`).
- `uv run ruff format tests/tools/test_check_issue_inventory_conformance.py`, `uv run
  ruff check tests/tools/test_check_issue_inventory_conformance.py --fix`, then `uv run
  ruff check tests/tools/test_check_issue_inventory_conformance.py` (confirm clean).
- `uv run mypy tests/tools/test_check_issue_inventory_conformance.py` (per
  `rules/coding.md` mypy note: `tests/` is covered by pre-commit's mypy run).

## Completion criteria
`tests/tools/test_check_issue_inventory_conformance.py` imports `GOVERNANCE_DOC_PATH`;
a new `TestGovernanceDocPathIntegration` class with one test method asserting
`GOVERNANCE_DOC_PATH.is_file()` exists; that test passes once seq 01/03/07 have landed;
no existing test in this file is modified or fails as a result of this change.

## Out of scope
Any change to the file's existing hermetic fixture-based test classes
(`TestVocabularyViolation`, `TestTemplateFieldCountViolation`, `TestOrphanedBullets`,
`TestClosingSummaryConsistency`, `TestReferentialIntegrity`, and any other existing
class); any test invoking `main()` end-to-end (see Alternatives considered).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `GOVERNANCE_DOC_PATH` to the import block and append `TestGovernanceDocPathIntegration` | Completed | 20260924-122840 | 20260924-122840 | Added GOVERNANCE_DOC_PATH import and TestGovernanceDocPathIntegration class with test_governance_doc_path_resolves_on_disk. ruff format/check and mypy pass clean. |
| 2 | N/A: this row's Step 1 is itself the new test being added | Completed | 20260924-122840 | 20260924-122840 | N/A: this row's Step 1 is itself the new test being added. |
| 3 | Run `uv run pytest tests/tools/test_check_issue_inventory_conformance.py -q`, `uv run pytest tests/tools/ -q`, `ruff`/`mypy` against this file | Completed | 20260924-122840 | 20260924-122840 | uv run pytest tests/tools/test_check_issue_inventory_conformance.py -q: 21 passed (20 existing + 1 new), no regression. New test confirms GOVERNANCE_DOC_PATH.is_file() resolves against the moved repository tree (AC-6 met). |
| 4 | N/A: no documentation update — this is a test-only addition | Completed | 20260924-122840 | 20260924-122840 | N/A: no documentation update -- test-only addition. |

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
- **Requirement ID**: `REQ-004` (real-repo-path regression test for `GOVERNANCE_DOC_PATH`)
- **Source issue**: issues/20260923-140944_docsreorg05_move-governance-docs-into-new-governance-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-115855_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-121124
- **Related target files**: tests/tools/test_check_issue_inventory_conformance.py