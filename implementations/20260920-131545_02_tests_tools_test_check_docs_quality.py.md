## Goal
Add unit tests for the cross-file comparison path (REQ-002) to
`tests/tools/test_check_docs_quality.py`: one positive case, one negative
case, and an extension of `TestRegressionFullDocsTree` confirming the
within-file finding count stays at 206 while the known governance_01/
governance_04 duplication is now detected.

## Scope
In scope: a small, backward-compatible extension to the `_make_doc_file`
fixture helper (add an optional `tmp_name` parameter, default unchanged);
2 new test methods in a new `TestContentSimilarityCrossFile` class; 1 new
test method appended to the existing `TestRegressionFullDocsTree` class.
Out of scope: any change to the 17 existing tests' behavior or the
`_make_doc_file` helper's default (no-argument) behavior.

## Assumptions
The sibling implementation procedure
(`implementations/20260920-131545_01_tools_check_docs_quality.py.md`) has
already added the cross-file comparison pass to
`tools/check_docs_quality.py`'s `check_content_similarity` before this row
is implemented, per table order (this is `seq` 02, after `seq` 01).

## Design decisions
- `_make_doc_file` currently writes any path-less fixture unconditionally
  to the single hardcoded `.tmp_test_doc.md` (confirmed via Read,
  2026-09-20: `check_content_similarity` calls `doc.path.read_text(...)`,
  not `doc.lines`, so a real on-disk file is required for each fixture,
  not just an in-memory object). Testing 2 *different* documents at once
  therefore needs 2 *different* temp files, or the second fixture's write
  would silently overwrite the first before it is read. Add an optional
  `tmp_name: str = ".tmp_test_doc.md"` parameter (default preserves all 8
  existing call sites' behavior exactly) so a cross-file test can request 2
  distinct temp filenames.
- Each new cross-file test explicitly deletes its own temp file(s) in a
  `try`/`finally` block, so no new untracked file is left in the working
  tree after the test run (unlike the pre-existing `.tmp_test_doc.md`,
  which this Plan does not touch or attempt to fix — Out of Scope, a
  pre-existing test-hygiene characteristic of this file, not introduced by
  this row).
- The `TestRegressionFullDocsTree` extension distinguishes within-file vs.
  cross-file findings by substring: the existing within-file message format
  is `"Content similarity detected between sections '..."` (containing the
  word "sections"); the new cross-file message format (per the sibling
  procedure's Method) is `"Content similarity detected between
  {file}#'...' and {file}#'...'"` (no "sections" substring) — counting
  `"between sections '"` occurrences therefore counts only within-file
  findings, unaffected by the new cross-file ones.

## Alternatives considered
- Using `pytest`'s `tmp_path` fixture instead of writing into the repo
  root — rejected: `_make_doc_file`'s existing `path is not None` branch
  requires `path.relative_to(_ROOT_DIR / "docs")` to succeed, which a
  `tmp_path`-based path cannot satisfy; reworking that branch's contract
  is a larger change than this row's narrow scope justifies.
- Using 2 real existing `docs/*.md` files (via explicit `path=`) for the
  positive/negative cross-file tests instead of writing new temp files —
  viable for the positive case (see below) but fragile for the negative
  case, since two arbitrary real files might coincidentally share
  boilerplate (e.g. both have a "Related Documents" section) and produce an
  unwanted finding; the temp-file approach gives full control over content.
- For the positive case specifically, the real `docs/00_governance_01_documentation-policy.md`/
  `docs/00_governance_04_documentation-checks.md` pair (a "known real-world
  defect", mirroring `TestAlphabeticSuffixDuplicateHeading::test_true_positive_known_defect_case`'s
  pattern) is used in the `TestRegressionFullDocsTree` extension instead of
  a synthetic fixture, since it is the actual motivating case — no separate
  synthetic real-file-based unit test is added for it beyond the two
  synthetic-fixture tests below, to avoid duplicating coverage of the same
  underlying logic path.

## Implementation
### Target file
tests/tools/test_check_docs_quality.py

### Procedure
1. Extend `_make_doc_file`'s signature and path-less branch (lines 29-44):
   ```python
   def _make_doc_file(
       content: str, path: Path | None = None, tmp_name: str = ".tmp_test_doc.md"
   ) -> object:
       """Construct an object that behaves like DocFile for check functions."""

       class FakeDocFile:
           def __init__(self, content: str, path: Path | None = None) -> None:
               self.lines = content.splitlines()
               if path is not None:
                   self.path = path
                   self.rel_path = str(path.relative_to(_ROOT_DIR / "docs"))
               else:
                   tmp = _ROOT_DIR / tmp_name
                   tmp.write_text(content, encoding="utf-8")
                   self.path = tmp
                   self.rel_path = tmp_name

       return FakeDocFile(content, path)
   ```
2. `check_content_similarity` is already imported at line 14 (confirmed
   via Read, 2026-09-20) — no import change is needed.
3. Append a new class after `TestContentSimilarity` (after line 180):
   ```python
   class TestContentSimilarityCrossFile:
       def test_true_positive_cross_file_overlap(self):
           """Two different documents sharing a near-duplicate section body → expect cross-file Issue."""
           common_text = (
               "This is boilerplate content that appears in many documents. "
               "It describes the purpose and scope of the section."
           )
           content_a = f"# Title A\n\n## Section One\n\n{common_text}"
           content_b = f"# Title B\n\n## Section Two\n\n{common_text}"
           doc_a = _make_doc_file(content_a, tmp_name=".tmp_test_doc_a.md")
           doc_b = _make_doc_file(content_b, tmp_name=".tmp_test_doc_b.md")
           try:
               issues = check_content_similarity(_DOCS_DIR, [doc_a, doc_b])  # type: ignore[arg-type]  # — FakeDocFile duck-types DocFile
               assert len(issues) >= 1
               assert any(
                   doc_a.rel_path in issue.message and doc_b.rel_path in issue.message
                   for issue in issues
               )
           finally:
               (_ROOT_DIR / ".tmp_test_doc_a.md").unlink(missing_ok=True)
               (_ROOT_DIR / ".tmp_test_doc_b.md").unlink(missing_ok=True)

       def test_false_positive_cross_file_unrelated(self):
           """Two different documents with unrelated content → no cross-file Issue."""
           content_a = "# Title A\n\n## Section One\n\nCompletely unrelated discussion of widgets."
           content_b = "# Title B\n\n## Section Two\n\nA totally different discussion of gadgets."
           doc_a = _make_doc_file(content_a, tmp_name=".tmp_test_doc_a.md")
           doc_b = _make_doc_file(content_b, tmp_name=".tmp_test_doc_b.md")
           try:
               issues = check_content_similarity(_DOCS_DIR, [doc_a, doc_b])  # type: ignore[arg-type]  # — FakeDocFile duck-types DocFile
               assert issues == []
           finally:
               (_ROOT_DIR / ".tmp_test_doc_a.md").unlink(missing_ok=True)
               (_ROOT_DIR / ".tmp_test_doc_b.md").unlink(missing_ok=True)
   ```
4. Append a new test method to the existing `TestRegressionFullDocsTree`
   class (after `test_no_new_false_positives_on_full_docs_tree`, i.e.
   after line 230):
   ```python
   def test_cross_file_duplication_detected_on_full_docs_tree(self):
       """Run the extended checker against the full docs/ tree → confirm the
       within-file finding count is unchanged and the known governance_01/
       governance_04 duplication is now detected cross-file."""
       if not _DOCS_DIR.exists():
           pytest.skip(f"Docs directory not found: {_DOCS_DIR}")

       result = subprocess.run(
           [sys.executable, "-m", "tools.check_docs_quality"],
           capture_output=True,
           text=True,
           cwd=str(_ROOT_DIR),
       )
       output = result.stdout + result.stderr

       within_file_count = output.count("Content similarity detected between sections '")
       assert within_file_count == 206, (
           f"Expected 206 within-file content-similarity findings (Plan baseline), "
           f"got {within_file_count}"
       )

       assert (
           "00_governance_01_documentation-policy.md" in output
           and "00_governance_04_documentation-checks.md" in output
       ), "Expected a cross-file finding between the known governance_01/governance_04 duplication"
   ```

### Method
Three separate `Edit` calls (old_string/new_string): (1) the
`_make_doc_file` signature/body extension, (2) the new
`TestContentSimilarityCrossFile` class, (3) the new method appended to
`TestRegressionFullDocsTree`. Each is independently revertable. No import
change is needed (step 2 above).

### Details
Do not alter any of the 17 existing tests' bodies, the existing
`test_no_new_false_positives_on_full_docs_tree` method, or
`_make_doc_file`'s behavior for any existing call site (all 8 existing
call sites omit `tmp_name`, so they are unaffected by the new default
parameter). Confirm before finalizing that
`within_file_count == 206` in step 4's assertion matches the sibling
procedure's actual Step 4 full-tree review outcome — if that review found
a different within-file count due to an unrelated corpus change since this
Plan's baseline was recorded, update this test's expected count to match
current reality rather than the Plan's original baseline number, and note
the discrepancy in this document's Execution Status Notes.

## Compatibility considerations
Test-only change; no production code behavior affected beyond the additive
`tmp_name` parameter (backward-compatible default).

## Security considerations
N/A: test file, writes only to explicitly-named temp files it also cleans
up, no production code path affected.

## Rollback considerations
Revert via `git checkout` on this one file — no data migration or state
change is involved. Each of the 4 Method edits is independently
revertable.

## Validation plan
`uv run pytest tests/tools/test_check_docs_quality.py -v` — confirm 20
passed (17 existing + 3 new: 2 in `TestContentSimilarityCrossFile`, 1 in
`TestRegressionFullDocsTree`), 0 failed. Confirm no new file remains in
`git status --short` after the test run (the `try`/`finally` cleanup in the
2 new `TestContentSimilarityCrossFile` tests should leave no trace).

## Completion criteria
The 3 new tests exist, pass, and the working tree shows no new untracked
file after running them; the 17 existing tests still pass unmodified.

## Out of scope
- The cross-file comparison pass itself — implemented in the sibling
  `tools/check_docs_quality.py` procedure document (REQ-001, REQ-003).
- Any change to the 17 existing tests or `_make_doc_file`'s default
  behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` — add unit tests for the cross-file comparison path
- **Source issue**: issues/20260920-115531_docdup01tool_detect-cross-file-section-duplication-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-121316_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-131545
- **Related target files**: tests/tools/test_check_docs_quality.py
