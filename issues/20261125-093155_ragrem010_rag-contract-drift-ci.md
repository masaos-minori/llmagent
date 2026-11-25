# Remove residual RAG contract drift and add CI checks for it

## Priority
Low

## Summary
After the functional RAG remediation, correct stale comments, types, and docstrings and add CI checks that compare tool schemas, artifact writers and readers, and documented configuration keys with the runtime.

## Background
Verified against master on 2026-11-25 (source: `memo-issue.md` L-01):
- Confirmed: `DocumentItem.title` is typed `str` (`scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py:221-229`); whether DB rows return null titles was not verified.
- Refuted as stated: the note asks to run "the repository Markdown linter". No markdownlint configuration (`.markdownlint*`) exists and `markdownlint` or `mdformat` is not referenced in `.pre-commit-config.yaml` or `.github/workflows/ci.yml`. The repository's document checks are its own tools (for example `tools/check_docs_consistency.py`).
- Not verified: the individual stale-comment, docstring, and HTTP-mode claims (the note lists them without locations), and `DocumentStore.get_or_create()` documentation.
- Existing contract tooling to reuse rather than duplicate: `tools/_contract_manifests.py`, `tools/check_docs_consistency.py`, and the drift checker described in `rules/tool-gates.md`.

## Problem
Contracts are duplicated across TOML, Python schemas, readers, writers, and documents with no automatic comparison, and some comments and types are stale.

## Reason for Change
Without enforcement the fixes in the preceding issues drift again.

## Implementation Intent
Fix the stale text only where it contradicts final behavior, then add CI checks that report the exact mismatched key and source files, built on the existing contract and docs-consistency tooling.

## Target Files or Areas
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`, `rag_pipeline_tools.py`, `rag_pipeline_server.py`, `document_manager.py`
- `scripts/rag/models_data.py`, `scripts/rag/ingestion/document_persistence.py`, `crawler_utils.py`, `scripts/db/store_impl.py`
- `tools/`, `.github/workflows/`, `rules/tool-gates.md`, `tests/`

## Required Changes
- Re-inventory the stale comments, DTO types, and docstrings against the final code and fix them; make `DocumentItem.title` nullable or normalize null.
- Reject invalid count parameters instead of treating them as empty or unlimited.
- Add checks comparing tool schemas (registry versus `TOOL_LIST`), artifact writer fields versus reader schemas, and documented configuration keys versus DTO fields, each reporting the mismatched key and files.
- Register new checkers in `tools/TOOL_DESCRIPTIONS.md` and `rules/tool-gates.md`.

## Constraints
- Do not start before the functional issues land.
- New checks must be deterministic and run in the existing CI jobs.

## Acceptance Criteria
- Comments and docstrings match signatures and behavior; type checking accepts DB-backed values without hidden null mismatches.
- CI fails on tool-schema, artifact-schema, or configuration drift with the mismatched key named.
- The drift gate (`tools/run_validation_gates.py drift`) stays green.

## Testing Expectations
Unit tests per new checker with a passing and a drifting fixture; gate runs per `rules/tool-gates.md`; whole-suite run.

## Documentation Impact
Update `rules/tool-gates.md` and `tools/TOOL_DESCRIPTIONS.md` for the new checks.

## Out of Scope
- Adding a Markdown linter (not present in the repository; a separate decision).

## Dependencies
- Depends on issues/20261125-093146_ragrem001_rag-runtime-tool-contracts.md, issues/20261125-093147_ragrem002_rag-startup-posture-readiness.md, issues/20261125-093148_ragrem003_rag-consistency-structured-probes.md, issues/20261125-093149_ragrem004_rag-pipeline-outcomes.md, issues/20261125-093150_ragrem005_rag-rerank-context-trust.md, issues/20261125-093151_ragrem006_rag-artifact-generations.md, issues/20261125-093152_ragrem007_rag-ingest-exit-routing.md, issues/20261125-093153_ragrem008_rag-crawler-security-policy.md, issues/20261125-093154_ragrem009_rag-embedding-validation.md.

## Unresolved Questions
- `不明`: which Markdown linter, if any, the maintainer wants; none is configured today.
- `不明`: the concrete list of stale comments (to be produced by the re-inventory).

## AI Implementation Instruction
Reuse the existing contract and docs tooling; do not invent a linter configuration; stop and ask if the stale-text list is unclear.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-093155
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`, `scripts/rag/models_data.py`, `scripts/db/store_impl.py`, `tools/_contract_manifests.py`
