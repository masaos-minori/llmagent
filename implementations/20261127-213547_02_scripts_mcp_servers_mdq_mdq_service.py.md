## Goal

Scope MDQ stats counts to the currently authorized roots, drop the raw `index_state` metadata dict, refuse stats when no roots are authorized, and consume the shared validated startup-configuration result instead of swallowing configuration failures (REQ-002 authorized stats, REQ-007 single configuration source).

## Scope
**Release unit**: boundary-characterization-tests (Plan steps 5 and 6 cite this row; the unit covers Phases 1, 3, 4, 5, 6)

## Assumptions
- Companion test rows (SKILL.md conditions 1-4 hold; each is named only by this row and needs no design decision of its own): `tests/mcp_servers/mdq/test_mdq_service.py`, `tests/mcp_servers/mdq/test_mdq_schema_migration.py`, `tests/mcp_servers/mdq/test_mdq_read_authorization.py`.
- `scripts/db/helper.py` is not modified; `SQLiteHelper` is consumed as it stands with a caller-supplied `db_path`.
- The configuration result consumed here is produced by `scripts/mcp_servers/mdq/startup_config.py` (seq 09); this document does not define the loader.
- Cross-plan overlap on `docs/22_mcp/mcp_04_04_mdq.md` is a documentation-sequencing dependency with eight other Frozen plans, not a conflict: the authorized-stats statement belongs to this plan's REQ-002 section.
- `grimp` reports no production importer of `mcp_servers.mdq.mdq_service`, so the stats shape change is consumed only by the tests named in the plan.

## Design decisions
- Counts are filtered by the authorized roots through `documents.source_path`, so a shrunk allowlist immediately removes prior-root information from the response.
- `stats()` refuses when no roots are authorized, rather than reporting zero counts, so "no access" and "nothing indexed" stay distinguishable.
- `__init__()` stops catching `(FileNotFoundError, KeyError, TypeError)`; configuration failure propagates as the shared startup error.

## Alternatives considered
- Keep the `index_state` dict but filter its keys — rejected: the requirement removes the raw metadata dict from the public response.
- Return zero counts for the no-roots case — rejected: AC-2 requires the refusal to be observable, and the existing search path already distinguishes deny-all from an unfiltered scan.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_service.py`

### Procedure
- In `stats()` (line 329), replace the `SELECT key, value FROM index_state` metadata dict with root-scoped counts and remove the metadata dict from the response.
- Refuse the call when `self._allowed_dirs` is empty, using the domain code from `scripts/mcp_servers/mdq/mdq_error_codes.py` (seq 08).
- In `__init__()` (lines 57-68), read the validated startup-configuration result instead of `ConfigLoader().load("mdq_mcp_server.toml")` with a fallback, and stop supplying the literal default database path.
- Keep `grep_docs()` gating on `enable_grep` at execution, but the availability decision now comes from the server boundary (seq 01); the service gate stays as the last check.

### Method
- Root filtering uses the canonical stored `source_path` values (`path.resolve().as_posix()` at index time), so the SQL predicate compares canonical values.
- The refusal is raised before any query runs, so no database-wide count is computed for an unauthorized caller.

### Details
- `stats()` currently reports database-wide `fts_count` and stale count; both must be computed within the authorized roots or removed from the response.
- The response keeps the existing field names for counts that remain, so the only shape change is the removed metadata dict.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_service.py`
  - Procedure: update `test_stats_returns_counts_after_indexing`, `test_stats_includes_fts_count`, and `test_stats_includes_stale_count` for root-scoped counts and the removed metadata dict.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_service.py`
- `tests/mcp_servers/mdq/test_mdq_schema_migration.py`
  - Procedure: update `test_chunk_count_in_stats` and `test_document_count_in_stats` to the authorized-root scope; `test_index_metadata_from_index_state` is replaced by the removed-dict expectation.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_schema_migration.py`
- `tests/mcp_servers/mdq/test_mdq_read_authorization.py`
  - Procedure: add the stats-refusal test for the no-authorized-roots case and the shrink-the-allowlist case; `test_deny_all_returns_no_matches_not_unfiltered_scan` stays unchanged.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_read_authorization.py`

## Compatibility considerations
- The stats response shape is a public tool response; the plan's consumer scan found no production consumer of the removed metadata dict.
- Removing the configuration fallback changes startup behavior for a deployed configuration that relies on defaults; seq 11 adds the currently-implicit keys with the same values, so production behavior is unchanged.

## Security considerations
- Counts scoped to authorized roots are the security fix: today a caller with a narrow allowlist can see database-wide counts (AC-2).
- No raw path is added to the stats response.

## Rollback considerations
- Revert the commit; the Phase 1 characterization tests fail again, which is the expected pre-change state.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_service.py tests/mcp_servers/mdq/test_mdq_schema_migration.py tests/mcp_servers/mdq/test_mdq_read_authorization.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- Counts describe only the currently authorized roots.
- The raw `index_state` metadata dict is absent from the response.
- Stats is refused when no roots are authorized, and shrinking the allowlist immediately removes prior-root information.
- A missing production configuration raises instead of falling back to defaults.

## Out of Scope
- The configuration loader itself (seq 09) and the strict type primitives (seq 06).
- The search query boundary, which is plan `mdqmcp002` and consumes the codes defined by seq 08.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Three companion test files are covered by this document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Documentation is a separate row (seq 27) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-002 (authorized stats), REQ-007 (single validated configuration source)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `scripts/mcp_servers/mdq/mdq_service.py`, `tests/mcp_servers/mdq/test_mdq_service.py`, `tests/mcp_servers/mdq/test_mdq_schema_migration.py`, `tests/mcp_servers/mdq/test_mdq_read_authorization.py`
