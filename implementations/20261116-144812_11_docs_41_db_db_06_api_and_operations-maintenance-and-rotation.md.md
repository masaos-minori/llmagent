## Goal

Document the six new artifact-retention keys, the four-sweep `purge_archive_artifacts()` entry point, and its weekly cadence line in `docs/41_db/db_06`, extending the existing corrupt-retention paragraph (REQ-007, AC-8).

## Scope
**Release unit**: retention-sweeps-and-drill-lifecycle

- In scope: one new paragraph (plus a cadence line) in `db_06`.
- Out of scope: the code behavior itself (row 1); the drill section (row 12, `db_07`).

## Assumptions
- Anchors re-verified 2026-11-16. The corrupt-archive retention paragraph is `db_06:42` (the pattern to mirror); the rotation archive-dir/format text is `:40`. The cadence table lives in `maintenance.py:11-17`.
- `ArtifactRetentionConfig` and `purge_archive_artifacts` are created by the row-01 procedure; `resolve_unique_path` by row 02 — this document references them, it does not introduce them.

## Design decisions
- Mirror the wording and key contract of `:42` (typed integers, fail-closed, `0` disables a rule, validator-known) so the six new keys read like the landed corrupt-retention keys.

## Alternatives considered
- N/A: documentation-only row.

## Implementation
### Target file
`docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`

### Procedure
1. After the corrupt-retention paragraph at `:42`, add a retention paragraph documenting ArtifactRetentionConfig and the purge_archive_artifacts() entry point: the six keys (sqlite_archive_max_files, sqlite_archive_max_age_days, sqlite_drill_artifact_max_files, sqlite_drill_artifact_max_age_days, sqlite_quarantine_max_files, sqlite_quarantine_max_age_days) with defaults 14/30, 14/30, 10/90; `0` disables the matching rule; negative/bool raise; the four sweep classes (archives, drill JSON, quarantine directories, 1-day stale work files); most-recent-per-source-DB protection; the `_corrupt_` exclusion (owned by `purge_corrupt_archives`); and the weekly purge_archive_artifacts cadence line matching `maintenance.py:11-17`.

### Method
- New paragraph only; existing section headings and neighboring paragraphs stay in place.

### Details
- Reference-table refresh for the six keys is validated by `tools/generate_reference_table.py --check`.

## Compatibility considerations
- Additive prose; no existing documented contract changes. `purge_corrupt_archives`' documented behavior stays as written.

## Security considerations
- N/A: documentation.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain db`; `uv run python tools/generate_reference_table.py --check`.

## Completion criteria
- The six keys, defaults, `0`-disables semantics, the four sweep classes, and the cadence line are documented consistently with `maintenance.py` and `agent.toml`; the doc checkers pass.

## Out of Scope
- Drill lifecycle wording (row 12).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the retention-keys paragraph and cadence line | Pending | — | — | |
| 2 | Run the documentation checkers (`check_docs_consistency.py --domain db`, `generate_reference_table.py --check`) | Pending | — | — | |

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
- **Requirement ID**: REQ-007 (document retention keys and sweeps)
- **Source issue**: issues/20261114-092857_dbreview008_artifact-retention-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-054021_dbreview008_artifact-retention-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-144812
- **Related target files**: `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`
