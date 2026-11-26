## Goal
- Add symlink-exclusion and traversal-limit tests for the read traversals with the structured truncation reason (REQ-002, REQ-003, AC-2).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: new test cases in `tests/mcp_servers/file/test_read_service.py` covering the traversals in `read_business.py` (seq 07) and `read_static_helpers.py` (seq 08).
- Out of scope: the implementation changes themselves (seq 07, 08).

## Assumptions
- Verified in Step 3a: the existing file covers path-authorization symlink cases for `_resolve_safe` (lines 67-100) but has no traversal-enumeration symlink cases and no limit cases.
- This row has its own document because it is cited by two other rows (seq 07, 08), so it fails the companion single-citation condition.

## Design decisions
- Test matrix per the Plan: symlink exclusion (external file symlink, external directory symlink, chained symlink, loop, broken link) and limits (large flat directory for node limit, many small files for scanned-file limit, cumulative-byte limit, deadline) each asserting the structured truncation reason.
- Deadline tests use a fixed small `traversal_deadline_sec` with a pre-created tree rather than time-based flaky sleeps.

## Alternatives considered
- N/A: test-coverage row with no design decision of its own.

## Implementation
### Target file
`tests/mcp_servers/file/test_read_service.py`

### Procedure
1. Add traversal symlink cases: entries outside the allowed root via file and directory symlinks, chained symlinks, self-referential loops, broken links — assert they are excluded and the traversal completes.
2. Add limit cases: node limit via a large flat directory, scanned-file limit via many small files, cumulative-byte limit, deadline — assert each stop reports its structured reason.

### Method
- Use `tmp_path` fixtures and `FileReadConfig.from_dict()` with lowered limits to keep fixtures small and deterministic.

### Details
- Existing `_resolve_safe` symlink tests stay; the new cases target enumeration behavior, not authorization.

## Compatibility considerations
- N/A: tests only.

## Security considerations
- N/A: the tests verify the symlink-exclusion security behavior.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/file/test_read_service.py -v`; full `rules/toolchain.md` sequence.

## Completion criteria
- All Plan-listed symlink and limit cases exist and pass with the structured reason asserted (AC-2).

## Out of Scope
- Implementation changes (seq 07, 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-183821 | 20261126-183821 | TestTraversalSymlinkExclusion added: external file symlink, external directory symlink, chained symlink, self-referential loop, broken link, grep symlink skip, tree symlink skip — all assert exclusion and completion. Files: tests/mcp_servers/file/test_read_service.py |
| 2 | Add or update tests per Validation plan | Completed | 20261126-183821 | 20261126-183821 | TestTraversalLimits added: node limit (count_tree_nodes == max), scanned-file limit, cumulative-byte limit, deadline for both search and grep; deadline uses traversal_deadline_sec=0.0 with a pre-created tree, no sleeps. Helper _limited_service builds the service via FileReadConfig.from_dict with lowered limits. Targeted run 113 passed. Files: tests/mcp_servers/file/test_read_service.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-201535 | 20261126-201535 | ruff/format/mock-patch-targets/reference-table pass; full-suite run deferred to end of plan batch; Step 5/6: N/A: no docs/00_index.md task-scope mapping for tests/mcp_servers/file/test_read_service.py End-of-batch full-suite run passed (15774 passed, 5 skipped); diff-cover 100% on changed source lines — the added TestTraversalStatRace cases cover the OSError branches in search_files and _collect_grep_matches that the first run left uncovered (265-266, 313-314); targeted run 115 passed; gates pass. Intermittent flaky failures in 3 unrelated tests under -n logical, all pass serially. |

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
- **Requirement ID**: `REQ-002` (symlink exclusion), `REQ-003` (traversal limits with structured truncation reason)
- **Source issue**: issues/20261119-140516_mcpai009_file-mcp-hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-065258_mcpai009_file-mcp-hardening.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-171048
- **Related target files**: `tests/mcp_servers/file/test_read_service.py`