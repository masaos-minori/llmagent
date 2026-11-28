# Implementation Procedure — scripts/mcp_servers/mdq/index_scan.py

## Goal

Make file discovery deterministic: explicit case behavior, canonical deduplication, and a stated
symlink-directory behavior, while keeping the module free of database access and authorization.

## Scope
**Release unit**: byte-limit-key-rename (the Plan groups Phase 4 in this unit; this document's
change is the scan-semantics half of that phase)

Requirement implemented: REQ-005 (scan semantics are deterministic). Acceptance criterion: AC-4.

## Assumptions
- The module keeps its boundary: discovery only, no database access and no authorization.
  Re-authorization and re-stat are applied by `scripts/mcp_servers/mdq/indexer.py` (procedure seq 02).
- Symlinked directories are not traversed and symlinked files are discovered; the Plan states that
  behavior in the documentation instead of changing it.
- On the project's POSIX runtime `fnmatch.fnmatch()` is already case-sensitive, so the change makes
  the behavior explicit rather than altering it.
- The plan's Assumptions keep `index_scan.py` free of authorization, so re-authorization and re-stat
  between scan and read are applied in `scripts/mcp_servers/mdq/indexer.py` (seq 02), not here. The
  re-authorization part of REQ-005 is therefore implemented by seq 02; this document covers matching,
  case behavior, and canonical deduplication only. `tests/mcp_servers/mdq/test_mdq_scan_semantics.py`
  covers `index_scan.py` alone and cannot pin the re-authorization behavior, so that case belongs to
  `scripts/mcp_servers/mdq/indexer.py`'s companion `tests/mcp_servers/mdq/test_mdq_index_internal_failures.py`
  (seq 02), which is where the file-disappearance case is already listed.

## Design decisions
- Matching is performed on the normalized root-relative POSIX path with `fnmatch.fnmatchcase()`, so
  case behavior is declared by the code instead of inherited from `os.path.normcase`.
- Deduplication is by canonical path, which removes a symlinked duplicate that `str(f)` keeps.

## Alternatives considered
- `pathlib.Path.match()`: rejected and recorded in the existing docstring (Lines 28-33) because it
  right-aligns only as many segments as the pattern has, so `.git/**` does not match a deeper path.
  The per-suffix matching loop is kept for the same reason.
- Canonicalizing only for deduplication and matching on the raw path: rejected, because AC-4 requires
  matching on normalized root-relative POSIX paths.

## Implementation
### Target file
`scripts/mcp_servers/mdq/index_scan.py`

### Procedure
Switch the glob match to the case-explicit form and key the deduplication dictionary by canonical
path; state the symlink behavior in the module docstring.

### Method
Two expression-level changes in existing functions; no new function and no new dependency.

### Details
- `_matches_any_glob()` Lines 25-47: replace `fnmatch.fnmatch()` with `fnmatch.fnmatchcase()` at
  Line 45. Keep the per-suffix loop, which is what makes nested exclude patterns work.
- `iter_indexable_files()` Lines 50-67: key `matched` by `f.resolve().as_posix()` instead of
  `str(f)` at Line 66, so a symlinked duplicate collapses to one entry.
- Module docstring Lines 2-13: state that symlinked directories are not traversed by `Path.rglob`
  and that a symlinked file is discovered and rejected later by `authorize_path()`.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_scan_semantics.py` (new)
  - Procedure: add the symlinked-directory and symlinked-file cases, canonical deduplication, nested
    exclude, duplicate include, and case sensitivity.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_scan_semantics.py` — matching is
    deterministic on normalized root-relative POSIX paths and a symlinked duplicate is deduplicated.

## Compatibility considerations
- Case behavior changes only on a platform where `fnmatch.fnmatch()` was case-insensitive; the
  project's POSIX runtime is unaffected, and the scan test pins the behavior.
- Canonical deduplication changes the returned path objects for symlinked entries, which is the
  intended AC-4 behavior; `scripts/mcp_servers/mdq/index_write.py` stores the canonical form
  (`path.resolve().as_posix()`), so the scan and the stored rows now agree.

## Security considerations
- No authorization decision is made here; `authorize_path()` stays in the caller. The contract check
  must keep showing that this module gains no authorization or database dependency.

## Rollback considerations
- N/A: revert the commit — two expression-level changes with no persisted state.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_scan_semantics.py`
- `PYTHONPATH=scripts uv run lint-imports` — 6 contracts, `index_scan` keeps `MdqService` as a
  TYPE_CHECKING-only dependency.
- Full sequence per `rules/toolchain.md`; `uv run python tools/check_module_size.py` (2759 B of
  24576 B used).

## Completion criteria
- Matching, deduplication, and case behavior are deterministic and pinned by tests.
- The symlink-directory behavior is stated in the module and in the documentation.
- The module still holds no database access and no authorization call.

## Out of Scope
- Re-authorization and re-stat between scan and read (`scripts/mcp_servers/mdq/indexer.py`, seq 02).
- Changing symlink behavior; the Plan documents the existing behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the scan-semantics tests (companion) | Completed | 2026-11-28 | 2026-11-28 | tests/mcp_servers/mdq/test_mdq_scan_semantics.py (new): 6 cases - nested exclude at any depth, case-sensitive exclude and include, duplicate include patterns, symlinked file collapses to one canonical entry, symlinked directory not traversed. |
| 2 | Switch to `fnmatch.fnmatchcase()` and canonical deduplication | Completed | 2026-11-28 | 2026-11-28 | fnmatch.fnmatchcase() at the suffix loop; matched keyed by f.resolve().as_posix(). Per-suffix loop kept unchanged. |
| 3 | State the symlink-directory behavior in the module docstring | Completed | 2026-11-28 | 2026-11-28 | Module docstring states rglob does not traverse symlinked directories and that a discovered symlinked file is judged later by authorize_path() in the indexer. |
| 4 | Run the validation sequence (`rules/toolchain.md`) and the contract check | Completed | 2026-11-28 | 2026-11-28 | Gates pass: ruff format/check, mypy (20 files), lint-imports 6 kept 0 broken (index_scan still TYPE_CHECKING-only MdqService), bandit clean, check_module_size OK. Targeted: 6 passed. Whole tests/mcp_servers/mdq/ + test_mdq_audit.py: 517 passed. |

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
- **Requirement ID**: REQ-005 (deterministic scan semantics: normalized matching, canonical dedup,
  stated symlink behavior)
- **Source issue**: `issues/done/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-163030_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-225351
- **Related target files**: `scripts/mcp_servers/mdq/index_scan.py`, `tests/mcp_servers/mdq/test_mdq_scan_semantics.py`
