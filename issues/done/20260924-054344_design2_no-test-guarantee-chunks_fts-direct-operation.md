# No test guarantees application code never directly operates chunks_fts

## Priority
Medium

## Summary
Add enforcement that application code respects ADR-009's boundary between direct `chunks_fts` operations and the FTS wrapper interface.

## Background
ADR-009 establishes that application code must never directly operate on the `chunks_fts` table — all FTS operations must go through the FTS wrapper. This invariant protects the abstraction boundary between the RAG ingestion pipeline and the full-text search layer. ADR-009's Known Deviations section cites TEST-DESIGN3-02 (`test_chunks_fts_is_trigger_synced` in `tests/agent/services/test_rag_index_integrity.py`) as evidence that chunks_fts is trigger-synced from chunks, but no test verifies that application code respects the boundary.

## Problem
No test or lint rule enforces the invariant established by ADR-009. Without enforcement, new code can inadvertently operate on `chunks_fts` directly, breaking the abstraction boundary.

## Reason for Change
The current state relies entirely on developer discipline. Zero direct-write bypasses of ADR-009's rebuild-path restriction have been found so far, but the absence of violations does not prove the invariant holds — it proves nothing has been tested. As the codebase grows, the risk of accidental bypass increases.

## Implementation Intent
Add a static analysis guard that scans for direct `chunks_fts` references outside the sanctioned write paths. Two approaches are viable:
1. A lint rule (e.g., via `pylint` custom checker or `ruff` plugin) that flags any SQL string containing `chunks_fts` outside the sanctioned write paths listed below.
2. An integration test that verifies all FTS operations go through the wrapper by mocking the database connection and asserting no direct writes occur.

Approach 1 is preferred because it catches violations at development time rather than runtime.

**Sanctioned write paths** (must NOT be flagged):
- `scripts/agent/services/rag_maintenance_service.py::rebuild_fts()` — sanctioned `/session rag-rebuild-fts` command path
- `scripts/db/schema_sql.py` — schema initialization SQL (executed once during setup, not runtime)

**Out-of-scope read paths** (not write operations, already documented in DESIGN-2 Observed Implementation):
- `scripts/rag/repository.py` — read-only SELECT/bm25 queries against `chunks_fts`
- `scripts/mcp_servers/mdq/` — targets a separate database (`/opt/llm/db/mdq.sqlite`)

## Target Files or Areas
- `scripts/rag/` — source directory where FTS wrapper lives
- `scripts/agent/services/rag_maintenance_service.py` — sanctioned write path
- `scripts/db/schema_sql.py` — schema initialization SQL
- `tests/` — test directory for new enforcement test
- `.pylintrc` or equivalent lint configuration
- `tools/` — potential location for a new lint script

## Required Changes
- Define a whitelist of sanctioned `chunks_fts` write paths (above)
- Add a lint rule or script that detects direct `chunks_fts` INSERT/UPDATE SQL references outside the whitelist
- Add a test (if choosing approach 2) that mocks the database connection and asserts no unsanctioned direct writes to `chunks_fts`
- Document the enforcement mechanism in ADR-009's "Known Deviations" section
- Update the Known Issue entry DESIGN-2 status to reflect the new enforcement

## Constraints
- The enforcement must not flag the sanctioned write paths listed above
- The enforcement must not flag MDQ's `chunks_fts` access (separate database, out of ADR-009's scope)
- The enforcement must not add runtime overhead to production code paths
- Any lint rule must integrate with the existing CI pipeline without requiring additional dependencies

## Acceptance Criteria
- A whitelist of sanctioned `chunks_fts` write paths is defined and documented
- A lint rule or script exists that detects direct `chunks_fts` INSERT/UPDATE references outside the whitelist
- Sanctioned write paths pass the enforcement check without false positives
- A new test demonstrating an unsanctioned `chunks_fts` violation fails the enforcement check
- The enforcement runs in CI

## Testing Expectations
- Unit test: verify the lint rule/script correctly identifies both sanctioned and unsanctioned `chunks_fts` references
- Integration test: verify the enforcement runs in CI without false positives on sanctioned paths
- Regression test: confirm existing tests pass after adding the enforcement

## Documentation Impact
- ADR-009's "Known Deviations" section must document the new enforcement mechanism and the whitelist of sanctioned paths
- The Known Issue entry DESIGN-2 must be updated to reflect the resolution status
- If a new lint script is added under `tools/`, it needs a description file per `routing.md` Tools → "When to run which tool"

## Out of Scope
- Refactoring the FTS wrapper itself
- Adding new FTS functionality
- Changing the `chunks_fts` schema
- Modifying MDQ's separate database access patterns
- Adding enforcement for read-only `SELECT` statements against `chunks_fts`

## Dependencies
- ADR-009 (source of the invariant)
- DESIGN-1 (resolved; shared-corpus note added to docs/03_rag_01_system_overview.md)

## Unresolved Questions
- Which lint framework to use (pylint vs ruff)? Depends on the project's existing lint configuration.
- Should the enforcement be a pre-commit hook or CI-only? Pre-commit provides faster feedback but adds local dependency.
- Are there any other sanctioned `chunks_fts` write paths not yet identified? Requires review of all `INSERT INTO chunks_fts` occurrences across the repository.

## AI Implementation Instruction
- Do not modify any production code paths that currently reference `chunks_fts` unless they need to be added to the whitelist
- Preserve the existing FTS wrapper API contract
- If adding a lint rule, ensure it integrates with the existing CI pipeline without adding new dependencies
- Report open questions about lint framework choice and unidentified sanctioned paths before proceeding

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260924-054344
- **Related target files**: scripts/rag/, scripts/agent/services/rag_maintenance_service.py, scripts/db/schema_sql.py, tests/, .pylintrc or equivalent lint configuration, tools/
