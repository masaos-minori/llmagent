# Establish canonical MDQ FTS5 schema identity, readiness, and database recreation operations

## Priority
High

## Summary
Validate the real FTS5 virtual-table and trigger definitions, publish a canonical MDQ schema identity, align readiness with functional search capability, and define one database recreation runbook.

## Background
Source: consolidated MDQ MCP backlog (`memo-issue.md`, Issue 6).

Evidence (`Explicit in code`): `scripts/mcp_servers/mdq/db_schema.py:59-87` defines `chunks_fts` as an FTS5 virtual table and the sync triggers `chunks_ai`, `chunks_ad`, `chunks_au`. The claims that readiness passes with a normal table or no-op triggers, that the shared fingerprint checks virtual tables by name, and that ADR-008 gives conflicting recovery instructions are `Needs confirmation`. The ADR is at `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (the backlog's `docs/adr/` path does not exist); `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` and `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` exist. Related archived work: `issues/done/20261020-123146_compat006_make-the-mdq-legacy-schema-rebuild-observable-and-document-its-recovery-procedure.md`, `issues/done/20261109-112715_adrrev005_schema-fingerprint-unify.md`.

## Problem
Readiness may not prove canonical columns, tokenizer, options, or trigger synchronization; schema identity is missing from execution snapshots; recovery wording for a mismatched database is inconsistent.

## Reason for Change
A search service can report ready while FTS is broken or desynchronized; an operator has no single recovery procedure.

## Implementation Intent
Ready only when the expected FTS5 definition exists and insert, update, and delete synchronization works; schema drift changes a stable identity published safely and included in execution snapshots; one documented stop, archive or recreate, re-index, verify, restart sequence.

## Target Files or Areas
- `scripts/mcp_servers/mdq/db_schema.py`, `health_check.py`, `mdq_security_validation.py`
- `scripts/shared/schema_fingerprint.py`, `scripts/shared/execution_snapshot.py`
- `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
- New tests `test_mdq_fts_schema.py`, `test_mdq_fts_trigger_sync.py`, `test_mdq_schema_identity.py` (absent)

## Required Changes
- Verify `chunks_fts` is an FTS5 virtual table; normalize and compare actual and canonical DDL including columns, tokenizer, prefix, content, detail, options, and trigger SQL; run functional insert, update, and delete probes.
- Generate a canonical `mdq_schema_id` from tables, FTS5 DDL, indexes, constraints, foreign keys, and triggers; publish it via safe health or discovery metadata; include it in execution snapshots.
- Define readiness states healthy, rebuild in progress, degraded, inconsistent, and failed; treat documents or chunks with an unexpectedly empty FTS index as not ready.
- Reuse the recreation runbook defined by `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md` and align it with the FTS5 identity and readiness states (rebuild in progress, failed); update the ADR matrices, decision details, restart conditions, and AAL references only where the FTS5 identity changes them.

## Constraints
- Readiness exposes no unauthorized counts or paths (`issues/20261119-142123_mdqmcp001_mdq-server-boundary.md`).
- An ADR decision change needs a maintainer approval record in the same change (governance_01, governance_05); do not write or simulate it.

## Acceptance Criteria
- [ ] A normal table named `chunks_fts` and no-op triggers cannot pass readiness.
- [ ] Tokenizer, column, option, and trigger drift are detected; FTS synchronization is verified functionally.
- [ ] Execution snapshots change when the MDQ schema identity changes.
- [ ] One authoritative recreation runbook exists.

## Testing Expectations
- Real FTS5 integration tests for normal table, no-op trigger, tokenizer, column, and option drift; insert, update, delete probes; execution-snapshot identity tests; a recovery smoke test or scripted verification.
- Run ruff, mypy, fingerprint and docs checkers, and the full test suite.

## Documentation Impact
Yes. Consolidate ADR-008 recovery wording; document actual readiness guarantees and schema identity; update the AAL-024 and AAL-025 references (the governing document is `不明`; `docs/00_governance/governance_03_issue-and-uncertainty-management.md` mentions them).

## Out of Scope
- File fingerprint fields (`issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`); transactions (`issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`).

## Dependencies
- Depends on `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md` and `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`. Blocks `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md` and `issues/20261119-142132_mdqmcp010_mdq-release-readiness.md`.
- FTS5 inconsistency uses the error classification of `issues/20261119-142124_mdqmcp002_mdq-search-query-boundary.md` and the readiness reporting of `issues/20261119-142123_mdqmcp001_mdq-server-boundary.md`.

## Unresolved Questions
- `不明`: which document governs AAL-024 and AAL-025.
- `不明`: the existence and location of the MDQ re-index verification runbook.
- `不明`: how ADR-008 wording conflicts (delete, archive, or recreate) should be resolved; this needs the maintainer's decision.

## AI Implementation Instruction
Write the normal-table and no-op-trigger readiness tests first. Do not modify ADR decisions without an approval record. Stop and report any conflict between ADR-008 and the chosen sequence.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-142128
- **Related target files**: `scripts/mcp_servers/mdq/db_schema.py`, `scripts/mcp_servers/mdq/health_check.py`, `scripts/mcp_servers/mdq/mdq_security_validation.py`, `scripts/shared/schema_fingerprint.py`, `scripts/shared/execution_snapshot.py`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
