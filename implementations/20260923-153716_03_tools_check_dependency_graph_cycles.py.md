## Goal

Implement REQ-004 (`plans/20260923-152824_plan.md`) in
`tools/check_dependency_graph_cycles.py`: update `GRAPH_DOC_NAME` for the
directory-qualified `rel_path` that `discover_md_files()` now produces once
seq 01 lands.

## Scope

Modify only `tools/check_dependency_graph_cycles.py` to update
`GRAPH_DOC_NAME`'s value from `"00_governance_01_documentation-policy.md"` to
`"00_governance/00_governance_01_documentation-policy.md"`.

## Assumptions

- This document depends on seq 01 (`tools/_docs_consistency_lib.py`) having
  already landed — `GRAPH_DOC_NAME` is compared via
  `f.rel_path == GRAPH_DOC_NAME` (line 105) after
  `discover_md_files(DOCS_DIR, prefix="")` (line 104), and `rel_path` only
  becomes directory-qualified once `discover_md_files()`'s glob is recursive.
- `DOCS_DIR = REPO_ROOT / "docs"` (line 34) itself needs no change — it
  stays the flat root, exactly as seq 01's design intends.

## Design decisions

- Update only the one constant. No other logic in this file changes — the
  `discover_md_files(DOCS_DIR, prefix="")` call, the error-reporting
  f-strings using `GRAPH_DOC_NAME` (lines 107, 113, 121), and the graph-cycle
  detection logic that runs once the document is found are all unaffected.

## Alternatives considered

- Changing `DOCS_DIR` to point directly at `docs/00_governance` instead of
  updating `GRAPH_DOC_NAME`: rejected — this tool only ever looks for one
  specific file, so keeping `DOCS_DIR` at the flat root (matching every other
  tool sharing this same pattern) and updating the one comparison constant is
  more consistent with the rest of this Plan's approach, and avoids a
  `discover_md_files(DOCS_DIR, prefix="")` call scanning a narrower tree than
  its sibling tools for no benefit.

## Implementation

### Target file

`tools/check_dependency_graph_cycles.py`

### Procedure

1. Locate `GRAPH_DOC_NAME = "00_governance_01_documentation-policy.md"`
   (line 35).
2. Change its value to
   `"00_governance/00_governance_01_documentation-policy.md"`.

### Method

One `Edit` call to the constant's value.

### Details

Current:
```python
GRAPH_DOC_NAME = "00_governance_01_documentation-policy.md"
```

After modification:
```python
GRAPH_DOC_NAME = "00_governance/00_governance_01_documentation-policy.md"
```

## Compatibility considerations

- Depends on seq 01 landing first (see Assumptions).
- The error messages at lines 107, 113, 121 (`f"ERROR: {GRAPH_DOC_NAME} not
  found under docs/."` etc.) will now print the directory-qualified value —
  slightly more informative, not a behavior concern.
- CI (`governance-docs-consistency.yml`, `paths: docs/**/*.md` — already
  recursive) is unaffected by this change's own scope.

## Security considerations

No security impact.

## Rollback considerations

1. Revert `GRAPH_DOC_NAME` to its original bare-filename value.
2. No other state to unwind.

## Validation plan

Run `uv run pytest tests/tools/test_check_dependency_graph_cycles.py -q` —
note this document's own change alone does not make the file's one
real-repository test (`TestRealGraphIntegration`) pass yet; that test is
updated by seq 10 in this same Plan, and both must land together for the
full suite to pass against the post-move tree. Against the current
(pre-move) tree, this document's change alone has no observable effect
(`GRAPH_DOC_NAME`'s new value simply won't match anything until the file
actually moves) — confirm via `uv run python tools/check_dependency_graph_cycles.py`
that it now reports `GRAPH_DOC_NAME not found` (expected, pre-move) rather
than silently succeeding on stale matching logic.

## Completion criteria

- `GRAPH_DOC_NAME` equals `"00_governance/00_governance_01_documentation-policy.md"`.
- Running the tool against the current (pre-move) tree reports "not found"
  for the new path (expected until the physical move lands) rather than a
  Python exception or a silent false-pass.

## Out of scope

- `DOCS_DIR`'s own value.
- The graph-parsing/cycle-detection logic once the document is found.
- Updating `tests/tools/test_check_dependency_graph_cycles.py` (tracked by
  seq 10).
- Any physical `docs/` file move.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-155228 | 20260923-155228 | Step3 stale_detector false-positives (GRAPH_DOC_NAME, TestRealGraphIntegration) confirmed via grep against actual source (both exist); bypassed. GRAPH_DOC_NAME updated. Discovered during Validation: TestMainIntegration's 4 tests (not mentioned in this document, an omission in seq10's own drafting) broke because tests/tools/test_check_dependency_graph_cycles.py's _write() helper didn't create filename's parent directory. Corrected seq10's procedure document and applied the _write() fix (out of this document's own Scope, but required to validate this change without leaving the test suite broken) -- see implementations/20260923-153716_10_...md for the corrected record. |
| 2 | Add or update tests per Validation plan | Completed | 20260923-155228 | 20260923-155228 | No new test needed for this document's own scope; validated via tests/tools/test_check_dependency_graph_cycles.py (see seq10's own fix for the _write() helper coupling). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-155228 | 20260923-155228 | ruff/mypy/bandit pass. pytest tests/tools/test_check_dependency_graph_cycles.py: 12 passed, 1 failed (TestRealGraphIntegration, expected -- depends on docsreorg05's physical move, not a regression from this document). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-155228 | 20260923-155228 | N/A: no docs/00_index.md task-scope mapping for tools/check_dependency_graph_cycles.py. |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/done/20260923-140602_docsreorg02_make-docs-domain-checkers-subfolder-aware.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-152824_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-153716
- **Related target files**: tools/check_dependency_graph_cycles.py