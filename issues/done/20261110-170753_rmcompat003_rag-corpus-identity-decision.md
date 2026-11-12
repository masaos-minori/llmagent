# Decide the future of the RAG corpus identity and remove its tolerant branches

## Priority
Medium

## Summary
Record an explicit, approved decision to keep or remove the RAG corpus identity (`rag_corpus_meta`), and then make the code match it with no branch that returns a placeholder identity for a missing table or row.

## Background
- Source: `memo-issue.md` item H-03 (consolidated version), re-checked against current source on 2026-11-10. `plans/done/20261110-092546_adrrev003_rag-http-delegation.md` lists `corpus_identity` and the identity view of the rag-pipeline MCP server as out of scope, so the decision was not made there.
- `Explicit in code`:
  - `scripts/rag/ingestion/ingester.py` calls `bump_index_generation()` from `scripts/rag/corpus_identity.py` after a successful `ingest_all()`.
  - `corpus_identity.py` returns an identity-unverified sentinel (`verified=False`) when the table is absent ("pre-migration database") or the row is missing or corrupt, and `ensure_corpus_meta()` and `bump_index_generation()` return `None` instead of failing.
  - `scripts/rag/identity_gate.py` is now only a local identity reader (`compute_local_identity()`); its output is used for the `corpus_generation` diagnostics field and the identity view of `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`.
  - `scripts/agent/services/rag_maintenance_service.py` wraps `ensure_corpus_meta()`.
  - The startup and maintenance consistency check treats a missing, multi-row, or id-less `rag_corpus_meta` as the fatal "unverifiable corpus generation" class (`scripts/db/rag_consistency.py`, `scripts/db/rag_consistency_queries.py`); the DDL is in `scripts/db/schema_sql.py` with `CREATE TABLE IF NOT EXISTS`.
- `Operationally observed` (recorded in `plans/20261110-095137_adrrev005_schema-fingerprint-unify.md` by read-only inspection of `/opt/llm/db` on 2026-11-10): the deployed `rag.sqlite` has no `rag_corpus_meta` table.

## Problem
- Runtime code tolerates a database that the consistency check classifies as fatal, so the same defect is a hard failure in one path and a quiet placeholder in another; a broken or old database can look normal in diagnostics and in the identity view.
- The cost of the table, the ingester write path, and the maintenance wrapper is paid for a single consumer (a diagnostics field and an identity view) without an explicit decision that it is worth keeping.

## Reason for Change
- The current-only policy (`compatrm001`) says an old-shape database is rejected at startup, not handled at runtime; the deployed `rag.sqlite` already lacks the table, so the tolerant branch is reachable in production today. The decision blocks the diagnostics issue (`issues/20261110-170709_rmcompat002_rag-diagnostics-model.md`) because it decides whether `corpus_generation` exists.

## Implementation Intent
- Maintainer decision (2026-11-10, stated in the conversation): Option B (remove). It still has to be recorded as an ADR decision with an approval record (the implementer does not write the approval).
- Option A (keep; not chosen): the startup schema check guarantees the table and its single row exist; every branch that handles a missing table or row is removed.
- Option B (remove; chosen): the table, `corpus_identity.py`, the identity reader, the `bump_index_generation()` call, the maintenance wrapper, the identity view of the MCP server, and the related diagnostics field are removed together.
- Keep unrelated RAG search and ingestion behavior unchanged.

## Target Files or Areas
- `scripts/rag/corpus_identity.py`, `scripts/rag/identity_gate.py`, `scripts/rag/pipeline.py`
- `scripts/rag/ingestion/ingester.py`, `scripts/agent/services/rag_maintenance_service.py`
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`
- `scripts/db/schema_sql.py`, `scripts/db/rag_consistency.py`, `scripts/db/rag_consistency_queries.py`
- Tests: `tests/rag/test_corpus_identity.py`, `tests/rag/ingestion/test_ingester_index_generation.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_identity.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`, `tests/agent/services/test_rag_index_integrity.py`, `tests/db/test_create_schema.py`
- Documents: `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`, the schema reference for the RAG database, and the ADR that records the decision (ADR-005 or ADR-008; `Needs confirmation`)

## Required Changes
- Record the Option B decision in the chosen ADR; the approval record is the maintainer's statement.
- Implement Option B as described in Implementation Intent, including tests and documents.
- Remove every code path that returns a placeholder or `None` identity because the table or row is missing (all of them go with the module).

## Constraints
- No migration or auto-repair of an existing database (`compatrm001`): a database without the required shape is refused with an explicit archive-and-recreate error.
- Option A depends on a startup schema check that actually guarantees the table; today the check is existence-only for the RAG database, so it must be provided by the schema-fingerprint plan or by this change.
- The deployed `rag.sqlite` lacks the table; any change that makes this fatal at startup requires the operator to archive and recreate the file (deployment impact).

## Acceptance Criteria
- A recorded ADR decision with an approval record exists for the chosen option.
- No code path returns a placeholder identity because the table or row is missing.
- `rg -n "corpus_identity|rag_corpus_meta|bump_index_generation|compute_local_identity" scripts tests docs` returns nothing.
- The full test suite and the documentation checks pass.

## Testing Expectations
- Delete the identity tests and the ingester index-generation tests, and add a schema test showing the DDL has no `rag_corpus_meta`.
- Run `rules/toolchain.md` validation, `uv run python tools/check_db_separation.py` (DDL change), `uv run python tools/check_docs_consistency.py --domain rag` and `--domain db`, and the documentation checkers for ADR edits (`tools/check_adr_preservation.py`, `tools/check_adr_structure.py`).

## Documentation Impact
- Documentation must be updated: the ADR decision and its approval record, `rag_05_07` (the unverifiable-generation class under Option B), and the RAG schema reference (the table under Option B). Describe intent, boundaries, and failure behavior only; no field catalogs.

## Out of Scope
- The diagnostics model and output shape (`issues/20261110-170709_rmcompat002_rag-diagnostics-model.md`), except for the `corpus_generation` field that follows from this decision.
- Removing the remote delegation leftovers (`issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md`).
- Severity policy of the consistency check (`issues/20261109-113123_adrrev013_rag-consistency-policy.md`).
- Writing the maintainer's approval statement.

## Dependencies
- Blocks `issues/20261110-170709_rmcompat002_rag-diagnostics-model.md` (the `corpus_generation` field depends on this decision).
- Related: `plans/20261110-095137_adrrev005_schema-fingerprint-unify.md` (applies an exact schema check to `rag.sqlite`, which would also supply Option A's startup guarantee and edits `scripts/db/rag_consistency_queries.py`); decide the order before implementing, and implement after that plan lands if Option A is chosen.
- Related: `issues/20261109-113123_adrrev013_rag-consistency-policy.md` (touches the same consistency-check policy and `scripts/db/rag_consistency*.py`).

## Unresolved Questions
- Decided (2026-11-10): Option B (remove).
- `不明`: the maintainer's approval statement for the ADR record of this decision; it is not yet given.
- `不明`: the operator's plan for the deployed `rag.sqlite`, which lacks `rag_corpus_meta` (recorded in `plans/20261110-095137_adrrev005_schema-fingerprint-unify.md`). Under Option B the table is removed from the canonical DDL, so a deployed file that still matches the new DDL needs no action, but the file's other differences from the current schema and the timing of any archive and recreate are not decided.
- `Needs confirmation`: which ADR records the decision (ADR-005 or ADR-008).
- `Needs confirmation`: whether the current startup path already refuses the deployed `rag.sqlite` (the consistency check classifies a missing table as fatal in code and documents, but how startup acts on it was not traced here).
- `Needs confirmation`: whether any operator or external reader depends on the identity view of the rag-pipeline MCP server (relevant to Option B).

## AI Implementation Instruction
- Implement Option B only; the ADR record may be written in the same change, but its approval statement is the maintainer's.
- Do not write approval text on behalf of the maintainer.
- Keep comments and log text in English.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261110-170753
- **Related target files**: `scripts/rag/corpus_identity.py`, `scripts/rag/identity_gate.py`, `scripts/rag/pipeline.py`, `scripts/rag/ingestion/ingester.py`, `scripts/agent/services/rag_maintenance_service.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/db/schema_sql.py`, `scripts/db/rag_consistency.py`, `scripts/db/rag_consistency_queries.py`
