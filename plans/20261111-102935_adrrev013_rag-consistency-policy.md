## Goal
Make `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` the single severity policy for RAG index consistency findings, bring ADR-005, ADR-009, `db_07`, `security_01`, and `rag_05_02` into line with it (one `orphan_vec` remediation, startup versus ingest-time dimension-mismatch handling stated separately, no restated startup behavior), and route the MCP document deletion through the shared `delete_document_chain()` helper.

## Priority
Medium

## Scope
- **In-Scope**: Documentation alignment of the five documents named in the issue plus `rag_05_02-execution-guide.md` (found during verification); ADR-009 invariant merge and normalization-failure wording; replacing the duplicated delete SQL in the MCP `DocumentManager.delete_document()` with the shared helper and the matching ADR-005 Decision 11 wording; one test proving the shared helper is used.
- **Out-of-Scope**: The startup-timeout decision (abort versus an approved ADR-004 exception) and any change to `scripts/agent/startup_validation.py` (maintainer decision, recorded as UNK-01; the documents state the current behavior); removing the identity-gate and "unverifiable" wording (owned by `issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md` and `issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md`); changing which findings are Degraded or Fatal; relaxing any Fatal abort; writing approval records for a maintainer (`plans/20261111-095703_adrrev012_adr-approval-ledger.md` and each ADR edit carry pending records).
- **Dependencies**: The issue's dependency `issues/20261109-112608_adrrev003_rag-http-delegation.md` is closed (remote delegation removed, `b217f999b`). The ordering dependency that remains is rmcompat001, which rewrites the same startup-check wording in `rag_05_07` and `startup_validation.py`.
  - **Depends on**: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md | phase all | removes the identity-gate wording from `rag_05_07` that this Plan edits around; implementing this Plan first would conflict on the same paragraph.

## Background
`rag_05_07` classifies each finding with a fixed severity (Degraded: warn and proceed; Fatal: abort startup) and says a failed or timed-out check prints a warning and startup continues. Verification (2026-11-11) found the other documents disagree: ADR-005 Decision 10 says `orphan_vec_count > 0` means re-ingest while `rag_05_07` maps it to `rebuild_vec`; `security_01` and `rag_05_02` say `ingester.py --force`; ADR-005 line 182 and `db_07` line 96 say the startup check only warns or skips and never aborts, which contradicts the Fatal abort in code; ADR-005 Decision 11 records that the MCP delete path issues the same SQL itself instead of calling the shared helper. The timeout behavior is unchanged: `startup_validation.py` waits 30 seconds, adds a warning, and continues, and ADR-004 holds no exception for it. In ADR-009, INV-04 and INV-09 overlap, and the Fail-Fast label on normalization failure disagrees with the code, which skips the file and continues.

## Problem
- Documents state different severities, remediations, and timeout handling for the same finding, so operators cannot predict whether an inconsistency stops the service and alerts cannot be designed.
- The MCP delete path duplicates the delete SQL, which can drift from the shared helper and leave orphan vector rows.
- ADR-009 carries an overlapping invariant pair and a failure classification that does not match behavior.

## Reason for Change
One policy source is needed before alerts and operations documents can be relied on, and the ADR-005 deletion-order invariant (INV-02, INV-05) is safest when both delete paths share one implementation.

## Implementation Intent
`rag_05_07` stays the only place that states severities and startup handling; the other documents reference it and keep only what they own. Fatal findings and the existing abort stay untouched. The MCP delete path calls `delete_document_chain()` (explicit `chunks_vec` delete before `documents`, unchanged order). The timeout behavior is documented as it is today and its decision is tracked, not guessed.

## Requirements
- `REQ-001`: `rag_05_07` states the startup handling of a failed or timed-out check and the dimension-mismatch handling separately for ingest time (chunk skipped, warning logged) and startup (Fatal abort), without changing any severity.
- `REQ-002`: The `orphan_vec_count > 0` remediation is `rebuild_vec` in every document (`rag_05_07`, ADR-005 Decision 10, `security_01`, `rag_05_02`); the `ingester.py --force` alternative is removed for this finding.
- `REQ-003`: ADR-005 (startup check paragraph) and `db_07` (startup consistency bullet) no longer say the startup check never aborts or that a timeout skips it; each states what it owns and references `rag_05_07` for severity and startup behavior.
- `REQ-004`: `DocumentManager.delete_document()` in the MCP server calls `delete_document_chain()` and issues no delete SQL of its own; ADR-005 Decision 11 drops the sentence that the MCP path issues the statements itself; INV-02/INV-05 (`chunks_vec` before `documents`) still hold.
- `REQ-005`: A test asserts the MCP delete path uses the shared helper (and so cannot drift), in addition to the existing no-orphan test.
- `REQ-006`: ADR-009 merges INV-04 and INV-09 into one invariant, states the normalization-failure result (no chunks for that file, remaining files continue, stored chunks of that file are left unchanged), and relabels the condition so it no longer reads as Fail-Fast; pending maintainer approval records are marked, none invented.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Modify | Add the separate ingest-time and startup dimension-mismatch statements, state the failed/timed-out check behavior as the single policy, and standardize the `orphan_vec_count > 0` row (line 94) on `rebuild_vec` | REQ-001, REQ-002 / AC-1, AC-2 | Lines 22-26 (startup handling), 44-45 (severity table), 94 ("`rebuild_vec` ... (or `ingester.py --force`)") (checked in Step 2) | `tools/check_docs_consistency.py --domain rag` | Verified |
| `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Modify | Decision 10 `orphan_vec_count` remediation to `rebuild_vec`; line 182 startup-check paragraph; Decision 11 MCP-path sentence | REQ-002, REQ-003, REQ-004 / AC-2, AC-3, AC-4 | Line 79 "re-ingest the target documents"; line 182 "does not abort startup; a timeout or an unexpected failure of the check skips it"; Decision 11 "The MCP path issues the same statements itself rather than calling the shared helper" (checked in Step 2) | `tools/check_adr_invariant_matrix.py`, `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Modify | Merge INV-04 and INV-09, state the normalization-failure result and existing-chunk behavior, relabel the Fail-Fast condition | REQ-006 / AC-6 | INV-04 (line 161) and INV-09 (line 166) overlap; Failure Policy lines 172-175 label a file-level skip "Fail-Fast"; `ChunkSplitter.process_all()` catches the error and continues (checked in Step 3) | `tools/check_adr_invariant_matrix.py`, `tools/check_adr_structure.py`, `tools/check_adr_preservation.py` | Verified |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Modify | Replace the "non-critical, skippable finding and does not stop startup" bullet (line 96) with a reference to `rag_05_07` | REQ-003 / AC-3 | Line 96 (checked in Step 2) | `tools/check_docs_consistency.py --domain db` | Verified |
| `docs/91_security/security_01_architecture-and-trust-boundaries.md` | Modify | Orphan-vector remediation (line 229) to `rebuild_vec`; keep the ingest-time dimension-mismatch row (line 226) and make it say ingest time | REQ-001, REQ-002 / AC-1, AC-2 | Line 226 "Chunk skipped, WARNING logged"; line 229 "Run `ingester.py --force`" (checked in Step 2) | `tools/check_docs_consistency.py --domain overview` | Verified |
| `docs/21_rag/rag_05_02-execution-guide.md` | Modify | Line 72 says `orphan_vec_count > 0` is fixed by `ingester.py --force`; standardize on `rebuild_vec` | REQ-002 / AC-2 | Line 72 (checked in Step 2; missing from the issue's target list) | `tools/check_docs_consistency.py --domain rag` | Verified |
| `scripts/mcp_servers/rag_pipeline/document_manager.py` | Modify | `delete_document()` replaces its two inline `DELETE` statements with `delete_document_chain(db, doc_id)` (2973 bytes) | REQ-004 / AC-4 | Lines 66-81 issue `DELETE FROM chunks_vec ...` and `DELETE FROM documents ...`; `open()` returns a `SQLiteHelper`, matching the helper's signature (checked in Step 3) | `tests/mcp_servers/rag_pipeline/test_document_manager.py` | Verified |
| `tests/mcp_servers/rag_pipeline/test_document_manager.py` | Modify | Add a test that `delete_document()` calls the shared helper | REQ-005 / AC-5 | `TestDeleteDocument` at line 245 already covers no orphan `chunks_vec` rows (checked in Step 3) | itself | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/document_manager.py` | Defines `delete_document_chain()` (the shared helper) and its db-layer-only imports | REQ-004 |
| `scripts/agent/startup_validation.py` | The 30-second timeout path and Fatal/Degraded routing the documents must describe; unchanged by this Plan | REQ-001, REQ-003 |
| `scripts/rag/ingestion/chunk_splitter.py` | `process_all()` catches the normalization error and continues | REQ-006 |
| `scripts/rag/ingestion/chunk_japanese.py` | Raises `TokenizationError` on normalization failure | REQ-006 |
| `scripts/db/rag_consistency.py` | Findings and their fixed severities | REQ-001 |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` | Caller of `DocumentManager.delete_document()` | REQ-004 |
| `.importlinter` | Confirms no contract forbids `mcp_servers` importing `rag` | REQ-004 |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Failure policy; holds no exception for the timeout skip | REQ-001, REQ-003 |
| `docs/10_adr/adr_01_index.md` | Invariant matrix; cites ADR-009 INV-07 and INV-10 (check for INV-04/INV-09 after the merge) | REQ-006 |
| `tests/agent/services/test_rag_index_integrity.py` | Existing delete-chain and consistency tests cited by ADR-005 | REQ-004 |
| `tests/rag/ingestion/test_delete_chain.py` | Existing helper ordering test cited by ADR-005 INV-02 | REQ-004 |

## Acceptance Criteria
- AC-1: `rag_05_07` and `security_01` state the dimension-mismatch handling separately for ingest time (skip and warn) and startup (Fatal abort), with no severity changed (`REQ-001`).
- AC-2: Every document gives `rebuild_vec` as the `orphan_vec_count > 0` remediation and none still says `ingester.py --force` for it (`REQ-002`).
- AC-3: ADR-005 and `db_07` no longer state that the startup check never aborts or that a timeout skips it; severity and startup handling are referenced to `rag_05_07` (`REQ-003`).
- AC-4: `DocumentManager.delete_document()` contains no `DELETE` SQL and calls `delete_document_chain()`; ADR-005 Decision 11 matches (`REQ-004`).
- AC-5: A test fails if `delete_document()` stops using the shared helper; the existing no-orphan test still passes (`REQ-005`).
- AC-6: ADR-009 has no overlapping invariants, states the normalization-failure result and existing-chunk behavior, and its failure label matches the code (`REQ-006`).
- AC-7: `check_adr_authority.py`, `check_adr_invariant_matrix.py`, `check_adr_structure.py`, `check_docs_consistency.py --domain rag`, `check_docs_content_policy.py --strict`, `check_docs_quality.py`, `check_docs_structure.py`, and `check_docs_japanese.py` pass; `uv run pytest tests/rag tests/agent/services/test_rag_index_integrity.py tests/mcp_servers/rag_pipeline -v` passes; `check_adr_preservation.py` reports only the intended ADR-005/ADR-009 text changes.

## Tests
- `REQ-005`: in `tests/mcp_servers/rag_pipeline/test_document_manager.py`, patch `delete_document_chain` where `DocumentManager` imports it and assert it is called once with the document id on a hit and not called on a miss (`tools/check_mock_patch_targets.py` must pass).
- `REQ-004`: existing `TestDeleteDocument` cases (no orphan `chunks_vec`, other documents untouched) and `tests/rag/ingestion/test_delete_chain.py` run unchanged.
- Documentation requirements are verified by the checkers in the Validation plan.

## Documentation Impact
RAG, DB, security, and ADR documents (`docs/00_index.md` "Document References by Task", rag/db/overview/governance areas): `rag_05_07` stays the policy source; ADR-005, ADR-009, `db_07`, `security_01`, and `rag_05_02` become references or are corrected (REQ-001 to REQ-004, REQ-006). State intent, severity, and failure behavior; do not copy implementation locations (docs content policy). Write in English.

## Assumptions
- Importing `rag.ingestion.document_manager` from `mcp_servers.rag_pipeline` follows existing precedent (`rag_pipeline_service.py` and `rag_pipeline_server.py` already import `rag.*`) and no import-linter contract forbids it; the helper imports only `db` and `shared`. Recorded as UNK-03 for confirmation.
- The ADR-009 invariant merge keeps the remaining invariant numbers stable (INV-09 is folded into INV-04 and the other numbers are not renumbered) because the ADR index cites invariants by number; `check_adr_structure.py` confirms this is acceptable (UNK-04).
- Overlap judgment (`tools/check_plan_target_overlaps.py`): `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` is also targeted by `plans/20261110-233648_adrrev009_adr008-recovery-align.md`; compatible, because that Plan edits sections 9.2 and 9.5 (backup verification) and this Plan edits only the startup-consistency bullet near line 96.
- Relabeling the normalization-failure condition and stating the existing-chunk behavior documents current code; any change of that behavior is out of scope.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | On a startup check timeout or failure, abort startup or register an ADR-004 exception | Maintainer decision; ADR-004 holds no exception and code warns and continues | Maintainer decides; this Plan documents the current behavior and any code or ADR-004 change becomes a follow-up issue | False |
| UNK-02 | Classification of a normalization failure (item-level skip versus Fail-Fast) and whether stored chunks of a re-normalization-failed file are kept | The ADR says Fail-Fast but code continues; stored chunks stay because the failure precedes the force prune | Maintainer confirms; Phase 5 words ADR-009 to match code and marks the approval record pending | False |
| UNK-03 | Whether `mcp_servers` importing `rag.ingestion.document_manager` is acceptable layering | `.importlinter` has no contract against it, but its comment says `mcp_servers -> db, shared` | Run `lint-imports` in Phase 3; if it fails or the maintainer objects, move the helper to the `db` layer as a plan amendment | False |
| UNK-04 | Whether `check_adr_structure.py` and the invariant matrix accept a gap after folding INV-09 into INV-04, and whether the index cites ADR-009 INV-04/INV-09 | The index excerpt cites INV-07 and INV-10; line 207 lists were not read in full | Run the ADR checkers after the edit; add `docs/10_adr/adr_01_index.md` through `tools/amend_plan.py` (fallout) if it needs an update | False |
| UNK-05 | Maintainer approval statements for the ADR-005 and ADR-009 decision-text edits | Approvals are maintainer statements | Write marked pending records and report them (ledger plan tracks them) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Modify | Medium (policy source; referenced by four documents) | 3 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Modify | Medium (ADR graph and index consumers) | 2 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Modify | Medium (invariant matrix) | 2 | N/A | not applicable (docs) |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Modify | Low | 20 | N/A | not applicable (docs) |
| `docs/91_security/security_01_architecture-and-trust-boundaries.md` | Modify | Low | 15 | N/A | not applicable (docs) |
| `docs/21_rag/rag_05_02-execution-guide.md` | Modify | Low | 1 | N/A | not applicable (docs) |
| `scripts/mcp_servers/rag_pipeline/document_manager.py` | Modify | Low (one method; sole caller is `rag_pipeline_service.py`) | 0 | N/A | Requires deploy of `scripts/` (rag-pipeline-mcp restart) |
| `tests/mcp_servers/rag_pipeline/test_document_manager.py` | Modify | Low | 0 | N/A | not applicable (tests are not deployed) |

## Design
Path B (more than 3 files). Findings from the inspection:
- Architecture: `mcp_servers.rag_pipeline.document_manager` currently imports only `db`/`shared`; adding `from rag.ingestion.document_manager import delete_document_chain` creates an `mcp_servers -> rag` edge already used elsewhere in the same package. `rag.ingestion.document_manager` imports `db.helper`, `db.models`, `db.rag_consistency`, `shared.logger`, so no new cycle. Alternative rejected: moving the helper to `db` (wider blast radius across ingestion and Agent callers) unless UNK-03 forces it.
- Dependency graph: the sole production caller of `DocumentManager.delete_document()` is `rag_pipeline_service.py`; the helper is also used by the ingester path (ADR-005 INV-02).
- Historical: churn figures are from `git log --since=30.days`; bus factor is `N/A`.
- Operational: rag-pipeline-mcp (port 8010) restarts on deploy; no database schema or lock is touched. Persisted schema: not applicable.
- Consumer scan: no persisted schema, public API, or shared constant changes (`not affected`: the delete statements are identical, so ADR-005 INV-02/INV-05 and the `chunks_vec_ad` backstop trigger behave the same).
- Ordering with sibling work: this Plan edits `rag_05_07` around the startup paragraph that rmcompat001 rewrites; implementing after rmcompat001 avoids a conflict (the `Depends on` line). `rag_05_07` is also a target of rmcompat003 (corpus identity); the edits touch different sentences.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: MCP delete path through the shared helper** (REQ-004, REQ-005; `scripts/mcp_servers/rag_pipeline/document_manager.py`, `tests/mcp_servers/rag_pipeline/test_document_manager.py`)
   - [ ] Write the helper-usage test first and see it fail.
   - [ ] Replace the inline `DELETE` statements with `delete_document_chain(db, doc_id)`.
   - [ ] Run `uv run pytest tests/mcp_servers/rag_pipeline tests/rag/ingestion/test_delete_chain.py -v`.
2. **Phase 2: Policy source and remediation standardization** (REQ-001, REQ-002; `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`, `docs/21_rag/rag_05_02-execution-guide.md`)
   - [ ] State startup versus ingest-time dimension-mismatch handling and the failed/timed-out check behavior in `rag_05_07`.
   - [ ] Standardize `orphan_vec_count > 0` on `rebuild_vec` in all three documents.
3. **Phase 3: ADR-005 and db_07 alignment** (REQ-002, REQ-003, REQ-004; `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`)
   - [ ] Update ADR-005 Decision 10, the startup-check paragraph, and Decision 11; add a pending approval record for the decision-text edits.
   - [ ] Replace the `db_07` startup bullet with a reference to `rag_05_07`.
   - [ ] Run `lint-imports` (UNK-03).
4. **Phase 4: ADR-009 invariants and failure wording** (REQ-006; `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`)
   - [ ] Fold INV-09 into INV-04, update the Verification table and the no-dedicated-test line.
   - [ ] State the normalization-failure result and existing-chunk behavior and relabel the condition; add a pending approval record.
5. **Phase 5: Deployment & Verification** (`scripts/mcp_servers/rag_pipeline/document_manager.py` and the documents above)
   - [ ] Run the Validation plan commands and the `rules/toolchain.md` sequence.
   - [ ] Hand off to `skills/deploy/SKILL.md`: the change is committed and pushed first, and deploying is the user's decision (approval gate); rag-pipeline-mcp restarts on deploy.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/rag_pipeline/document_manager.py` | Unit and integration | `uv run pytest tests/rag tests/agent/services/test_rag_index_integrity.py tests/mcp_servers/rag_pipeline -v` | Pass |
| Python targets | Format, lint, type, security | `uv run ruff format <files>`, `uv run ruff check <files>`, `uv run mypy <files>`, `uv run bandit -r scripts/mcp_servers/rag_pipeline -c pyproject.toml` | Clean |
| `tests/mcp_servers/rag_pipeline/test_document_manager.py` | Mock patch target reaches code | `uv run python tools/check_mock_patch_targets.py` | Pass |
| Architecture | Import contracts | `uv run lint-imports` | Pass |
| Coverage | Changed lines | `rules/toolchain.md` section 7 diff-cover sequence | At or above the Completion checklist threshold |
| RAG, DB, security, ADR docs | Structure and policy | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` | Pass |
| RAG docs | Claims against code and config | `uv run python tools/check_docs_consistency.py --domain rag` (and `--domain db`, `--domain overview` for the other two) | Pass |
| ADR-005, ADR-009 | ADR structure, authority, matrix, preservation | `uv run python tools/check_adr_structure.py`, `check_adr_authority.py`, `check_adr_invariant_matrix.py`, `check_adr_preservation.py` | Pass (preservation: only the intended text changes reported) |

Validation quality baseline: `radon` and `vulture` are not installed on this host (Tool availability guard; ruff covers the lightweight checks); `bandit -q -r scripts/mcp_servers/rag_pipeline -c pyproject.toml` exited 0 with no finding on the scanned path.

## Risks
- **Risk**: Routing delete through the helper changes delete order or transaction behavior and leaves orphan vectors. → **Mitigation**: The helper issues the same two statements in the same order; the existing no-orphan and other-documents-untouched tests plus `test_delete_chain.py` run unchanged; the caller keeps its own commit.
- **Risk**: An `mcp_servers -> rag` import trips an architecture contract or draws a layering objection. → **Mitigation**: `lint-imports` in Phase 3 and UNK-03; fall back to moving the helper to `db` by plan amendment.
- **Risk**: Folding INV-09 into INV-04 breaks the invariant matrix or an index citation. → **Mitigation**: Keep other invariant numbers stable and run `check_adr_invariant_matrix.py` and `check_adr_structure.py`; UNK-04.
- **Risk**: Documenting the timeout as "warn and continue" is read as approving a fail-open that ADR-004 does not allow. → **Mitigation**: State it as current behavior with the decision pending (UNK-01), not as an approved exception; the ledger plan can record it.
- **Risk**: Editing `rag_05_07` collides with rmcompat001. → **Mitigation**: The `Depends on` line orders this Plan after it; `tools/check_plan_target_overlaps.py` is rerun when both exist.
- **Risk**: A decision-text edit to ADR-005 or ADR-009 lacks an approval record. → **Mitigation**: Marked pending records, reported, never fabricated (UNK-05).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | MCP delete path through the shared helper (REQ-004, REQ-005) | Pending | — | — | |
| 2 | Policy source and remediation standardization (REQ-001, REQ-002) | Pending | — | — | |
| 3 | ADR-005 and db_07 alignment (REQ-002, REQ-003, REQ-004) | Pending | — | — | |
| 4 | ADR-009 invariants and failure wording (REQ-006) | Pending | — | — | |
| 5 | Deployment & Verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261109-113123_adrrev013_rag-consistency-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261111-102935
- **Related target files**: `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`, `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`, `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`, `docs/21_rag/rag_05_02-execution-guide.md`, `scripts/mcp_servers/rag_pipeline/document_manager.py`, `tests/mcp_servers/rag_pipeline/test_document_manager.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes: state ingest-time and startup dimension-mismatch handling separately | `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Step 2 | AC-1 | `check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-001 | Verification: `security_01` line 226 states the ingest-time skip | `docs/91_security/security_01_architecture-and-trust-boundaries.md` | Step 2 | AC-1 | `check_docs_consistency.py --domain overview` | Confirmed by repository evidence |
| REQ-002 | Required Changes: standardize the `orphan_vec` remediation on `rebuild_vec()` | `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Step 2 | AC-2 | `check_docs_consistency.py --domain rag` | Confirmed by repository evidence |
| REQ-002 | Same; `security_01` line 229 | `docs/91_security/security_01_architecture-and-trust-boundaries.md` | Step 2 | AC-2 | `check_docs_consistency.py --domain overview` | Confirmed by repository evidence |
| REQ-002 | Verification: `rag_05_02` line 72 missing from the issue's targets | `docs/21_rag/rag_05_02-execution-guide.md` | Step 2 | AC-2 | `check_docs_consistency.py --domain rag` | Derived from confirmed evidence |
| REQ-002 | Background: ADR-005 lists re-ingest for `orphan_vec_count > 0` | `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Step 3 | AC-2 | `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes: update ADR-005 and `db_07` to the Degraded/Fatal classification | `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Step 3 | AC-3 | `check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-003 | Same; `db_07` line 96 | `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Step 3 | AC-3 | `check_docs_consistency.py --domain db` | Confirmed by repository evidence |
| REQ-004 | Required Changes: route MCP-side deletion through the shared helper | `scripts/mcp_servers/rag_pipeline/document_manager.py` | Step 1 | AC-4 | `uv run pytest tests/mcp_servers/rag_pipeline -v` | Confirmed by repository evidence |
| REQ-004 | Same; ADR-005 Decision 11 records the duplicated SQL | `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Step 3 | AC-4 | `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-005 | Testing Expectations: a test for the MCP delete path | `tests/mcp_servers/rag_pipeline/test_document_manager.py` | Step 1 | AC-5 | `check_mock_patch_targets.py`, pytest | Derived from confirmed evidence |
| REQ-006 | Required Changes: merge duplicate ADR-009 invariants, define normalization-failure behavior, fix classification | `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` | Step 4 | AC-6 | `check_adr_invariant_matrix.py`, `check_adr_preservation.py` | Confirmed by repository evidence |
