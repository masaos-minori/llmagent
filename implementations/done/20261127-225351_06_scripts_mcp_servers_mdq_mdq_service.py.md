# Implementation Procedure — scripts/mcp_servers/mdq/mdq_service.py

## Goal

Honor an explicit zero context, carry the byte-unit attribute name, and render the outcome text from
the DTO counters so the reported text matches what actually happened.

## Scope
**Release unit**: per-file-outcome-and-counters (the byte-unit attribute is the part that belongs to
release unit `byte-limit-key-rename`; the zero-context change belongs to
`grep-context-and-line-numbers`)

Requirements implemented: REQ-003 (outcome text from the DTO counters, `partial_success` (new)),
REQ-004 (byte-unit attribute), REQ-006 (only `None` selects the configured default).
Acceptance criteria: AC-2, AC-3, AC-5.

## Assumptions
- The DTO, the counter keys, and the byte field are defined by procedure seq 01; this document reads
  them and does not define them.
- The all-files-failed tool error is raised by the indexing path (`scripts/mcp_servers/mdq/indexer.py`,
  seq 02) as `MdqServiceError` and rendered by the audit boundary owned by the server-boundary plan;
  this document does not modify `scripts/mcp_servers/mdq/mdq_server.py`.
- The context defaults come from `MdqConfig` (default 3, seq 01), so an explicit zero is
  distinguishable from the default.

## Design decisions
- The outcome text is derived from the counters, not from the absence of a failure, so a mixed run
  reports `partial_success` (new) rather than a success line.
- `or` is replaced by an explicit `None` test, which is the smallest change that separates "not
  provided" from "provided as zero".

## Alternatives considered
- Keeping `or` and documenting that zero means "use the default": rejected, because AC-5 requires an
  explicit zero to be honored.
- Rendering the outcome text in the audit boundary: rejected, because the audit surface is owned by
  the server-boundary plan.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_service.py`

### Procedure
Change the context resolution, rename the size-limit attribute, and extend the summary lines with the
file-level counters.

### Method
Three localized changes in existing methods; no new function and no new import.

### Details
- Lines 404-405: `req.context_before or self.context_before` and the `context_after` equivalent
  become an explicit `None` test, so an explicit zero is passed to `grep_docs()`.
- Line 73: `self.max_file_chars = cfg.max_file_chars` becomes `self.max_file_bytes` (new), matching
  the renamed field in procedure seq 01.
- `_format_refresh_summary()` Lines 319-326: add the file-level counter lines and select
  `partial_success` (new) as the header when the run is mixed; the existing lines stay for runs with
  no file-level work.
- The grep summary reports the returned context, so the formatter in
  `scripts/mcp_servers/mdq/db_grep.py` (seq 05) is the renderer; this file only supplies the context
  values.

## Compatibility considerations
- `self.max_file_chars` is read by `scripts/mcp_servers/mdq/indexer.py` Line 85; the rename lands in
  the same commit as procedure seq 02.
- Seven `text == "Indexing complete"` assertions in `tests/mcp_servers/mdq/test_mdq_service.py`
  change: two skip-only runs, two all-failed runs, three runs with committed work. They are
  rewritten by procedure seq 12.
- `tests/mcp_servers/mdq/test_oversized_file_is_skipped_with_warning` (Line 118) asserts the message
  text `exceeds max_file_chars`; the message and the assertion move to the byte unit together.

## Security considerations
- No authentication or path authorization behavior. The byte limit remains a hard bound enforced
  before the read.

## Rollback considerations
- N/A: revert the commit — three localized changes with no persisted state.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_service.py` — explicit zero context, the byte
  attribute, the outcome text, and the ASCII, Japanese, emoji, and BOM size-limit cases.
- Baseline before any change: 159 passed for the five-file subset (re-run 20261127).
- Full sequence per `rules/toolchain.md`, including `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- An explicit zero context reaches the grep layer.
- The outcome text reflects the counters, including `partial_success` (new) for a mixed run.
- The size-limit attribute names its unit and the byte-versus-character cases pass.

## Out of Scope
- The DTO and the counter key definitions (procedure seq 01).
- The counter production and the all-files-failed raise (procedure seq 02).
- The audit rendering and the error codes, owned by the server-boundary plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace `or` with an explicit `None` test for both context values | Completed | 2026-11-28 | 2026-11-28 | Lines 422-423 (procedure said 404-405): both context values now read `self.X if req.X is None else req.X`. max_chars_per_match keeps its `or` because REQ-006 names only the context pair. |
| 2 | Rename the size-limit attribute to the byte unit | Completed | 2026-11-28 | 2026-11-28 | Line 75 (procedure said 73): self.max_file_bytes landed early with the seq 02 cycle, forced by the seq 01 field rename; recorded in seq 02 Step 4 Notes. |
| 3 | Render the outcome text from the DTO counters, including `partial_success` (new) | Completed | 2026-11-28 | 2026-11-28 | 3b decision (user-approved 20261128): RefreshSummary gains unchanged_file_count so a refresh whose files were all unchanged is not reported as partial. The header is mdq_models.outcome_text(), which now treats unchanged files as completed work: full success means committed == discovered - unchanged, skipped_files == unchanged, skipped_count == unchanged, and no failure at either level. Added the four file counter lines plus "Files unchanged", and "Refresh complete in Xs" became "Indexing complete" + "Elapsed: Xs"; the pinned test tests/mcp_servers/mdq/test_mdq_service.py::test_refresh_index_delegates_to_indexer was rewritten with two new cases (unchanged-only, size-skipped). |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-28 | 2026-11-28 | outcome_text() and the two text constants moved from indexer.py to mdq_models.py: indexer.py reached 25297 B against the 24576 B gate after the counter additions, and the outcome vocabulary belongs with the outcome DTOs. Contracts stay 6 kept 0 broken; indexer.py now 24088 B. Gates: ruff format/check, mypy (20 files), bandit clean, check_module_size OK. Targeted: service + incremental_refresh + internal_failures = 127 passed; whole tests/mcp_servers/mdq/ + test_mdq_audit.py = 522 passed. |

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
- **Requirement ID**: REQ-003 (outcome text from the DTO counters), REQ-004 (byte-unit attribute),
  REQ-006 (explicit zero context honored)
- **Source issue**: `issues/done/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-163030_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-225351
- **Related target files**: `scripts/mcp_servers/mdq/mdq_service.py`
