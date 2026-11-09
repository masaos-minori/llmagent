# Align the RAG consistency-check policy across ADR-005, ADR-009, db_07, security_01, and rag_05_07

## Priority
Medium

## Summary
Make `rag_05_07` the single severity policy for RAG index consistency findings (Degraded versus Fatal), align ADR-005, ADR-009, `db_07`, and `security_01` with it, decide the timeout behavior explicitly, standardize the `orphan_vec` remediation, and route the MCP delete path through the shared helper.

## Background
- Source: `memo-issue.md` item M-04, re-checked against current source on 2026-11-09.
- `Explicit in documentation` (`docs/21_rag/rag_05_07-rag-index-consistency-checks.md`): findings have a fixed severity in code, Degraded (warn and proceed) or Fatal (abort startup); a failed or timed-out check prints an identity-unverified warning and startup continues. This document also describes an identity gate and an "unverifiable" state that the RAG delegation removal issue in this batch deletes.
- `Explicit in documentation`: ADR-005 (`docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`) lists the `orphan_vec_count > 0` remediation as "re-ingest the target documents", while `rag_05_07` maps orphan vec rows to `rebuild_vec`. `db_07` states the startup consistency check records mismatches as warnings, does not abort startup, and that a timeout or unexpected failure skips the check; `rag_05_07` classifies an embedding-dimension mismatch as Fatal, and `rag_05_07` also says at ingest time a dimension mismatch skips the chunk with a warning (the memo says `security_01` mentions the skip; `Needs confirmation` against `security_01`).
- `Explicit in code`: `scripts/mcp_servers/rag_pipeline/document_manager.py` `delete_document()` issues its own `DELETE FROM chunks_vec ...` SQL; `scripts/db/schema_sql.py` also defines a `chunks_vec_ad` trigger on `chunks`. `Needs confirmation`: whether a shared deletion helper exists for the Agent-side maintenance path that the MCP path should reuse.
- `Needs confirmation`: ADR-009's invariants and failure classification (the memo reports duplicate INVs INV-02/10 and INV-04/09, an undefined behavior for existing chunks on normalization failure, and a continue-on-error behavior classified as Fail-Fast). ADR-009 INV-05 now states that a failed normalization produces no chunks; the remaining memo claims were not confirmed.
- Related archived: `startup001_classify-rag-consistency-startup-exceptions-instead-of-skipping-all`, `startup002_clarify-startup-status-reporting-for-skipped-checks-and-shutdown-during-startup` under `issues/done/`. Re-verify this issue against current source; the timeout behavior may already have changed.

## Problem
- Several documents state different severities and different timeout handling for the same finding, so operators cannot predict whether an index inconsistency stops the service, and alerts cannot be designed.
- Skipping the check on timeout means a large or slow database may never be checked; ADR-004 requires such a fail-open to be an approved exception.
- Different remediations for the same finding (re-ingest versus `rebuild_vec`) cost differently, and duplicated delete SQL can drift from the shared helper and leave orphans.

## Reason for Change
- One severity policy is needed before alerts and operations documents can be relied on. Timing: after the RAG delegation removal merges, so the "unverifiable" state is already gone from `rag_05_07`.

## Implementation Intent
- `rag_05_07` is the single severity policy; every exception to Fail-Fast is explicit and approved; every write path uses the shared helpers.
- Documents reference the policy instead of restating it.

## Target Files or Areas
- `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`, `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`, `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`
- `scripts/mcp_servers/rag_pipeline/document_manager.py` and the shared deletion helper (`Unknown`: exact module), `scripts/agent/startup_validation.py` (timeout path)
- `tests/agent/services/test_rag_index_integrity.py` and related RAG tests

## Required Changes
- Update ADR-005, ADR-009, `db_07`, and `security_01` to the Degraded/Fatal classification of `rag_05_07`.
- Decide the timeout behavior: abort, or register an ADR-004 exception.
- State separately the handling at ingest time (skip the chunk and warn) and at startup (Fatal) for a dimension mismatch.
- Standardize the `orphan_vec` remediation on `rebuild_vec()`, and route MCP-side deletion through the shared helper.
- Merge duplicate invariants in ADR-009, define the normalization-failure behavior, and fix its Fail-Fast classification, after confirming the memo's findings.

## Constraints
- Fatal findings stay un-downgradable (`rag_05_07` AC-4); do not relax any current abort.
- ADR amendments need approval records (governance-ledger issue); the implementer must not fabricate approvals.
- The deletion change must keep ADR-005 INV-02/INV-05 (explicit `chunks_vec` deletion before `documents`).
- Docs content policy applies: describe policy, not code locations.

## Acceptance Criteria
- All five documents state the same severity for each finding and the same timeout behavior.
- No duplicated delete SQL remains in the MCP delete path (it calls the shared helper).
- ADR-009 has no duplicate invariants (if the memo's claim holds).
- `check_adr_authority.py`, `check_adr_invariant_matrix.py`, `check_adr_structure.py`, and `check_docs_consistency.py --domain rag` pass; RAG tests pass.

## Testing Expectations
- `uv run pytest tests/rag tests/agent/services/test_rag_index_integrity.py tests/mcp_servers/rag_pipeline -v`; a test that the MCP delete path leaves no orphan vector rows; full validation sequence if code changes.
- Documentation checkers listed above.

## Documentation Impact
- `rag_05_07` stays the policy source; ADR-005, ADR-009, `db_07`, and `security_01` become references or are corrected. State intent, severity, and failure behavior without copying implementation locations.

## Out of Scope
- Removing the RAG delegation path (separate issue in this batch).
- Changing which findings are Degraded or Fatal, unless a document conflict requires a decision.

## Dependencies
- Depends on: `issues/20261109-112608_adrrev003_rag-http-delegation.md` (removes the unverifiable/fallback state first).
- Related, recently archived: `startup001` and `startup002` under `issues/done/`.

## Unresolved Questions
- Decision: on timeout, abort startup or register an ADR-004 exception (maintainer; `不明`).
- `Needs confirmation`: `security_01` text; ADR-009 invariant duplicates and classification; the shared deletion helper to reuse.

## AI Implementation Instruction
- Treat `rag_05_07` as the source for severities; change it only where a maintainer decision requires.
- Do not relax or reclassify an existing Fatal finding.
- Do not write approval records on a maintainer's behalf.
- Write documentation in English and follow the docs content policy; do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-113123
- **Related target files**: `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`, `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`, `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`, `scripts/mcp_servers/rag_pipeline/document_manager.py`, `scripts/agent/startup_validation.py`
