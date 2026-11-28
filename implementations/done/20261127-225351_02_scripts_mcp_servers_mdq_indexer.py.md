# Implementation Procedure — scripts/mcp_servers/mdq/indexer.py

## Goal

Make the indexing path report what actually happened to each file: return the per-file DTO, tally
from its status, advance `index_state` only after a commit, and count paths and files as separate
units.

## Scope
**Release unit**: per-file-outcome-and-counters

Requirements implemented: REQ-001 (every caller tallies from the DTO status), REQ-002
(`index_state` advances only after a successful commit), REQ-003 (separate path and file counters,
`partial_success` (new), the all-files-failed tool error), REQ-005 (re-authorization and re-stat
between scan and read). Acceptance criteria: AC-1, AC-2, AC-4.

## Assumptions
- The DTO, the closed status and reason-code sets, and the counter keys are defined by procedure
  seq 01 in `scripts/mcp_servers/mdq/mdq_models.py`; this document uses them and does not redefine
  them.
- `RefreshSummary` is defined in this file (Line 42), so its new keys are added here.
- The all-files-failed case raises `MdqServiceError` from the service layer; the audit boundary
  that renders it is owned by the server-boundary plan and is not touched here.
- `index_scan.py` keeps its boundary: discovery only. Re-authorization and re-stat stay in this
  file, which already imports `authorize_path`.

## Design decisions
- `_index_single_file()` returns `FileOutcome` instead of `None`, so the caller no longer treats
  "the call returned" as evidence of success.
- The two swallowed error classes are distinguished by reason code rather than by message text, so
  a count can be reported without a path.
- The commit outcome is the DTO status: `indexed` means the write transaction committed, so
  `index_state` advances only on that status.

## Alternatives considered
- Keeping the swallow and adding a separate flag for the commit outcome: rejected, because it leaves
  two sources of truth for the same file.
- Counting files in force mode only: rejected, because `input_path_count` and `indexed_count` would
  still describe different units in the same response (AC-2).

## Implementation
### Target file
`scripts/mcp_servers/mdq/indexer.py`

### Procedure
Change the per-file function to return the DTO, tally from its status, gate the `index_state` write
on the commit outcome, add the file-level counters to the tally and to `RefreshSummary`, and
re-authorize and re-stat each discovered file before the read.

### Method
One return-contract change plus the callers that consume it. The tally stays a mutable dataclass;
the outcome text is rendered from the counters, not from the fact that no exception was raised.

### Details
- `RefreshSummary` Lines 42-49: add `discovered_file_count` (new), `committed_file_count` (new),
  `skipped_file_count` (new), `failed_file_count` (new).
- `_PathTally` Lines 52-64: add the matching four counters; the existing four keep their
  path-level meaning (UNK-06).
- `_index_single_file()` Lines 75-110: return `FileOutcome`. The size gate Lines 79-87 compares
  `st_size` with `max_file_bytes` and returns `skipped_size_limit`; the `FileNotFoundError` branch
  Line 93 returns `skipped_no_content` or `failed` according to the reason code; the
  `sqlite3.Error` branch Line 106 returns `failed` instead of swallowing.
- `_tally_indexing()` Lines 119-133: tally from the returned status instead of the absence of an
  exception.
- `_index_directory()` Lines 113-116: re-authorize and re-stat each discovered file before the
  read, and count discovered files.
- `_refresh_changed_file()` Lines 304-327: write `index_state` only when the returned status is
  `indexed`; a swallowed write failure no longer advances state.
- `_reindex_forced()` Lines 274-290: report files as the unit in both modes.
- `index_paths()` Lines 179-195 and `refresh_paths()` Lines 399-434: build the metadata with the
  new keys, report `partial_success` (new) for a mixed run, and raise `MdqServiceError` when every
  file fails.

(All line numbers verified against the source at 20261128; the procedure's original references
drifted by at most four lines.)

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_index_internal_failures.py` (new)
  - Procedure: measure the production SQLite write failure, the size limit, file disappearance
    between scan and read, and the no-content outcome through the DTO, and the retry-after-failure
    path.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_index_internal_failures.py` — a
    skipped or failed file never advances `index_state` and is never counted as committed.
- `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`
  - Procedure: move the counter assertions onto the DTO-based counts and add the mixed-success
    directory and retry-after-failure cases; `test_failed_reindex_does_not_record_the_new_mtime`
    stays as the post-success characterization.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` — the counters
    name distinct units and the post-commit rule holds for the internal swallow.

## Compatibility considerations
- `_index_single_file()` changes its return contract; the call sites that unpack it are
  `_tally_indexing()`, `_reindex_forced()`, `_refresh_changed_file()`, and the tests that monkeypatch
  it (`tests/mcp_servers/mdq/test_mdq_service.py` Lines 561 and 578, verified 20261128; Line 578's
  fake also gains the `tally` parameter because `_index_directory()` now takes it).
- `scripts/mcp_servers/mdq/mdq_server.py` reads the counter keys with `.get(..., 0)`, so the added
  counters are additive and that file needs no change.
- The outcome text changes for runs that currently report success; the affected assertions are
  listed in the Plan's predictable fallout check.

## Security considerations
- Re-authorization and re-stat before the read close the gap between the scan decision and the read;
  `authorize_path` is called, not modified.
- The DTO carries a root-relative POSIX path, so no absolute path reaches the audit record.

## Rollback considerations
- Revert this file with the release-unit commit. `index_state` rows written by the new rule are not
  rewritten by a revert; a reverted deployment re-reads the existing state, which is the pre-change
  behavior.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_index_internal_failures.py tests/mcp_servers/mdq/test_mdq_incremental_refresh.py tests/mcp_servers/mdq/test_mdq_service.py`
- Baseline before any change: 416 passed, 1 skipped for `tests/mcp_servers/mdq/` (re-run 20261127).
- Full sequence per `rules/toolchain.md`, including `PYTHONPATH=scripts uv run lint-imports`
  (6 contracts) and `uv run python tools/check_module_size.py` (14835 B of 24576 B used).

## Completion criteria
- No counter reports a skipped or failed file as committed, and no `index_state` row advances without
  a commit.
- A mixed run reports `partial_success` (new) and an all-failed run raises the tool error.
- The directory unit is the same in the incremental and force modes.

## Out of Scope
- The DTO definition and the closed status and reason-code sets (procedure seq 01).
- The glob matching and deduplication semantics (`scripts/mcp_servers/mdq/index_scan.py`, seq 03).
- The audit rendering and the error codes, owned by the server-boundary plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the DTO-based outcome tests before any production change | Completed | 2026-11-28 | 2026-11-28 | Companion tests landed in the same cycle as the production change; characterization fakes updated to the DTO contract (FileOutcome-returning), all-failed cases moved to pytest.raises(MdqServiceError), new mixed-directory and retry-after-failure cases added. |
| 2 | Return `FileOutcome` from `_index_single_file()` and tally from its status | Completed | 2026-11-28 | 2026-11-28 | _index_single_file() returns FileOutcome; re-authorization and re-stat happen inside it (REQ-005), covering both the single-file and the directory path. |
| 3 | Gate the `index_state` write on the commit outcome | Completed | 2026-11-28 | 2026-11-28 | REQ-002, Phase 3 |
| 4 | Add the file-level counters and the `partial_success` (new) and all-failed outcomes | Completed | 2026-11-28 | 2026-11-28 | Companion byte-unit renames from the seq 06/12/13 scope landed early in this cycle, forced by the seq 01 field rename (service construction broke otherwise): mdq_service.py:75, mdq_security_validation.py:48, config/mdq_mcp_server.toml:29, tests/mcp_servers/mdq/_startup.py:29, and key renames in test_mdq_config.py/test_mdq_service.py. They land in the same release-unit commit. |
| 5 | Re-authorize and re-stat each discovered file before the read | Completed | 2026-11-28 | 2026-11-28 | REQ-005, Phase 4 |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-28 | 2026-11-28 | Gates pass: ruff format/check, mypy (20 files), lint-imports 6 kept, bandit 0 findings, check_module_size OK (indexer.py 24127 B of 24576 B; docstrings compressed after a first draft exceeded the limit). Targeted: internal_failures + incremental_refresh + service = 122 passed; whole tests/mcp_servers/mdq/ + test_mdq_audit.py = 511 passed. Full suite + diff-cover run once at unit end. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | Red state inherited from seq 01: `test_mdq_config.py` 5 failures plus import-time `ValidationError` in `mdq_service.py` because `MdqConfig.max_file_chars` no longer exists | Yes — the companion `max_file_bytes` renames landed with this cycle (see Step 4 Notes) | 20261128 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (tally from the DTO status), REQ-002 (`index_state` after commit),
  REQ-003 (counters that name their unit), REQ-005 (re-authorization and re-stat)
- **Source issue**: `issues/done/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-163030_mdqmcp003_mdq-file-processing-outcomes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-225351
- **Related target files**: `scripts/mcp_servers/mdq/indexer.py`, `tests/mcp_servers/mdq/test_mdq_index_internal_failures.py`, `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`
