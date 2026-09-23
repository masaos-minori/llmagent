## Goal

Implement REQ-011 (`plans/20260923-152824_plan.md`) in
`tests/tools/test_check_dependency_graph_cycles.py`: update the one
real-repository-path test so it continues to pass once the governance file
moves to `docs/00_governance/`.

## Scope

Modify only `tests/tools/test_check_dependency_graph_cycles.py`:
1. `TestRealGraphIntegration.test_real_repo_graph_has_no_cycle` — build
   `doc_path` with the new `00_governance/` directory segment (no edit
   needed, see Design decisions).
2. **Correction found during seq 03's implementation** (2026-09-23): this
   file's own `_write(dir_path, filename, content)` helper only creates
   `dir_path` itself (`dir_path.mkdir(parents=True, exist_ok=True)`), not
   `(dir_path / filename).parent` — so once `GRAPH_DOC_NAME` becomes
   directory-qualified (seq 03's change), every call using
   `_write(tmp_path, GRAPH_DOC_NAME, ...)` fails with `FileNotFoundError`
   (the `00_governance/` subdirectory under `tmp_path` doesn't exist). This
   affects `TestMainIntegration`'s 4 tests
   (`test_cycle_free_graph_exits_zero`, `test_synthetic_cycle_exits_nonzero`,
   `test_missing_section_exits_nonzero`, `test_unknown_node_exits_nonzero`)
   — confirmed via running the full file's suite after seq 03 landed: these
   4 plus `TestRealGraphIntegration`'s 1 failed, `test_missing_doc_file_exits_nonzero`
   (which doesn't call `_write`) and all other hermetic tests passed. This
   was not identified during this Plan's original drafting — `_write()`'s
   own behavior with a directory-qualified `filename` argument was not
   checked at that time. The fix: change `_write()` to create
   `(dir_path / filename).parent` instead of `dir_path` itself.

## Assumptions

- Originally (at Plan-drafting time): this was believed to be the only test
  in this file with a real-repository-path dependency — every other test
  uses `monkeypatch.setattr(cdgc, "DOCS_DIR", tmp_path)` (hermetic).
  **Corrected**: that remains true for *real-repository-path* dependence
  specifically (`TestMainIntegration` still never touches the real `docs/`
  tree, it uses `tmp_path` throughout) — but 4 of those "hermetic" tests
  turned out to share a different, newly-discovered dependency on
  `GRAPH_DOC_NAME` staying a bare filename via the `_write()` helper's
  parent-directory assumption (see Scope item 2).
- This document depends on seq 03 (`tools/check_dependency_graph_cycles.py`,
  which updates `GRAPH_DOC_NAME` to include the same `00_governance/` prefix)
  having already landed — this test imports `GRAPH_DOC_NAME` directly rather
  than hardcoding the bare filename, so once seq 03 lands, `GRAPH_DOC_NAME`
  itself already carries the new directory-qualified value; this document
  only needs to add the corresponding directory segment to its own
  `doc_path` construction, which builds the path independently
  (`repo_root / "docs" / GRAPH_DOC_NAME`).
- Confirmed via Read: this test also depends on the physical governance-file
  move (`docsreorg05`) having landed, since it reads the real file's content
  — this is the same coordinated-landing-order note already documented for
  every other document in this Plan touching a governance/ADR constant.

## Design decisions

- Since `doc_path = repo_root / "docs" / GRAPH_DOC_NAME` already imports
  `GRAPH_DOC_NAME` from the tool module (confirmed via the file's own
  imports), and `GRAPH_DOC_NAME` itself becomes directory-qualified once seq
  03 lands, this test's `doc_path` construction is automatically correct
  without any change to this specific line. Confirmed via direct check during
  this document's own drafting: `Path("a") / "b/c"` evaluates to `Path("a/b/c")`
  (Python's `Path.__truediv__` splits a `/`-containing string on the
  right-hand side correctly), so once `GRAPH_DOC_NAME` equals
  `"00_governance/00_governance_01_documentation-policy.md"`,
  `repo_root / "docs" / GRAPH_DOC_NAME` correctly evaluates to
  `repo_root/docs/00_governance/00_governance_01_documentation-policy.md`.
  **No edit to this line is needed** — this document's only action is
  verifying this fact and recording it, per Procedure below.

## Alternatives considered

- Hardcoding the new directory segment separately from `GRAPH_DOC_NAME` in
  this test (e.g. `repo_root / "docs" / "00_governance" / GRAPH_DOC_NAME`
  where `GRAPH_DOC_NAME` would then need to stay bare): rejected — this would
  require `GRAPH_DOC_NAME` itself to stay bare, contradicting seq 03's own
  design (which makes `GRAPH_DOC_NAME` directory-qualified specifically so
  the `f.rel_path == GRAPH_DOC_NAME` exact-match comparison keeps working).
  Since this test already imports and reuses `GRAPH_DOC_NAME` rather than
  hardcoding its own copy of the filename, no divergence is introduced either
  way — confirming via the Design decisions check above is the correct,
  minimal-risk path.

## Implementation

### Target file

`tests/tools/test_check_dependency_graph_cycles.py`

### Procedure

1. Locate `TestRealGraphIntegration.test_real_repo_graph_has_no_cycle`
   (around line 175-184). No source edit is required — `doc_path = repo_root
   / "docs" / GRAPH_DOC_NAME` already resolves correctly once seq 03's
   `GRAPH_DOC_NAME` update has landed (confirmed via the `Path` behavior
   check in Design decisions).
2. Locate the `_write()` helper (near the top of the file, before
   `_CYCLE_FREE_DOC`). Change `dir_path.mkdir(parents=True, exist_ok=True)`
   to `(dir_path / filename).parent.mkdir(parents=True, exist_ok=True)`.
3. Record both findings (item 1's no-edit confirmation, item 2's fix) in
   this document's own Execution Status Notes for traceability.

### Method

One `Edit` call to `_write()`'s helper body; no edit to
`TestRealGraphIntegration` itself.

### Details

`TestRealGraphIntegration` — current (and final — no change):
```python
    def test_real_repo_graph_has_no_cycle(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent.parent
        doc_path = repo_root / "docs" / GRAPH_DOC_NAME
        assert doc_path.is_file(), f"{doc_path} not found"
```

This is already correct once `GRAPH_DOC_NAME` (imported from the tool
module, updated by seq 03) equals
`"00_governance/00_governance_01_documentation-policy.md"` — confirmed via
the `Path` combination check in Design decisions.

`_write()` helper — current:
```python
def _write(dir_path: Path, filename: str, content: str) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / filename).write_text(content, encoding="utf-8")
```

After modification:
```python
def _write(dir_path: Path, filename: str, content: str) -> None:
    (dir_path / filename).parent.mkdir(parents=True, exist_ok=True)
    (dir_path / filename).write_text(content, encoding="utf-8")
```

## Compatibility considerations

- `TestRealGraphIntegration` depends on seq 03 (`GRAPH_DOC_NAME` update) and
  `docsreorg05` (physical governance-file move) both landing before it
  passes against the real repository.
- `_write()`'s fix restores `TestMainIntegration`'s 4 tests to passing
  immediately once seq 03 lands (no dependency on `docsreorg05`, since those
  4 tests are fully hermetic via `monkeypatch`).

## Security considerations

No security impact — test-only file.

## Rollback considerations

1. Revert `_write()`'s helper body to its original `dir_path.mkdir(...)`
   form.
2. No other state to unwind.

## Validation plan

Run `uv run pytest tests/tools/test_check_dependency_graph_cycles.py -q`
once seq 03 has landed — expect `TestMainIntegration`'s 4 tests and every
other hermetic test to pass immediately. `TestRealGraphIntegration` remains
expected to fail until `docsreorg05` (physical governance-file move) also
lands — this is the same coordinated-landing-order behavior documented
throughout this Plan, not a regression.

## Completion criteria

- `_write()` creates `(dir_path / filename).parent`, not `dir_path` itself.
- `TestMainIntegration`'s 4 tests pass once seq 03 lands (no dependency on
  `docsreorg05`).
- `test_real_repo_graph_has_no_cycle` passes once seq 03 and `docsreorg05`
  have both landed.
- Every other test in this file continues to pass unaffected.

## Out of scope

- Any change to `tools/check_dependency_graph_cycles.py` itself (tracked by
  seq 03).
- Any physical `docs/` file move (tracked by `docsreorg05`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-155214 | 20260923-162624 | Partial: _write() helper's parent-directory fix applied early (during seq03's own validation, to unblock TestMainIntegration's 4 tests which broke as a side effect of seq03's GRAPH_DOC_NAME change -- this document's own procedure was corrected to record this finding). test_real_repo_graph_has_no_cycle itself still Pending (depends on docsreorg05). This document's own cycle (seq10) is NOT being run in full as part of this batch -- only the urgent shared-helper fix was applied. Confirmed complete: _write() helper fix (applied earlier during seq03's validation) verified still in place. Step3 stale_detector false-positives (FileNotFoundError mentioned in prose, doc_path scope-misattributed) confirmed as noise, bypassed. TestRealGraphIntegration itself correctly needs no source edit (GRAPH_DOC_NAME already directory-qualified via seq03). |
| 2 | Add or update tests per Validation plan | Completed | 20260923-162624 | 20260923-162624 | No new test added; this document's own scope is fixing existing tests, not adding new ones. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-162624 | 20260923-162624 | ruff/mypy pass. bandit: 24 B101 (assert_used) Low/High-confidence findings, expected/standard for a pytest file. pytest tests/tools/test_check_dependency_graph_cycles.py: 12 passed (including TestMainIntegration's 4), 1 failed (TestRealGraphIntegration, expected -- depends on docsreorg05's physical move). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-162624 | 20260923-162624 | N/A: no docs/00_index.md task-scope mapping for tests/tools/test_check_dependency_graph_cycles.py. |

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
- **Requirement ID**: REQ-011
- **Source issue**: issues/done/20260923-140602_docsreorg02_make-docs-domain-checkers-subfolder-aware.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-152824_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-153716
- **Related target files**: tests/tools/test_check_dependency_graph_cycles.py