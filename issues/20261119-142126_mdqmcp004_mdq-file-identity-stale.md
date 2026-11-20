# Redesign MDQ persisted file identity, stale detection, and schema fields

## Priority
High

## Summary
Replace path and mtime derived content hashes and database-only stale checks with content-based fingerprints, current-filesystem comparison, explicit truncation metadata, and defined inconsistency states.

## Background
Source: consolidated MDQ MCP backlog (`memo-issue.md`, Issue 4).

Evidence (`Explicit in code`, by reading `index_write.py:66-81`): the document `content_hash` is `sha256(str(path) + str(mtime_ns))`, not a content hash; chunk hashes cover `section["content"]` (line 89). `health_check.py:44-48` and `mdq_service.py` count stale documents through `STALE_SQL_CONDITION` on database columns only. Test claims (artificial timestamps, orphans treated as normal) are `Needs confirmation`. Related archived work: `issues/done/20261021-102212_rmmdqmig_remove-the-mdq.sqlite-legacy-chunks-rebuild.md`.

## Problem
Same-mtime content changes, timestamp rollback, changes after a stored truncation boundary, deleted files, and orphaned chunks cannot be reliably detected, and the name `content_hash` is misleading.

## Reason for Change
Data integrity; the schema change forces database recreation, so it must precede the transaction and schema-identity work.

## Implementation Intent
The database records what source content was indexed, what truncated content was stored, and what filesystem state was observed; refresh and outline compare against the current filesystem and use one shared set of stale states.

## Target Files or Areas
- `scripts/mcp_servers/mdq/db_schema.py`, `index_write.py`, `mdq_models.py`, `mdq_service.py`, `health_check.py`
- `tests/mcp_servers/mdq/test_db_schema.py`, `test_mdq_stale_detection.py`, `test_mdq_health_stale.py`, `test_mdq_outline_stale_helper.py`, `test_mdq_schema_migration.py`
- `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (runbook alignment)

## Required Changes
- Add `source_content_hash` from source bytes; separate the path/mtime fingerprint; store section hash and stored chunk hash separately; store truncation flag, original and stored character counts, and indexed mtime and size.
- Compare current mtime, size, and source hash on refresh; inspect the filesystem for outline freshness; define `fresh`, `stale`, `missing`, `unknown`, and `inconsistent`; treat chunks without a document row as inconsistent; redesign the database-only stale SQL.
- Define the single derived-database recreation runbook (handling of the database, `-wal`, and `-shm` files, re-index verification, failure rollback, and alignment of the ADR matrices, decision details, restart conditions, and AAL references) and recreate the database according to it; every later MDQ schema change uses this runbook.

## Constraints
- DDL changes force recreation (ADR-008 treats the MDQ database as derived; no migration). An ADR change needs a maintainer approval record (governance_01, governance_05); do not write or simulate it.
- Health and outline use the same state definitions.

## Acceptance Criteria
- [ ] Same-mtime content changes and timestamp rollback are detected.
- [ ] Tail changes after a stored truncation boundary are detected.
- [ ] Deleted files and orphaned records have explicit states.
- [ ] Production-writer tests verify real hash semantics; health and outline share the stale-state definitions.

## Testing Expectations
- Real filesystem modifications; same mtime with different content; mtime rollback and deletion; truncation-tail changes; orphan document and chunk relationships.
- Schema recreation and production-writer contract tests.
- Run ruff, mypy, schema fingerprint checks, and the full test suite.

## Documentation Impact
Yes. Define every persisted fingerprint and stale state; remove statements implying path/mtime fingerprints are content hashes.

## Out of Scope
- FTS5 DDL identity and readiness (`issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`); transactions (`issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`).

## Dependencies
- Depends on `issues/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`. Blocks `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md` and `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`.
- Health state codes extend the non-sensitive readiness reporting of `issues/20261119-142123_mdqmcp001_mdq-server-boundary.md`; the truncation fields defined here are reused by `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`.

## Unresolved Questions
- `不明`: whether storing the full source hash requires reading files that exceed the size limit.
- `不明`: operator timing for the database recreation.

## AI Implementation Instruction
Write the same-mtime and rollback tests with real files first. Do not add migration code; use recreation. Stop and report if the stale-state set conflicts with existing health consumers.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-142126
- **Related target files**: `scripts/mcp_servers/mdq/db_schema.py`, `scripts/mcp_servers/mdq/index_write.py`, `scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/mdq_service.py`, `scripts/mcp_servers/mdq/health_check.py`
