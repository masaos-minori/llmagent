## Goal

Implement REQ-005 (`plans/20260923-152824_plan.md`) in
`tools/check_needs_confirmation_inventory.py`: update `INVENTORY_DOC_NAME`
for the directory-qualified `rel_path`, and fix the `_GOVERNANCE_META_DOCS`
membership check to compare basenames instead of full `rel_path`.

## Scope

Modify only `tools/check_needs_confirmation_inventory.py` to:
1. Change `INVENTORY_DOC_NAME`'s value from
   `"00_governance_03_issue-and-uncertainty-management.md"` to
   `"00_governance/00_governance_03_issue-and-uncertainty-management.md"`.
2. Change `doc.rel_path in _GOVERNANCE_META_DOCS` (line 184) to compare
   `Path(doc.rel_path).name in _GOVERNANCE_META_DOCS` instead.
3. **Correction found during this document's own implementation**
   (2026-09-23): `check_stale_resolved_markers()` (line ~153) builds its own
   local `by_name = {f.name: f for f in docs_dir.glob("*.md")}` lookup —
   another non-recursive glob this Plan's original drafting missed (it is a
   local helper inside this file, not one of `_docs_consistency_lib.py`'s
   shared functions covered by seq 01). `entry.source_file` (an NC entry's
   hand-written `**Source File**: `...``  field) stays a bare filename
   regardless of the physical move, so once a cited source file moves into a
   subfolder, `by_name.get(entry.source_file)` silently returns `None` and
   `check_stale_resolved_markers()` stops detecting a stale "resolved"
   marker for it — the same silent-safety-net-loss failure mode the source
   Issue warned about. Fix: change this glob to `docs_dir.rglob("*.md")` too.

## Assumptions

- This document depends on seq 01 (`tools/_docs_consistency_lib.py`) having
  already landed — both `INVENTORY_DOC_NAME` and `_GOVERNANCE_META_DOCS` are
  compared against `rel_path`, which only becomes directory-qualified once
  `discover_md_files()`'s glob is recursive.
- `_GOVERNANCE_META_DOCS`'s own 4 values stay unchanged (bare filenames) —
  its own test,
  `tests/tools/test_check_needs_confirmation_inventory.py::TestGovernanceMetaDocsCurrency::test_current_governance_filenames_are_covered`,
  independently derives bare `p.name` values via
  `{p.name for p in docs_dir.glob("00_governance_*.md")}` and checks them
  against this same set; making the set directory-qualified would make that
  comparison permanently fail. The membership-check site is fixed instead
  (this document's own change 2), while the test itself is updated
  separately by seq 11.
- `INVENTORY_DOC_NAME` is one of the 4 entries in `_GOVERNANCE_META_DOCS`
  (both name the same file,
  `"00_governance_03_issue-and-uncertainty-management.md"`) — confirmed via
  Read. `INVENTORY_DOC_NAME` itself is used only for the single exact-match
  lookup (`f.rel_path == INVENTORY_DOC_NAME`, line 234) and in display
  f-strings (lines 168, 195, 236) — none of those other uses depend on it
  staying bare, so it alone becomes directory-qualified.

## Design decisions

- Two independent, small changes in one file: a constant-value update
  (`INVENTORY_DOC_NAME`) and a comparison-logic fix
  (`_GOVERNANCE_META_DOCS` membership check) — these follow different
  patterns because `INVENTORY_DOC_NAME` is a single exact-match target while
  `_GOVERNANCE_META_DOCS` is a set independently derived and consumed as
  bare basenames elsewhere (see Assumptions).
- Use `Path(doc.rel_path).name` (import already present via this module's
  existing `from pathlib import Path`, confirm during implementation) rather
  than a manual `.rsplit("/", 1)[-1]` string operation, for clarity and
  correctness on any platform path-separator edge case.

## Alternatives considered

- Making `_GOVERNANCE_META_DOCS` directory-qualified instead of fixing the
  comparison site: rejected — breaks
  `test_current_governance_filenames_are_covered`'s own bare-basename
  derivation logic (see Assumptions); the comparison-site fix is the only
  option consistent with that test's existing, unchanged design.

## Implementation

### Target file

`tools/check_needs_confirmation_inventory.py`

### Procedure

1. Locate `INVENTORY_DOC_NAME = "00_governance_03_issue-and-uncertainty-management.md"`
   (line 44).
2. Change its value to
   `"00_governance/00_governance_03_issue-and-uncertainty-management.md"`.
3. Locate `if doc.rel_path in _GOVERNANCE_META_DOCS:` (line 184).
4. Change it to `if Path(doc.rel_path).name in _GOVERNANCE_META_DOCS:`.
5. Confirm `Path` is already imported at module level (expected, given
   `Path` is used throughout this file already for `DOCS_DIR`).
6. Locate `by_name = {f.name: f for f in docs_dir.glob("*.md")}` inside
   `check_stale_resolved_markers()` (line ~153).
7. Change it to `docs_dir.rglob("*.md")`.

### Method

Two `Edit` calls: one constant-value update, one comparison-logic fix.

### Details

Current:
```python
INVENTORY_DOC_NAME = "00_governance_03_issue-and-uncertainty-management.md"
...
        if doc.rel_path in _GOVERNANCE_META_DOCS:
            continue
```

After modification:
```python
INVENTORY_DOC_NAME = "00_governance/00_governance_03_issue-and-uncertainty-management.md"
...
        if Path(doc.rel_path).name in _GOVERNANCE_META_DOCS:
            continue
```

`_GOVERNANCE_META_DOCS` itself (lines 57-64) is unchanged.

## Compatibility considerations

- Depends on seq 01 landing first (see Assumptions).
- `_GOVERNANCE_META_DOCS`'s own 4 bare-filename values are untouched — no
  ripple to `test_current_governance_filenames_are_covered`'s existing logic.
- CI (`governance-docs-consistency.yml`) is unaffected by this change's own
  scope.

## Security considerations

No security impact.

## Rollback considerations

1. Revert `INVENTORY_DOC_NAME` to its original bare-filename value.
2. Revert the `_GOVERNANCE_META_DOCS` membership check to
   `doc.rel_path in _GOVERNANCE_META_DOCS`.
3. No other state to unwind.

## Validation plan

Run `uv run pytest tests/tools/test_check_needs_confirmation_inventory.py -q`
— note the file's 2 real-repository tests
(`TestGovernanceMetaDocsCurrency`) are updated separately by seq 11; both
must land together with this document for the full file's suite to pass
against the post-move tree. Against the current (pre-move) tree, manually
confirm `check_untracked_inline_markers()`'s exclusion still correctly skips
a synthetic governance-meta-doc fixture placed in a subdirectory (basename
match, not full-path match).

## Completion criteria

- `INVENTORY_DOC_NAME` equals
  `"00_governance/00_governance_03_issue-and-uncertainty-management.md"`.
- The `_GOVERNANCE_META_DOCS` membership check compares
  `Path(doc.rel_path).name`, not the full `rel_path`.
- `_GOVERNANCE_META_DOCS`'s own 4 values remain bare filenames, unchanged.

## Out of scope

- `_GOVERNANCE_META_DOCS`'s own values.
- `DOCS_DIR`'s own value.
- Updating `tests/tools/test_check_needs_confirmation_inventory.py` (tracked
  by seq 11).
- Any physical `docs/` file move.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-161040 | 20260923-161040 | Step3 stale_detector false-positives (INVENTORY_DOC_NAME, _GOVERNANCE_META_DOCS, etc.) confirmed via grep against actual source; bypassed. INVENTORY_DOC_NAME updated; _GOVERNANCE_META_DOCS membership check changed to basename comparison. Additional discovery: check_stale_resolved_markers()'s own local by_name={f.name:f for f in docs_dir.glob(...)} lookup (not covered by seq01, a local helper in this file) had the same non-recursive-glob issue -- corrected this document's own procedure and fixed it too (docs_dir.glob -> docs_dir.rglob). |
| 2 | Add or update tests per Validation plan | Completed | 20260923-161040 | 20260923-161040 | No new test file needed; manually verified check_untracked_inline_markers() correctly excludes a subdirectory-placed governance-meta-doc via basename match (synthetic DocFile fixture). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-161040 | 20260923-161040 | ruff/mypy/bandit pass. pytest tests/tools/test_check_needs_confirmation_inventory.py: 4 passed (TestGovernanceMetaDocsCurrency's 2 tests still pass because seq11 -- not yet run -- keeps their docs_dir logic matching the still-unmoved real files). Direct tool run against real tree: exit 1, 'INVENTORY_DOC_NAME not found' -- expected pre-move state (was exit 0 with 11 pre-existing WARNINGs before this change; docsreorg05 must land for main() to find the inventory again). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-161040 | 20260923-161040 | N/A: no docs/00_index.md task-scope mapping for tools/check_needs_confirmation_inventory.py. |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/done/20260923-140602_docsreorg02_make-docs-domain-checkers-subfolder-aware.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-152824_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-153716
- **Related target files**: tools/check_needs_confirmation_inventory.py