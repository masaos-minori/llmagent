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
- Verification result (2026-11-11, adversarial check against current source):
  - `Confirmed by repository evidence`: the shared deletion helper exists: `delete_document_chain()` in `scripts/rag/ingestion/document_manager.py` (explicit `chunks_vec` delete, then `documents`, CASCADE to `chunks`); it is already used by the ingestion path and cited by ADR-005 INV-02. `DocumentManager.delete_document()` in `scripts/mcp_servers/rag_pipeline/document_manager.py` still issues the same two statements itself, and ADR-005 Decision 11 says so explicitly. `SQLiteHelper.open()` returns a `SQLiteHelper`, so the helper's signature fits. `.importlinter` has no contract forbidding `mcp_servers` from importing `rag` (rag_pipeline modules already import `rag.pipeline`), although its comment lists `mcp_servers -> db, shared`. The `Unknown` helper module is resolved.
  - `Confirmed by repository evidence`: a test already asserts the MCP delete path leaves no `chunks_vec` or `chunks` rows (`tests/mcp_servers/rag_pipeline/test_document_manager.py::TestDeleteDocument::test_cascades_to_chunks_and_removes_chunks_vec`, cited by ADR-005 INV-05); a test that the path calls the shared helper is still missing.
  - `Confirmed by repository evidence`: the timeout behavior has not changed: `scripts/agent/startup_validation.py` waits 30 seconds, then `pipeline.add_warning` and startup continues. ADR-004 contains no exception for it (its only registered exception is the GitHub `path_denylist`). The decision (abort or approved exception) is still open.
  - Corrected: the "unverifiable state is already gone" premise is false. The remote RAG delegation removal merged (`b217f999b`), but `startup_validation.py` still emits two "identity-unverified ... the gate refuses fallback" warnings, and `rag_05_07` still describes them, `issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md` owns that wording; "unverifiable corpus generation" as a Fatal finding is live code (`scripts/db/rag_consistency.py`) owned by `issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md`. The dependency `adrrev003` is closed; the real ordering dependency is rmcompat001.
  - `Confirmed by repository evidence` (document conflicts): ADR-005 Decision 10 says `orphan_vec_count > 0` means "re-ingest the target documents"; `rag_05_07` maps it to `rebuild_vec` with "or `ingester.py --force`"; `security_01` line 229 and `rag_05_02-execution-guide.md` line 72 say `ingester.py --force` (the latter was missing from the issue's target list). ADR-005 line 182 and `db_07` line 96 say the startup check only warns and a timeout or failure skips it, while `rag_05_07` and the code abort on Fatal findings. `security_01` line 226 states the ingest-time skip ("Chunk skipped, WARNING logged") for a dimension mismatch, so that memo claim holds; `rag_05_07` does not separate ingest time from startup.
  - ADR-009: INV-02 and INV-10 are not duplicates (FTS-only use versus LLM context output). INV-04 and INV-09 overlap (INV-09 repeats INV-04 and adds Markdown heading chunks). INV-05 defines the normalization-failure result (no chunk for that file). The "Fail-Fast" label is inconsistent: `ChunkSplitter.process_all()` catches the error and continues with the remaining files, so it is an item-level skip, and the ADR also says no Fail-Open exists. Existing stored chunks of a file whose re-normalization fails are left in place because the failure occurs before the force prune; the ADR does not state this.
  - `scripts/agent/startup_validation.py` is a reference file only unless the timeout decision changes the code.

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
- Resolved by verification: `security_01` text, ADR-009 findings (INV-04/INV-09 overlap and the Fail-Fast label confirmed; INV-02/INV-10 refuted), the shared deletion helper (`delete_document_chain`).
- `Needs confirmation` (maintainer): the classification of a normalization failure (item-level skip versus Fail-Fast) and whether stored chunks of a re-normalization-failed file should be kept or removed.
- `Needs confirmation`: whether importing `rag.ingestion.document_manager` from `mcp_servers` is acceptable layering (no import-linter contract forbids it).

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
