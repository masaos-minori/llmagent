## Goal

Implement REQ-012 (`plans/20260923-152824_plan.md`) in
`tests/tools/test_check_needs_confirmation_inventory.py`: update the two
real-repository-path tests in `TestGovernanceMetaDocsCurrency` so both
continue to pass once the 4 governance files move to `docs/00_governance/`.

## Scope

Modify only `tests/tools/test_check_needs_confirmation_inventory.py`'s
`TestGovernanceMetaDocsCurrency` class:
1. `test_named_docs_exist_on_disk`: change `docs_dir / name` to
   `docs_dir / "00_governance" / name` (since `_GOVERNANCE_META_DOCS` stays
   bare per the source Plan's Assumptions).
2. `test_current_governance_filenames_are_covered`: change
   `docs_dir.glob("00_governance_*.md")` to
   `(docs_dir / "00_governance").glob("00_governance_*.md")`.

## Assumptions

- `_GOVERNANCE_META_DOCS` (imported from
  `tools.check_needs_confirmation_inventory`) stays a bare-filename
  frozenset — confirmed by seq 04's own design (its comparison-site fix, not
  a value change, per the source Plan's Assumptions) — so both tests here
  keep deriving/comparing bare basenames; only the `docs_dir` base changes.
- Depends on the physical governance-file move (`docsreorg05`) having
  landed for these 2 tests to actually pass — before that, `docs_dir /
  "00_governance"` won't exist yet, same coordinated-landing-order note
  documented throughout this Plan.
- No other test in this file has a real-repository-path dependency
  (confirmed via Read during the source Plan's drafting — every other test
  uses `tmp_path`-rooted synthetic fixtures).

## Design decisions

- A plain, non-recursive glob scoped to the one known subfolder
  (`(docs_dir / "00_governance").glob("00_governance_*.md")`) is sufficient
  for `test_current_governance_filenames_are_covered` — no need for
  `rglob`, since this test's own purpose is confirming exactly that one
  subfolder's contents match `_GOVERNANCE_META_DOCS`, not a repo-wide
  search.
- Keep both tests' overall structure and assertions unchanged — only the
  base directory each starts its filesystem lookup from changes.

## Alternatives considered

- Using `docs_dir.rglob("00_governance_*.md")` instead of scoping directly
  to the `00_governance` subfolder: rejected — broader than necessary, and
  the test's own intent (verifying `_GOVERNANCE_META_DOCS` against exactly
  that one subfolder's real contents) is best expressed by naming the
  subfolder explicitly.

## Implementation

### Target file

`tests/tools/test_check_needs_confirmation_inventory.py`

### Procedure

1. Locate `test_named_docs_exist_on_disk` (around line 34-40).
2. Change `if not (docs_dir / name).is_file()` to
   `if not (docs_dir / "00_governance" / name).is_file()`.
3. Locate `test_current_governance_filenames_are_covered` (around line
   44-51).
4. Change `{p.name for p in docs_dir.glob("00_governance_*.md")}` to
   `{p.name for p in (docs_dir / "00_governance").glob("00_governance_*.md")}`.

### Method

Two `Edit` calls, one per test method.

### Details

Current:
```python
    def test_named_docs_exist_on_disk(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent.parent
        docs_dir = repo_root / "docs"
        missing = [
            name for name in _GOVERNANCE_META_DOCS if not (docs_dir / name).is_file()
        ]
        assert missing == [], (
            f"_GOVERNANCE_META_DOCS names non-existent files: {missing}"
        )

    def test_current_governance_filenames_are_covered(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent.parent
        docs_dir = repo_root / "docs"
        real_governance_docs = {p.name for p in docs_dir.glob("00_governance_*.md")}
        assert real_governance_docs <= _GOVERNANCE_META_DOCS, (
            "A real docs/00_governance_*.md file is missing from "
            "_GOVERNANCE_META_DOCS: "
            f"{real_governance_docs - _GOVERNANCE_META_DOCS}"
        )
```

After modification:
```python
    def test_named_docs_exist_on_disk(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent.parent
        docs_dir = repo_root / "docs"
        missing = [
            name
            for name in _GOVERNANCE_META_DOCS
            if not (docs_dir / "00_governance" / name).is_file()
        ]
        assert missing == [], (
            f"_GOVERNANCE_META_DOCS names non-existent files: {missing}"
        )

    def test_current_governance_filenames_are_covered(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent.parent
        docs_dir = repo_root / "docs"
        real_governance_docs = {
            p.name for p in (docs_dir / "00_governance").glob("00_governance_*.md")
        }
        assert real_governance_docs <= _GOVERNANCE_META_DOCS, (
            "A real docs/00_governance_*.md file is missing from "
            "_GOVERNANCE_META_DOCS: "
            f"{real_governance_docs - _GOVERNANCE_META_DOCS}"
        )
```

## Compatibility considerations

- Depends on `docsreorg05` (governance physical move) landing before these 2
  tests pass against the real repository.
- No change to `_GOVERNANCE_META_DOCS`'s own values, or to any other test in
  this file.

## Security considerations

No security impact — test-only file.

## Rollback considerations

1. Revert both edits to their original `docs_dir`-relative form.
2. No other state to unwind.

## Validation plan

Run `uv run pytest tests/tools/test_check_needs_confirmation_inventory.py -q`
once `docsreorg05` has landed — expect all tests to pass. Before it lands,
both `TestGovernanceMetaDocsCurrency` tests are expected to fail (directory
not found), same coordinated-landing-order behavior as the rest of this
Plan.

## Completion criteria

- Both `TestGovernanceMetaDocsCurrency` tests scope their filesystem lookup
  to `docs_dir / "00_governance"`.
- `_GOVERNANCE_META_DOCS`'s own values are unchanged.
- All other tests in this file remain unaffected.

## Out of scope

- Any change to `tools/check_needs_confirmation_inventory.py` itself
  (tracked by seq 04).
- Any physical `docs/` file move (tracked by `docsreorg05`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-162740 | 20260923-162740 | stale_detector: no mismatches (clean pass). Both tests updated to scope docs_dir/00_governance. |
| 2 | Add or update tests per Validation plan | Completed | 20260923-162740 | 20260923-162740 | No new test added; this document's own scope is fixing existing tests. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-162740 | 20260923-162740 | ruff/mypy pass. bandit: 6 B101 findings, expected/standard for a pytest file. pytest: 3 passed, 1 failed. test_named_docs_exist_on_disk fails as expected (pre-move, docsreorg05 pending). test_current_governance_filenames_are_covered unexpectedly PASSES pre-move too -- (docs_dir/'00_governance').glob() on a non-existent directory returns an empty set, and an empty set is vacuously a subset of _GOVERNANCE_META_DOCS, so the assertion holds regardless of move status. This differs from this document's own Validation plan wording ('both tests are expected to fail') but is not a defect -- the test's own detection purpose (catching an un-tracked new governance file) still works correctly once docsreorg05 lands. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-162740 | 20260923-162740 | N/A: no docs/00_index.md task-scope mapping for tests/tools/test_check_needs_confirmation_inventory.py. |

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
- **Requirement ID**: REQ-012
- **Source issue**: issues/done/20260923-140602_docsreorg02_make-docs-domain-checkers-subfolder-aware.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-152824_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-153716
- **Related target files**: tests/tools/test_check_needs_confirmation_inventory.py