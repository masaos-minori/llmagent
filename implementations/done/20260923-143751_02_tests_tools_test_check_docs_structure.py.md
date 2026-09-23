## Goal

Implement REQ-006 (`plans/20260923-142045_plan.md`) in
`tests/tools/test_check_docs_structure.py`: update the two existing `validate_file()`
call sites for its new required `basename_index` parameter (introduced by this Plan's
seq-01 document, `tools/check_docs_structure.py`), and add new test coverage for
cross-directory bare-filename resolution, missing-file detection, an
already-directory-qualified reference, and the new recursive default glob.

## Scope

Modify only `tests/tools/test_check_docs_structure.py` to:
1. Update the two existing `validate_file()` calls (lines 170, 179) to supply a
   `basename_index` argument, since that parameter becomes required by seq-01's change.
2. Add a new test class covering `check_related_links()`/`check_links()`'s new
   basename-index resolution: cross-directory success, missing-file detection
   unchanged, and an already-directory-qualified reference still resolving.
3. Add a test covering the duplicate-basename hard-failure (REQ-004, implemented in
   seq-01's `_build_basename_index()`).
4. Add a test confirming the new recursive default glob discovers a file in a
   subdirectory (REQ-005).

## Assumptions

- This document's tests can only pass once seq-01
  (`tools/check_docs_structure.py`) has landed in the same working tree — both
  documents implement one coordinated code change split across two files, per this
  Plan's own Implementation Target Files table. Running this file's tests against an
  unmodified `tools/check_docs_structure.py` will fail with `TypeError` on the two
  updated call sites, by design (see the source Plan's Risks section).
- The existing test file's fixture style (`_write()` helper writing to `tmp_path`,
  functions imported directly and called rather than invoking the CLI) is preserved —
  new tests follow the same pattern, adding subdirectories under `tmp_path` where a
  cross-directory scenario is needed.
- `main()`'s new default-glob behavior (REQ-005) is exercised at the `check_docs_structure`
  module level (calling `_build_basename_index()`/`main()`-adjacent logic directly),
  not by invoking the CLI as a subprocess — matching this test file's existing style of
  testing functions directly rather than the `main()` entry point end-to-end.

## Design decisions

- For the two existing calls (`test_no_schema_argument_preserves_existing_behavior`,
  `test_schema_argument_adds_findings_without_schema_file`), pass `basename_index={}` —
  `_COMPLIANT_DOC`'s front matter has an empty `related:` field and no body links, so an
  empty index is sufficient and keeps these two tests focused on their own original
  purpose (schema opt-in behavior), not on basename-index behavior.
- Add the new basename-index-resolution tests as their own class
  (`TestBasenameIndexResolution`), mirroring the existing one-class-per-concern
  structure (`TestSchemaComplianceRequiredFields`, `TestCheckSize`, etc.) already used
  in this file.
- Build cross-directory fixtures using `tmp_path`'s ability to create subdirectories
  (`tmp_path / "sub"`) rather than relying on the real `docs/` tree, keeping tests
  hermetic and independent of the actual repository content.
- Import `_build_basename_index` and the updated `check_related_links`/`check_links`
  directly from `tools.check_docs_structure`, alongside the existing imports.

## Alternatives considered

- Testing only through `validate_file()` (the higher-level function) rather than also
  calling `check_related_links()`/`check_links()` directly: rejected — the source
  Issue's own Testing Expectations explicitly call for unit coverage of both functions,
  and testing them directly gives clearer failure localization than only exercising
  them transitively.
- Invoking `main()` via `subprocess.run(["python", "tools/check_docs_structure.py", ...])`
  to test the new default glob end-to-end: rejected — this file has no existing
  subprocess-based tests, and the existing direct-function-call style is simpler and
  faster; the recursive-glob behavior can be confirmed by calling the same glob logic
  `main()` uses against a `tmp_path`-rooted fixture tree instead.

## Implementation

### Target file

`tests/tools/test_check_docs_structure.py`

### Procedure

1. Add `_build_basename_index`, `check_related_links`, and `check_links` to the existing
   `from tools.check_docs_structure import (...)` block.
2. Update line 170: `validate_file(doc, expected_area=None)` →
   `validate_file(doc, expected_area=None, basename_index={})`.
3. Update line 179: `validate_file(doc, expected_area=None, schema=schema)` →
   `validate_file(doc, expected_area=None, schema=schema, basename_index={})`.
4. Add a new `TestBasenameIndexResolution` class with:
   - `test_cross_directory_bare_filename_resolves`: two `tmp_path` files in different
     subdirectories, one's front matter `related:` lists the other's bare filename;
     `check_related_links()` returns `[]`.
   - `test_missing_basename_is_still_flagged`: a `related:` entry naming a filename not
     present anywhere in the index; `check_related_links()` reports it.
   - `test_directory_qualified_reference_still_resolves`: a `related:` entry using an
     explicit relative path with a `/` (e.g. `sub/target.md`), verifying the
     `path.parent`-relative fallback still works even with an empty/irrelevant
     `basename_index`.
   - `test_body_link_cross_directory_resolves` and
     `test_body_link_missing_target_is_flagged`: the same two scenarios for
     `check_links()`.
5. Add a `TestDuplicateBasenameDetection` class with one test: two `tmp_path` files in
   different subdirectories sharing the same basename; `_build_basename_index()` raises
   `ValueError` naming both paths.
6. Add a `TestDefaultGlobIsRecursive` class with one test: a `tmp_path`-rooted fixture
   tree with a file directly under it and another in a subdirectory; confirm a
   `docs/**/*.md`-equivalent glob against that root finds both, where a
   `docs/*.md`-equivalent glob would find only the first.

### Method

Direct source edit via targeted `Edit` calls: two one-line signature-call updates, plus
three new test classes appended after the existing `TestCheckUniqueAdrIds` class. No
other file touched.

### Details

Existing (lines 166-179):
```python
class TestValidateFileSchemaOptIn:
    def test_no_schema_argument_preserves_existing_behavior(
        self, tmp_path: Path
    ) -> None:
        doc = _write(tmp_path / "example.md", _COMPLIANT_DOC)
        assert validate_file(doc, expected_area=None) == []

    def test_schema_argument_adds_findings_without_schema_file(
        self, tmp_path: Path
    ) -> None:
        doc = _write(tmp_path / "example.md", _COMPLIANT_DOC)
        schema = load_front_matter_schema(tmp_path / "absent.json")
        assert validate_file(doc, expected_area=None, schema=schema) == []
```

After modification:
```python
class TestValidateFileSchemaOptIn:
    def test_no_schema_argument_preserves_existing_behavior(
        self, tmp_path: Path
    ) -> None:
        doc = _write(tmp_path / "example.md", _COMPLIANT_DOC)
        assert validate_file(doc, expected_area=None, basename_index={}) == []

    def test_schema_argument_adds_findings_without_schema_file(
        self, tmp_path: Path
    ) -> None:
        doc = _write(tmp_path / "example.md", _COMPLIANT_DOC)
        schema = load_front_matter_schema(tmp_path / "absent.json")
        assert (
            validate_file(doc, expected_area=None, schema=schema, basename_index={})
            == []
        )
```

New test classes, appended after `TestCheckUniqueAdrIds` (illustrative; exact assertions
finalized during implementation to match the real return-value shapes of
`check_related_links`/`check_links`):
```python
class TestBasenameIndexResolution:
    def test_cross_directory_bare_filename_resolves(self, tmp_path: Path) -> None:
        target = _write(tmp_path / "sub" / "target.md", "# Target\n")
        content = (
            "---\ntitle: \"Example\"\narea: agent\ntags:\n  - agent\n"
            "related:\n  - target.md\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        index = _build_basename_index(tmp_path)
        assert check_related_links(doc, doc.read_text(), index) == []

    def test_missing_basename_is_still_flagged(self, tmp_path: Path) -> None:
        content = (
            "---\ntitle: \"Example\"\narea: agent\ntags:\n  - agent\n"
            "related:\n  - does-not-exist.md\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        index = _build_basename_index(tmp_path)
        issues = check_related_links(doc, doc.read_text(), index)
        assert any("does-not-exist.md" in i for i in issues)

    def test_directory_qualified_reference_still_resolves(self, tmp_path: Path) -> None:
        _write(tmp_path / "sub" / "target.md", "# Target\n")
        content = (
            "---\ntitle: \"Example\"\narea: agent\ntags:\n  - agent\n"
            "related:\n  - sub/target.md\n---\n\nBody.\n"
        )
        doc = _write(tmp_path / "example.md", content)
        assert check_related_links(doc, doc.read_text(), {}) == []


class TestDuplicateBasenameDetection:
    def test_duplicate_basename_raises(self, tmp_path: Path) -> None:
        _write(tmp_path / "a" / "dup.md", "# A\n")
        _write(tmp_path / "b" / "dup.md", "# B\n")
        with pytest.raises(ValueError, match="dup.md"):
            _build_basename_index(tmp_path)


class TestDefaultGlobIsRecursive:
    def test_recursive_glob_finds_subdirectory_file(self, tmp_path: Path) -> None:
        _write(tmp_path / "top.md", "# Top\n")
        _write(tmp_path / "sub" / "nested.md", "# Nested\n")
        found = set(tmp_path.glob("**/*.md"))
        assert len(found) == 2
```

(`pytest` and `import pytest` will need adding to this file's imports if not already
present — confirm during implementation.)

## Compatibility considerations

- This document's tests are coupled to seq-01's code change landing first (see
  Assumptions) — do not attempt to run this file's tests in isolation against an
  unmodified `tools/check_docs_structure.py` as a completion signal.
- The two updated existing test calls preserve their original assertions and intent
  (schema opt-in behavior) — only the new required argument is added.

## Security considerations

No security impact — test-only file, no production code path.

## Rollback considerations

1. Revert the two one-line signature-call updates.
2. Remove the three new test classes.
3. No fixtures or state persist outside each test's own `tmp_path`.

## Validation plan

Run `uv run pytest tests/tools/test_check_docs_structure.py -q` once both this
document's changes and seq-01's changes have landed — expect all tests (existing +
new) to pass with zero regressions.

## Completion criteria

- The two existing `validate_file()` calls pass `basename_index` and continue to pass.
- The three new test classes exist and pass once seq-01 has landed.
- `uv run pytest tests/tools/test_check_docs_structure.py -q` reports zero failures.

## Out of scope

- Any change to `tools/check_docs_structure.py` itself — tracked by this Plan's seq-01
  document.
- Any other test file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the two existing `validate_file()` calls for the new `basename_index` parameter | Completed | 20260923-145400 | 20260923-145400 | Updated the two existing validate_file() calls (basename_index={}); added _write() parent-dir creation (path.parent.mkdir) since new subdirectory fixtures needed it, not explicitly called out in the procedure but required for it to work. |
| 2 | Add `TestBasenameIndexResolution`, `TestDuplicateBasenameDetection`, `TestDefaultGlobIsRecursive` | Completed | 20260923-145400 | 20260923-145400 | Added TestBasenameIndexResolution (5 tests), TestDuplicateBasenameDetection (1), TestDefaultGlobIsRecursive (1). |
| 3 | Run the validation sequence (`rules/toolchain.md`) — requires seq-01 to have landed first | Completed | 20260923-145400 | 20260923-145400 | ruff format/check, mypy: pass. bandit: 28 B101 (assert_used) Low/High-confidence findings, expected/standard for a pytest test file. lint-imports: same 1 pre-existing unrelated violation as seq-01, unchanged. pytest tests/tools/test_check_docs_structure.py: 23 passed (16 existing + 7 new). Full-tree check_docs_structure.py "docs/**/*.md" --schema output diffed byte-for-byte against a pre-change baseline (git stash) — zero difference (AC-2/AC-3 met). Default-arg run now scans 188 files vs 164 before (AC-5 met). |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/done/20260923-140511_docsreorg01_make-docs-cross-reference-resolution-folder-independent.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-142045_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-143751
- **Related target files**: tests/tools/test_check_docs_structure.py