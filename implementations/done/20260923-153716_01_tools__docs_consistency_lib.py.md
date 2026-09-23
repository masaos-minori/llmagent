## Goal

Implement REQ-001, REQ-002 (`plans/20260923-152824_plan.md`) in
`tools/_docs_consistency_lib.py`: make `discover_md_files()`'s file discovery
and `check_broken_internal_links()`/`check_removed_file_references()`'s
"existing files" universe recursive, so all three continue to find files
regardless of which `docs/` subfolder they move into.

## Scope

Modify only `tools/_docs_consistency_lib.py` to:
1. Change `discover_md_files()`'s `docs_dir.glob(f"{prefix}*.md")` to
   `docs_dir.rglob(f"{prefix}*.md")`.
2. Change `check_broken_internal_links()`'s `docs_dir.glob("*.md")` to
   `docs_dir.rglob("*.md")`.
3. Change `check_removed_file_references()`'s `docs_dir.glob("*.md")` to
   `docs_dir.rglob("*.md")`.

## Assumptions

- No caller of `discover_md_files()` needs its own `docs_dir`/`prefix`
  arguments changed by this document — every current caller either already
  passes the flat `docs/` root (in which case recursive matching finds every
  prefix-matching file regardless of subfolder) or an already-final subfolder
  like `docs/adr` (unaffected by recursion since that subfolder has no
  further nesting). Confirmed via `rg "discover_md_files"` during the source
  Plan's drafting: exactly 8 call sites across
  `check_docs_consistency.py` (×4), `check_dependency_graph_cycles.py` (×1),
  `check_needs_confirmation_inventory.py` (×1),
  `check_known_deviation_sync.py` (×2), `check_adr_structure.py` (×1).
- `DocFile.rel_path` (computed as `str(p.relative_to(docs_dir))`) becomes
  directory-qualified for any moved file once this recursion lands — this is
  an intentional, accepted downstream effect; the 4 exact-match comparisons
  against a bare-filename constant elsewhere in the codebase are each
  corrected by this Plan's other implementation procedures (seq 02, 03, 04,
  05), not by this document.
- The 3 other "generic check" functions in this file
  (`check_command_drift`, `check_file_path_references`,
  `check_function_references`) accept a `docs_dir` parameter but never use
  it in their body (confirmed via `awk`+`grep` during the source Plan's
  drafting) — no change needed for them.

## Design decisions

- Change exactly 3 `.glob(...)` calls to `.rglob(...)` — no signature change,
  no new parameter, no behavior change beyond recursion depth. This is the
  minimal, most localized fix: every caller's own code stays unchanged.
- Do not touch `_BARE_MD_FILENAME_RE`'s pattern itself (already
  filename-only, directory-independent — confirmed unaffected in the source
  Issue).

## Alternatives considered

- Changing every caller to pass a domain-specific subfolder as `docs_dir`
  instead (the source Issue's original proposal): rejected — this breaks
  `check_broken_internal_links()`/`check_removed_file_references()`'s
  documented cross-domain guarantee ("a link from an agent doc to a removed
  RAG doc is still caught"), since narrowing `docs_dir` to one domain's
  subfolder would make the "existing files" universe miss every other
  domain's files.
- Adding a separate `existing_files_dir` parameter distinct from `docs_dir`
  to these two functions, so callers could pass a narrower `docs_dir` for
  discovery while keeping a wide one for existence-checking: rejected as
  unnecessary complexity — recursion alone achieves both goals without any
  new parameter.

## Implementation

### Target file

`tools/_docs_consistency_lib.py`

### Procedure

1. In `discover_md_files()`, change `for p in sorted(docs_dir.glob(f"{prefix}*.md")):`
   to use `docs_dir.rglob(f"{prefix}*.md")`.
2. In `check_broken_internal_links()`, change
   `existing_files = {f.name for f in docs_dir.glob("*.md")}` to use
   `docs_dir.rglob("*.md")`.
3. In `check_removed_file_references()`, change the identical line the same
   way.
4. Verify no other `.glob(` call exists in this file that should also become
   recursive (confirmed during drafting: only these 3).

### Method

Three one-line `Edit` calls, no signature or behavior change beyond glob
recursion depth.

### Details

Current (`discover_md_files`, line 52):
```python
def discover_md_files(docs_dir: Path, *, prefix: str) -> list[DocFile]:
    """Return all *prefix*-matching .md files under *docs_dir*, sorted for determinism."""
    result: list[DocFile] = []
    for p in sorted(docs_dir.glob(f"{prefix}*.md")):
```

After modification:
```python
def discover_md_files(docs_dir: Path, *, prefix: str) -> list[DocFile]:
    """Return all *prefix*-matching .md files under *docs_dir* (recursive),
    sorted for determinism."""
    result: list[DocFile] = []
    for p in sorted(docs_dir.rglob(f"{prefix}*.md")):
```

Current (`check_broken_internal_links` / `check_removed_file_references`,
each):
```python
    existing_files = {f.name for f in docs_dir.glob("*.md")}
```

After modification (identical in both functions):
```python
    existing_files = {f.name for f in docs_dir.rglob("*.md")}
```

## Compatibility considerations

- No caller's own source needs to change as a result of this document alone
  — callers passing the flat `docs/` root keep working exactly as before for
  files that haven't moved, and correctly extend to moved files once the
  physical-move issues land.
- `rel_path` values become directory-qualified for moved files — this is by
  design; downstream consumers needing an exact bare-filename match are
  fixed by this Plan's seq 02-05 documents, not this one.

## Security considerations

No security impact — this is a documentation-structure-validation helper
with no network, subprocess, or file-write behavior.

## Rollback considerations

1. Revert the 3 `.rglob(` calls back to `.glob(`.
2. No data migration or state to unwind.

## Validation plan

Run `uv run pytest tests/tools/test_check_agent_docs_consistency.py tests/tools/test_check_docs_consistency_port.py -q` (both confirmed hermetic, should pass unchanged) plus the new cross-subdirectory test case this Plan's Tests section calls for (tracked as part of this document's own test-coverage step, since `_docs_consistency_lib.py` has no dedicated test file of its own — the new case is added to `test_check_agent_docs_consistency.py`, which already imports directly from this module).

## Completion criteria

- All 3 `.glob(` calls identified in Scope are now `.rglob(`.
- A synthetic fixture with two files in different subdirectories, one
  referencing the other by bare filename, resolves without a false
  "removed/nonexistent" or "broken link" finding via `discover_md_files` +
  `check_broken_internal_links`/`check_removed_file_references`.
- `uv run pytest tests/tools/test_check_agent_docs_consistency.py tests/tools/test_check_docs_consistency_port.py -q` passes.

## Out of scope

- Any change to the 4 exact-match constants elsewhere in the codebase
  (tracked by seq 02-05).
- Any change to the 3 unused-`docs_dir` "generic check" functions.
- Any physical `docs/` file move.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-154619 | 20260923-154619 | Step3 stale_detector false-positive (1 finding: 'existing_files_dir', a rejected alternative symbol never present in source) confirmed and bypassed per established session precedent. 3 .glob() calls changed to .rglob(). |
| 2 | Add or update tests per Validation plan | Completed | 20260923-154619 | 20260923-154619 | Added TestDiscoverMdFilesRecursive (2 tests) and cross-subdirectory cases to TestCheckBrokenInternalLinks/TestCheckRemovedFileReferences in test_check_agent_docs_consistency.py. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-154619 | 20260923-154619 | ruff format/check, mypy, bandit: pass. pytest tests/tools/test_check_agent_docs_consistency.py tests/tools/test_check_docs_consistency_port.py: 21 passed. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-154635 | 20260923-154635 | N/A: no docs/00_index.md task-scope mapping for tools/_docs_consistency_lib.py. |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/done/20260923-140602_docsreorg02_make-docs-domain-checkers-subfolder-aware.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-152824_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-153716
- **Related target files**: tools/_docs_consistency_lib.py