# Remove the mdq.sqlite legacy chunks rebuild

## Priority
Low

## Summary
Remove the startup branch of the MDQ service that detects the legacy `chunks` table shape and drops and recreates it, now that the supported baseline is the current `chunks` shape.

## Background
The database design document (section 8e, Supported Upgrade Baseline) states that the minimum supported source schema of `mdq.sqlite` is the current `chunks` shape, keyed by `chunk_id`. The owner decided this on 2026-10-21; the only deployment is the single host using `/opt/llm`, and a read-only inspection that day found `chunks` starting with `chunk_id` (the current shape, not the legacy `id`). `_migrate_legacy_chunks_schema()` in `scripts/mcp_servers/mdq/db_schema.py` runs from `create_production_tables()` on every MDQ service start, detects the legacy shape with `PRAGMA table_info(chunks)`, and unconditionally drops the `chunks` and `chunks_fts` tables and their triggers; the data is lost and recovered only by re-indexing the Markdown files (section 8d). MDQ is a derived store, not a platform database. (Confirmed by code and by read-only inspection)

## Problem
A destructive branch runs on every start for a legacy shape that no supported database has. If a wrongly detected shape ever matched it, it would silently discard an index. It also needs its own test and its own documentation.

## Reason for Change
Removing a destructive startup path that serves no supported database lowers risk and lets the create-only table setup stand alone. The earlier work item to make this rebuild observable and document its recovery procedure becomes unnecessary once the rebuild is gone.

## Implementation Intent
Delete the legacy detection and rebuild, keeping the creation of the current tables, triggers, and index state unchanged. A store older than the baseline is recreated by re-indexing, which the design document already describes as the recovery path for this derived store.

## Target Files or Areas
- `scripts/mcp_servers/mdq/db_schema.py` (`_migrate_legacy_chunks_schema()` and its call in `create_production_tables()`, including the docstring)
- `scripts/mcp_servers/mdq/mdq_service.py` (the docstring that mentions migrating from a legacy schema)
- `tests/mcp_servers/mdq/test_db_schema.py` (the legacy detection and rebuild test)
- `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (sections 8d, 8e), `docs/90_deployment/deployment_01_deployment.md` (the sentence in section 3.0 about recreating a legacy chunk schema)

## Required Changes
- Remove `_migrate_legacy_chunks_schema()` and its call; update the docstrings that mention it.
- Remove or rewrite the legacy-shape test; keep tests that the current tables, triggers, and index state are created and that a database at the current shape starts unchanged.
- Update the documentation so section 8d and the deployment guide no longer describe automatic legacy detection and the data-loss warning; do not leave a history of the removal, and keep the re-indexing recovery statement.

## Constraints
- The current table definitions, full-text triggers, and index state must be created exactly as before.
- The MDQ health check semantics (a missing file or an unhealthy schema is degraded) must not change.
- Import boundaries between MDQ and RAG must hold (the MDQ/RAG boundary test must still pass).

## Acceptance Criteria
- `rg "_migrate_legacy_chunks_schema|old chunks schema" scripts tests docs` returns no match.
- Starting the MDQ service on an empty path and on a database at the current shape both succeed and leave the schema unchanged.
- The MDQ tests, `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`, `ruff`, `mypy --no-namespace-packages`, `lint-imports`, the full suite, and the documentation checkers pass.

## Testing Expectations
- Run `tests/mcp_servers/mdq/test_db_schema.py` and the MDQ boundary test, then the full suite once.
- Run `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, and the documentation checkers for the touched docs.
- Manual: read the first column of `chunks` in the deployed `mdq.sqlite` read-only and confirm it is `chunk_id` before deploying.

## Documentation Impact
Yes. Remove the description of automatic legacy detection, the unconditional drop, and the data-loss warning, and the deployment guide's mention of recreating a legacy chunk schema; keep the statements that MDQ is a derived store recovered by re-indexing.

## Out of Scope
- The workflow and EventBus migrations and the legacy offset import (separate issues).
- Changing the MDQ schema, the index content, or the re-indexing procedure.

## Dependencies
- Depends on the baseline recorded in the database design document (section 8e); that change is already merged.
- Shares the database design document and the deployment guide with the other removal issues; apply the edits one after another.
- Related: `issues/done/20261020-123146_compat006_make-the-mdq-legacy-schema-rebuild-observable-and-document-its-recovery-procedure.md` was archived without a code change; this removal supersedes it.
- Sibling-issue check: no open issue under `issues/` touches these files.

## Unresolved Questions
- N/A: none (the baseline and the single-deployment scope are owner decisions recorded in the design document). Re-run the read-only shape check on the deployed host immediately before the removal lands.

## AI Implementation Instruction
- Change only the files under Target Files or Areas; keep the diff minimal and do not refactor unrelated MDQ code.
- Do not add a replacement detection, a fallback, or a migration for older stores.
- Stop and report if a caller outside the listed files uses the removed function.
- Write documentation in English and follow the repository's documentation checkers.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261020-233138_plan.md`
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-102212
- **Related target files**: `scripts/mcp_servers/mdq/db_schema.py`, `scripts/mcp_servers/mdq/mdq_service.py`, `tests/mcp_servers/mdq/test_db_schema.py`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `docs/90_deployment/deployment_01_deployment.md`
