## Goal
- Implement the maintainer's Option B decision (remove) for the RAG corpus identity: delete `rag_corpus_meta`, `corpus_identity.py`, `identity_gate.py`, the ingester `bump_index_generation()` call, the maintenance wrapper, the identity view of the rag-pipeline MCP server, the `corpus_generation` diagnostics field, and the "unverifiable corpus generation" fatal class, so no branch returns a placeholder identity for a missing table or row. RAG search and ingestion behavior otherwise stays unchanged.

## Priority
Medium

## Scope
- **In-Scope**: the removals above, their tests, the `identity-unverified` startup warning prefix and the tests that assert it, the table entry in `tools/check_db_separation.py`, the documents that describe the identity, and a decision record (pending the maintainer's statement) in the ADR that owns the identity contract.
- **Out-of-Scope**: the rest of the diagnostics model and output shape (`issues/20261110-170709_rmcompat002_rag-diagnostics-model.md`; this Plan removes only the `corpus_generation` field it must remove to delete the identity reader); the remote delegation leftovers (`plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md`); the severity policy of the consistency check; writing the maintainer's approval statement; editing the historical body text of the withdrawn ADR-010; any migration or auto-repair of an existing database (`compatrm001`).
- **Dependencies**: Blocks `issues/20261110-170709_rmcompat002_rag-diagnostics-model.md` (it needs the `corpus_generation` removal landed here). Coordinates with `plans/done/20261111-102935_adrrev013_rag-consistency-policy.md` and its open procedures, which edit the same `rag_05_07` sentences and `rag_pipeline_server.py` `call_tool` (different regions); apply this Plan's edits to a re-read of those files.
  - **Depends on**: plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md | phase all | it edits `ingester.py` and rewrites the same two `startup_validation.py` warnings whose `identity-unverified` prefix this Plan removes.

## Background
`plans/done/20261110-092546_adrrev003_rag-http-delegation.md` left the corpus identity out of scope. The maintainer decided Option B (remove) on 2026-11-10 (stated in the Issue). Verified against current source (2026-11-12, Step 2 and Step 3):
- `corpus_identity.py` returns a `verified=False` sentinel for a missing table or row and `ensure_corpus_meta()` and `bump_index_generation()` return `None`; `identity_gate.compute_local_identity()` feeds `RagPipeline.augment()` (`pipeline.py:201`), `_identity_payload()` in `rag_pipeline_server.py`, and nothing else.
- `scripts/db/rag_consistency.py` treats a missing, multi-row, or id-less table as the fatal class `_unverifiable_corpus_issue` through `RagConsistencyReport.corpus_meta_verified` (`models.py:118`), but `_corpus_meta_verifiable` tolerates an absent table. The deployed `rag.sqlite` lacks the table (recorded in `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md`, not re-inspected).
- `deploy/init_db.sh` refuses any database whose shape differs from the canonical DDL by the exact-match fingerprint (missing and extra tables alike), so today the deployed file fails that gate on this table; removing the table from the DDL makes the deployed file match on this point.

Corrections found against the Issue (Step 2 and Step 3):
- The Issue's test list omits `tests/rag/test_identity_gate.py`, `tests/db/test_rag_consistency.py`, `tests/db/test_recovery_drill.py`, `tests/db/test_db_recovery.py`, `tests/deploy/test_init_db_schema_gate.py` (imports `ensure_corpus_meta`), `tests/rag/ingestion/test_ingester.py` (own copy of the DDL), and the three startup tests that assert `identity-unverified`; all are target rows here.
- The Issue's source list omits `scripts/db/models.py` (`corpus_meta_verified`), `tools/check_db_separation.py` (`TABLE_OWNERSHIP["rag"]` still lists `rag_corpus_meta`; the ADR-008 inventory at line 409 already lists four tables), `scripts/rag/models_result.py` (`corpus_generation`), `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` (`corpus_identity` wire field), and `scripts/agent/startup_validation.py` (the `RAG identity-unverified:` prefix).
- No schema reference document lists `rag_corpus_meta`; `docs/41_db/db_02_architecture_and_schema-schema-reference.md` and ADR-008 already match Option B, so neither needs an edit. `docs/41_db/db_06...` names `corpus_meta_verified` and `rag_01_system_overview.md` still describes an identity comparison on the removed fallback path; both are targets.
- `rg -n "corpus_identity|rag_corpus_meta|bump_index_generation|compute_local_identity" scripts tests docs` cannot return nothing: the withdrawn ADR-010 body names `corpus_identity` and its text is preserved (`tools/check_adr_preservation.py`), and the decision record may name the table. The acceptance search excludes that ADR's historical text.
- ADR placement: ADR-005 and ADR-008 never mention the table; ADR-010 (Withdrawn) introduced the identity contract through the RAGCORPUS001 amendment, so the decision record extends its Withdrawal record.

## Problem
Runtime code tolerates a database the consistency check classifies as fatal, so the same defect is a hard failure in one path and a quiet placeholder in another. The table, the ingester write path, the maintenance wrapper, a wire field, and a diagnostics field are paid for a single consumer without an explicit decision that it is worth keeping.

## Reason for Change
`compatrm001`: an old-shape database is rejected at startup, not handled at runtime. The decision blocks the diagnostics Issue because it decides whether `corpus_generation` exists.

## Implementation Intent
- Remove consumers first, then the modules, then the consistency class and the DDL; every phase leaves the codebase testable (the last three form one release unit).
- No compatibility key, alias, or tolerant branch: the MCP response and health details simply stop carrying `corpus_identity`; a database that still has the old table is refused by the fingerprint gate with the existing archive-and-recreate error.
- Record the decision in the ADR record with the approval left as `Pending maintainer statement`; the implementer does not write approval text.

## Requirements
- `REQ-001`: Record the Option B decision in ADR-010's Withdrawn record with the approval line pending; no approval text is written.
- `REQ-002`: `RagPipeline` no longer computes or reports a corpus generation: remove `compute_local_identity` use, `SCHEMA_VERSION`, `_last_corpus_generation`, the post-hoc `corpus_generation` key in `get_diagnostics()`, and `SearchDiagnostics.corpus_generation`.
- `REQ-003`: The rag-pipeline MCP server and its response model no longer produce or declare `corpus_identity`.
- `REQ-004`: `RagIngester` no longer imports or calls `bump_index_generation()`.
- `REQ-005`: `RagMaintenanceService` no longer wraps `ensure_corpus_meta()`.
- `REQ-006`: `scripts/rag/corpus_identity.py` and `scripts/rag/identity_gate.py` are deleted with their tests.
- `REQ-007`: The consistency check no longer has the unverifiable-corpus-generation fatal class: remove `_check_corpus_meta`, `_unverifiable_corpus_issue`, `_corpus_meta_verifiable`, and `RagConsistencyReport.corpus_meta_verified`.
- `REQ-008`: The canonical RAG DDL has no `rag_corpus_meta`, `TABLE_OWNERSHIP["rag"]` matches, and a schema test shows the table is absent.
- `REQ-009`: The startup consistency warnings no longer use the `identity-unverified` prefix; severity and continue-startup behavior are unchanged.
- `REQ-010`: Documents describe only current behavior: `rag_05_07`, `rag_01_system_overview`, `rag_03_03`, `rag_04`, `db_06` carry no identity or unverifiable-generation wording.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | Decision record | Extend the Withdrawn bullet and Withdrawal Approval Record with the Option B removal; approval stays pending | REQ-001 / AC-1 | line 252 Withdrawn bullet; lines 292-294 pending record (checked in Step 2) | `tools/check_adr_preservation.py` | Verified |
| `scripts/rag/pipeline.py` | Pipeline | Remove identity import, `SCHEMA_VERSION`, `_last_corpus_generation`, the compute block, and the `get_diagnostics` append | REQ-002 / AC-2 | lines 37, 51-55, 92, 200-206, 257-264 (checked in Step 3) | `tests/rag/test_diagnostics.py` | Verified |
| `scripts/rag/models_result.py` | Diagnostics model | Remove `SearchDiagnostics.corpus_generation` and its comment | REQ-002 / AC-2 | lines 90-91 (checked in Step 3) | `tests/rag/test_augment_refiner.py` | Verified |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | MCP server | Delete `_identity_payload` and its three uses | REQ-003 / AC-3 | lines 73-114, 240, 258, 296 (checked in Step 3) | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` | Verified |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | Response model | Remove the `corpus_identity` field | REQ-003 / AC-3 | line 259 (checked in Step 3) | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` | Verified |
| `scripts/rag/ingestion/ingester.py` | Ingester | Remove the import and the `bump_index_generation` call and the `total_success` sum it alone uses if unused | REQ-004 / AC-4 | lines 20, 183-190; `total_success` also read at line 200 (checked in Step 3) | `tests/rag/ingestion/test_ingester.py` | Verified |
| `scripts/agent/services/rag_maintenance_service.py` | Maintenance service | Remove the `corpus_identity()` wrapper, its import, and the NOTE comment | REQ-005 / AC-5 | lines 16, 60-78 (checked in Step 3) | `tests/agent/services/test_rag_index_integrity.py` | Verified |
| `scripts/rag/corpus_identity.py` | Identity module | Delete | REQ-006 / AC-6 | 29 identity references; importers pipeline, ingester, maintenance, one test (checked in Step 3) | `tests/rag/test_corpus_identity.py` | Verified |
| `scripts/rag/identity_gate.py` | Identity reader | Delete | REQ-006 / AC-6 | importers pipeline and server only (checked in Step 3) | `tests/rag/test_identity_gate.py` | Verified |
| `scripts/db/rag_consistency_queries.py` | Fatal-class probes | Remove `_check_corpus_meta` and its docstring line | REQ-007 / AC-7 | lines 12, 283-300 (checked in Step 3) | `tests/db/test_rag_consistency.py` | Verified |
| `scripts/db/rag_consistency.py` | Consistency check | Remove `_unverifiable_corpus_issue`, `_corpus_meta_verifiable`, the report field use, and the check entry | REQ-007 / AC-7 | lines 11, 111, 137, 374-400, 447 (checked in Step 3) | `tests/db/test_rag_consistency.py` | Verified |
| `scripts/db/models.py` | Report model | Remove `RagConsistencyReport.corpus_meta_verified` | REQ-007 / AC-7 | line 118 (checked in Step 3) | `tests/db/test_db_recovery.py` | Verified |
| `scripts/db/schema_sql.py` | Canonical DDL | Remove the `rag_corpus_meta` table | REQ-008 / AC-8 | lines 47-56 (checked in Step 3) | `tests/db/test_create_schema.py` | Verified |
| `tools/check_db_separation.py` | Ownership inventory | Remove `rag_corpus_meta` from `TABLE_OWNERSHIP["rag"]` | REQ-008 / AC-8 | line 57; ADR-008 line 409 lists four tables (checked in Step 2) | `tests/tools` (run `check_db_separation.py`) | Verified |
| `scripts/agent/startup_validation.py` | Startup warnings | Remove the `RAG identity-unverified:` prefix from both warnings | REQ-009 / AC-9 | lines 246-261 (checked in Step 2) | `tests/agent/test_startup_validation.py` | Verified |
| `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Consistency doc | Drop the unverifiable-generation class (lines 25, 33, 45, 103) and the identity sentence (line 26) | REQ-010 / AC-10 | lines 25-26, 33, 45, 103 (checked in Step 2) | docs checkers | Verified |
| `docs/21_rag/rag_01_system_overview.md` | Overview | Remove the stale identity-comparison paragraph (line 180) and the `corpus identity` keyword (line 189) | REQ-010 / AC-10 | lines 180, 189 (checked in Step 2) | docs checkers | Verified |
| `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md` | Diagnostics doc | Remove `corpus_generation` from the field sentence | REQ-010 / AC-10 | line 41 (checked in Step 2) | docs checkers | Verified |
| `docs/21_rag/rag_04_dto-models-types.md` | DTO doc | Remove `corpus_generation` from the `SearchDiagnostics` entry | REQ-010 / AC-10 | line 90 (checked in Step 2) | docs checkers | Verified |
| `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` | DB operations doc | Remove `corpus_meta_verified` from the `is_consistent` rule list | REQ-010 / AC-10 | line 50 (checked in Step 2) | docs checkers | Verified |
| `tests/rag/test_corpus_identity.py` | Identity tests | Delete | REQ-006 / AC-6 | 33 references (checked in Step 3) | itself | Verified |
| `tests/rag/test_identity_gate.py` | Identity-gate tests | Delete | REQ-006 / AC-6 | 16 references (checked in Step 3) | itself | Verified |
| `tests/rag/ingestion/test_ingester_index_generation.py` | Index-generation tests | Delete | REQ-004 / AC-4 | 15 references (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_identity.py` | Identity-view tests | Delete | REQ-003 / AC-3 | tests `_identity_payload`, imports `SCHEMA_VERSION` (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` | Endpoint tests | Remove the identity-wiring class that patches `_identity_payload` | REQ-003 / AC-3 | lines 209-227 (checked in Step 3) | itself | Verified |
| `tests/agent/services/test_rag_index_integrity.py` | Maintenance tests | Remove the `corpus_identity()` tests and the extra DDL for the table | REQ-005 / AC-5 | lines 12-13, 79-83, 555, 574 (checked in Step 3) | itself | Verified |
| `tests/rag/ingestion/test_ingester.py` | Ingester tests | Remove the seeded `rag_corpus_meta` DDL and row | REQ-008 / AC-8 | lines 37, 64-71, 105 (checked in Step 3) | itself | Verified |
| `tests/db/test_rag_consistency.py` | Consistency tests | Remove the table seed and `corpus_meta_verified` arguments and tests of the removed class | REQ-007 / AC-7 | lines 76, 183, 612, 658, 1128 (checked in Step 3) | itself | Verified |
| `tests/db/test_db_recovery.py` | Recovery tests | Remove `corpus_meta_verified` from the report fixture | REQ-007 / AC-7 | lines 1117-1120 (checked in Step 3) | itself | Verified |
| `tests/db/test_create_schema.py` | Schema tests | Replace the table-exists test with an absent-table test; drop the fixture DDL | REQ-008 / AC-8 | lines 56, 203-210 (checked in Step 3) | itself | Verified |
| `tests/db/test_recovery_drill.py` | Drill tests | Remove the `rag_corpus_meta` seed insert | REQ-008 / AC-8 | lines 101-104 (checked in Step 3) | itself | Verified |
| `tests/deploy/test_init_db_schema_gate.py` | Fingerprint gate tests | Remove the `ensure_corpus_meta` import and the seed | REQ-006 / AC-6 | lines 39, 122 (checked in Step 3) | itself | Verified |
| `tests/agent/test_startup_validation.py` | Startup tests | Drop the `identity-unverified` assertions | REQ-009 / AC-9 | lines 245-255, 281 (checked in Step 2) | itself | Verified |
| `tests/agent/test_startup.py` | Startup tests | Drop the `identity-unverified` assertions | REQ-009 / AC-9 | lines 554, 643, 657 (checked in Step 2) | itself | Verified |
| `tests/agent/test_startup_severity_classification.py` | Startup tests | Drop the `identity-unverified` assertion | REQ-009 / AC-9 | lines 518, 530 (checked in Step 2) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Line 409 inventory already lists four RAG tables; matches Option B, not edited | REQ-008 |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Schema reference; does not list the table, not edited | REQ-008 |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | An ADR edit that changes a decision needs a new approval record in the same change | REQ-001 |
| `deploy/init_db.sh` | Exact-match fingerprint gate refuses missing and extra tables | REQ-008 |
| `scripts/db/create_schema.py` | Builds the RAG schema from `build_rag_schema_sql`; recreate-only | REQ-008 |
| `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md` | Records the deployed `rag.sqlite` lacking the table | REQ-008 |
| `plans/done/20261111-102935_adrrev013_rag-consistency-policy.md` | Names rmcompat001 as its ordering dependency; its procedures edit `rag_05_07` | REQ-010 |
| `plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md` | Same `ingester.py` and startup warnings | REQ-004, REQ-009 |

## Acceptance Criteria
- AC-1 (REQ-001): ADR-010's Withdrawn bullet states the table, reader, wire field, and diagnostics field were removed; its Withdrawal Approval Record remains `Pending maintainer statement`; `tools/check_adr_preservation.py` reports no ERROR.
- AC-2 (REQ-002): `rg -n "SCHEMA_VERSION|_last_corpus_generation|corpus_generation|compute_local_identity" scripts/rag` returns nothing.
- AC-3 (REQ-003): `rg -n "corpus_identity|_identity_payload" scripts/mcp_servers` returns nothing.
- AC-4 (REQ-004): `rg -n "bump_index_generation|index_generation" scripts tests` returns nothing.
- AC-5 (REQ-005): `RagMaintenanceService` has no `corpus_identity` method.
- AC-6 (REQ-006): both modules and their tests are gone.
- AC-7 (REQ-007): `rg -n "corpus_meta|unverifiable corpus" scripts tests` returns nothing.
- AC-8 (REQ-008): the canonical RAG DDL has no `rag_corpus_meta`; `uv run python tools/check_db_separation.py` passes; a test asserts the table is absent.
- AC-9 (REQ-009): `rg -n "identity-unverified" scripts tests docs` returns nothing; the startup tests pass.
- AC-10 (REQ-010): `rg -n "corpus_identity|rag_corpus_meta|bump_index_generation|compute_local_identity|identity-unverified" scripts tests docs` returns only the preserved ADR-010 historical text and the new decision record; docs checkers pass.
- AC-11: the full test suite passes.

## Tests
- REQ-006: delete the four identity-focused test modules.
- REQ-008: `tests/db/test_create_schema.py` asserts `rag_corpus_meta` is absent from the fresh RAG schema; fingerprint gate tests pass without the seed.
- REQ-007: `tests/db/test_rag_consistency.py` keeps every other fatal-class and degraded-class test unchanged.
- REQ-009: startup tests keep their severity and continue-startup assertions and assert the category and timeout text.
- REQ-002 and REQ-003: the endpoint and diagnostics tests pass without the identity wiring.

## Documentation Impact
- Documentation must be updated (REQ-001, REQ-010): the ADR record, the consistency-checks document, the RAG overview, the diagnostics and DTO documents, and the DB operations document, located through `docs/00_index.md` "Document References by Task". Describe intent and failure behavior only, with no field catalogs (`skills/DESIGN.md`). Run the `routing.md` checkers for `docs/` and for ADR edits.

## Assumptions
- ADR-010 is the right decision record because it introduced the identity contract; ADR-005 and ADR-008 never mention the table. The Issue left this `Needs confirmation`; UNK-01 records it.
- The deployed `rag.sqlite` lacks the table (per `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md`, not re-inspected); a deployed or development file that still carries the table becomes an extra table and is refused by the fingerprint gate until archived and recreated.
- No consumer of the MCP `corpus_identity` wire field exists in the repository (searched `scripts/`, `tests/`, `docs/`); an external reader is not known.
- The three startup tests keep every other assertion; only the prefix assertion is dropped.
- Step 8b overlap judgements: `docs/10_adr/adr_02_06_010_rag-fallback.md` with `plans/20261111-110144_adrrev017_docs-history-wording.md` is compatible (that Plan removes the two Amendment sections and leaves the Withdrawal record untouched; this Plan edits the Withdrawn bullet and the Withdrawal record; line numbers shift, so re-read before editing). `tests/agent/test_startup_validation.py` with `plans/20261111-104147_adrrev015_adr-index-matrix.md` is compatible (that Plan adds unmocked `_check_component_mandatoriness()` tests; this Plan edits the two `identity-unverified` assertions). `scripts/agent/startup_validation.py` and `scripts/rag/ingestion/ingester.py` with `plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md` are a sequencing dependency (recorded in Scope Dependencies): that Plan first removes the gate clause and `REQ-007` reference and the ingester `__del__`, attribute, and `_log_ingest_failure`; this Plan then removes the `identity-unverified` prefix and the bump call.
- Compatible with the in-flight procedure `implementations/20261111-231122_01_scripts_mcp_servers_rag_pipeline_rag_pipeline_server.py.md` (it edits `call_tool`, not `_identity_payload`) and with `implementations/20261112-063813_01_docs_21_rag_rag_05_07-rag-index-consistency-checks.md.md` (a different sentence set; re-read `rag_05_07` before editing).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which ADR should carry the decision record (ADR-005, ADR-008, or ADR-010) | Maintainer preference | Plan uses ADR-010; maintainer may redirect at the approval statement | False |
| UNK-02 | The maintainer's approval statement for the ADR record | The statement | Maintainer writes it per `governance_05`; not written here | False |
| UNK-03 | Whether any operator or external reader depends on the MCP `corpus_identity` field | External usage information | Ask the operator before deploy; none found in the repository | False |
| UNK-04 | The operator's plan and timing for archiving and recreating `/opt/llm/db/rag.sqlite` (its other differences from the current schema are not decided) | Operator decision | Deployment hand-off in Phase 10 | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `scripts/rag/pipeline.py` | Modify | High | 5 | N/A | not applicable (rsynced) |
| `scripts/rag/models_result.py` | Modify | Medium | 2 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | Modify | Medium | 6 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | Modify | Medium | 5 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/ingester.py` | Modify | Medium | 7 | N/A | not applicable (rsynced) |
| `scripts/agent/services/rag_maintenance_service.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/rag/corpus_identity.py` | Delete | Medium | 3 | N/A | not applicable (rsynced) |
| `scripts/rag/identity_gate.py` | Delete | Medium | 2 | N/A | not applicable (rsynced) |
| `scripts/db/rag_consistency_queries.py` | Modify | Medium | 3 | N/A | not applicable (rsynced) |
| `scripts/db/rag_consistency.py` | Modify | High | 6 | N/A | not applicable (rsynced) |
| `scripts/db/models.py` | Modify | Medium | 4 | N/A | not applicable (rsynced) |
| `scripts/db/schema_sql.py` | Modify | High | 18 | N/A | not applicable (rsynced) |
| `tools/check_db_separation.py` | Modify | Low | 13 | N/A | not applicable (rsynced) |
| `scripts/agent/startup_validation.py` | Modify | Medium | 8 | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_01_system_overview.md` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_04_dto-models-types.md` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` | Modify | Low | 6 | N/A | not applicable (rsynced) |
| `tests/rag/test_corpus_identity.py` | Delete | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_identity_gate.py` | Delete | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/ingestion/test_ingester_index_generation.py` | Delete | Low | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_identity.py` | Delete | Low | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/services/test_rag_index_integrity.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/ingestion/test_ingester.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/db/test_rag_consistency.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/db/test_db_recovery.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/db/test_create_schema.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/db/test_recovery_drill.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/deploy/test_init_db_schema_gate.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_validation.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_severity_classification.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Consumer map (text search, one pass over `scripts tests docs tools config registry deploy skills rules`): `corpus_identity.py` is imported by `pipeline` (via `identity_gate`), `ingester`, `rag_maintenance_service`, and `tests/deploy/test_init_db_schema_gate.py`; `identity_gate.py` by `pipeline` and `rag_pipeline_server`; `SCHEMA_VERSION` by `rag_pipeline_server` and the identity test only; `corpus_meta_verified` by `rag_consistency.py`, `models.py`, two tests, and `db_06`. Every one is a target row. The scan is text-only; no dynamic reference to these names is expected.
- Wire contract: the MCP `corpus_identity` field was documented as an additive wire field; removing it is intended and recorded in the ADR record. No alias is kept.
- Persisted schema check (`rules/persisted-schema-change.md`): item 1 (version stores) and 5, 6 (migration registry) do not apply, because the RAG database has no registry and is recreate-only. Item 2 applies: removing the table moves the RAG fingerprint; `deploy/init_db.sh` refuses any file that differs, so a file with the old table needs archive and recreate, and no migration step is registered by design (`compatrm001`). Item 3 (rebuild cascade) and item 4 (`NOT NULL` write path) do not apply to a table drop; `rg -n "INSERT (OR \w+ )?INTO rag_corpus_meta" scripts tests` lists the writers, all target rows. Item 7: rows with an old meaning do not apply; the single row is dropped with the table. `tools/check_db_separation.py` verifies ownership after the change.
- Fatal class removal: the consistency check loses one fatal class because the thing it verified no longer exists; schema inconsistency stays covered by the fingerprint gate (ADR-004 integrity failures). No other severity changes, and no other Fatal abort is relaxed.
- Import architecture: `lint-imports` baseline 6 contracts kept; the change deletes imports and modules only.
- Complexity: `check_rag_consistency` is C (18) and only shrinks. `vulture` and `bandit` baselines (recorded in `plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md` Design): findings are pre-existing; deletions add none.
- Operational: no port, MCP server registration, or process change; `ss` and `fuser` not run (N/A). The deployed `rag.sqlite` shape was not inspected (production). `pip-audit` N/A.
- Historical: churn above from `git log --since=30.days`; `schema_sql.py` (18) and `check_db_separation.py` (13) are the busiest targets; bus factor not measured.

## Implementation steps
1. **Phase 1: Decision record**
   - [ ] Extend the Withdrawn bullet and the Withdrawal Approval Record; leave approval pending (REQ-001; `docs/10_adr/adr_02_06_010_rag-fallback.md`)
2. **Phase 2: Pipeline diagnostics**
   - [ ] Remove identity use and the `corpus_generation` field (REQ-002; `scripts/rag/pipeline.py`, `scripts/rag/models_result.py`)
   - [ ] Remove the field mention from the two docs (REQ-010; `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md`, `docs/21_rag/rag_04_dto-models-types.md`)
3. **Phase 3: MCP server identity view**
   - [ ] Delete `_identity_payload` and the wire field (REQ-003; `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`)
   - [ ] Delete and trim tests (REQ-003; `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_identity.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`)
4. **Phase 4: Ingester**
   - [ ] Remove the bump call (REQ-004; `scripts/rag/ingestion/ingester.py`)
   - [ ] Delete the index-generation tests (REQ-004; `tests/rag/ingestion/test_ingester_index_generation.py`)
5. **Phase 5: Maintenance wrapper**
   - [ ] Remove the wrapper and its tests (REQ-005; `scripts/agent/services/rag_maintenance_service.py`, `tests/agent/services/test_rag_index_integrity.py`)
6. **Phase 6: Delete identity modules**
   - [ ] Delete the modules and their tests (REQ-006; `scripts/rag/corpus_identity.py`, `scripts/rag/identity_gate.py`, `tests/rag/test_corpus_identity.py`, `tests/rag/test_identity_gate.py`)
   - [ ] Remove the import and seed (REQ-006; `tests/deploy/test_init_db_schema_gate.py`)
7. **Phase 7: Consistency class removal**
   - [ ] Remove the probe, the finding, the report field (REQ-007; `scripts/db/rag_consistency_queries.py`, `scripts/db/rag_consistency.py`, `scripts/db/models.py`)
   - [ ] Update tests and the doc rule list (REQ-007, REQ-010; `tests/db/test_rag_consistency.py`, `tests/db/test_db_recovery.py`, `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`)
8. **Phase 8: DDL and inventory**
   - [ ] Remove the table and the inventory entry (REQ-008; `scripts/db/schema_sql.py`, `tools/check_db_separation.py`)
   - [ ] Update schema, drill, and ingester fixtures (REQ-008; `tests/db/test_create_schema.py`, `tests/db/test_recovery_drill.py`, `tests/rag/ingestion/test_ingester.py`)
9. **Phase 9: Startup warnings and documents**
   - [ ] Remove the prefix (REQ-009; `scripts/agent/startup_validation.py`, `tests/agent/test_startup_validation.py`, `tests/agent/test_startup.py`, `tests/agent/test_startup_severity_classification.py`)
   - [ ] Update the documents (REQ-010; `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`, `docs/21_rag/rag_01_system_overview.md`)
10. **Phase 10: Deployment and verification**
    - [ ] Hand off to `skills/deploy/SKILL.md` after the change is committed and pushed; deploying is the user's decision (approval gate). State the prerequisite that an existing `rag.sqlite` with the old table must be archived and recreated by the operator (UNK-04). Run the acceptance searches, validation sequence, and docs and ADR checkers (REQ-001 to REQ-010)

### Release units
**Unit**: corpus-meta-removal | **Phases**: 6, 7, 8 | **Reason**: deleting `corpus_identity.py` breaks the gate test's import until its seed goes; removing that seed breaks the fatal-class tests until the class goes; removing the class before the DDL is safe but the fixtures that seed the table must change with the DDL.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| RAG pipeline and diagnostics | Unit | `uv run pytest tests/rag` | Pass without identity code |
| MCP server | Unit | `uv run pytest tests/mcp_servers/rag_pipeline` | Pass; no `corpus_identity` key |
| Consistency, schema, recovery | Unit | `uv run pytest tests/db tests/deploy tests/agent/services/test_rag_index_integrity.py` | Pass; table absent |
| Startup | Unit | `uv run pytest tests/agent/test_startup_validation.py tests/agent/test_startup.py tests/agent/test_startup_severity_classification.py` | Pass without the prefix assertion |
| Ownership and DDL | Static | `uv run python tools/check_db_separation.py` | Pass |
| Changed Python files | Static | `uv run ruff format`, `ruff check`, `mypy --no-namespace-packages`, `lint-imports`, `bandit -r scripts/ -c pyproject.toml`, `python tools/check_module_size.py` | No new finding |
| Whole change | Search | the AC-2 to AC-10 `rg` commands | Match the criteria |
| Documents and ADR | Docs | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag` and `--domain db`, `check_adr_preservation.py`, `check_adr_structure.py`, `check_adr_reference.py`, `check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py` | No findings |
| Coverage | Coverage | diff-cover sequence in `rules/toolchain.md` section 7 | At or above the threshold |

## Risks
- **Risk**: An operator's `rag.sqlite` still carries the table and the fingerprint gate refuses it → **Mitigation**: stated in the Phase 10 hand-off and UNK-04; the refusal is the existing archive-and-recreate error, and the deployed file is reported to lack the table already.
- **Risk**: An external reader depends on the MCP `corpus_identity` field → **Mitigation**: UNK-03; none found in the repository; the removal is recorded in the ADR record.
- **Risk**: Another procedure edits `rag_05_07` or `rag_pipeline_server.py` first → **Mitigation**: re-read both files before editing; the regions differ; `tools/check_plan_target_overlaps.py` was run at freeze.
- **Risk**: The ADR record is read as an approved decision → **Mitigation**: the approval line stays `Pending maintainer statement`; the implementer writes no approval text.
- **Risk**: Removing a Fatal finding class is mistaken for relaxing a Fatal abort → **Mitigation**: the Design states the class verified only the removed table; the fingerprint gate covers schema inconsistency.
- **Risk**: Deleting `total_success` or the sum alters the ingestion summary → **Mitigation**: the variable is also read at `ingester.py:200`, so only the bump condition is removed.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record the Option B decision in ADR-010 (approval pending) | Pending | — | — | |
| 2 | Remove corpus generation from the pipeline and two docs | Pending | — | — | |
| 3 | Remove the MCP server identity view and its tests | Pending | — | — | |
| 4 | Remove the ingester bump call and its tests | Pending | — | — | |
| 5 | Remove the maintenance wrapper and its tests | Pending | — | — | |
| 6 | Delete the identity modules and their tests | Pending | — | — | Release unit corpus-meta-removal with steps 7, 8 |
| 7 | Remove the unverifiable-generation consistency class | Pending | — | — | Release unit corpus-meta-removal with steps 6, 8 |
| 8 | Remove the DDL table, the inventory entry, and fixtures | Pending | — | — | Release unit corpus-meta-removal with steps 6, 7 |
| 9 | Remove the startup prefix and update the documents | Pending | — | — | |
| 10 | Deployment hand-off and verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261112-223151_01_docs_10_adr_adr_02_06_010_rag-fallback.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261112-223151_02_scripts_rag_pipeline.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261112-223151_03_scripts_rag_models_result.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261112-223151_04_scripts_mcp_servers_rag_pipeline_rag_pipeline_server.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261112-223151_05_scripts_mcp_servers_rag_pipeline_rag_pipeline_models.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261112-223151_06_scripts_rag_ingestion_ingester.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261112-223151_07_scripts_agent_services_rag_maintenance_service.py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261112-223151_08_scripts_rag_corpus_identity.py.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261112-223151_09_scripts_rag_identity_gate.py.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261112-223151_10_scripts_db_rag_consistency_queries.py.md` | 7 | Procedure | Pending | — | — |
| `implementations/20261112-223151_11_scripts_db_rag_consistency.py.md` | 7 | Procedure | Pending | — | — |
| `implementations/20261112-223151_12_scripts_db_models.py.md` | 7 | Procedure | Pending | — | — |
| `implementations/20261112-223151_13_scripts_db_schema_sql.py.md` | 8 | Procedure | Pending | — | — |
| `implementations/20261112-223151_14_tools_check_db_separation.py.md` | 8 | Procedure | Pending | — | — |
| `implementations/20261112-223151_15_scripts_agent_startup_validation.py.md` | 9 | Procedure | Pending | — | — |
| `implementations/20261112-223151_16_docs_21_rag_rag_05_07-rag-index-consistency-checks.md.md` | 9 | Procedure | Pending | — | — |
| `implementations/20261112-223151_17_docs_21_rag_rag_01_system_overview.md.md` | 9 | Procedure | Pending | — | — |
| `implementations/20261112-223151_18_docs_21_rag_rag_03_03_query_pipeline-context-and-diagnostics.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261112-223151_19_docs_21_rag_rag_04_dto-models-types.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261112-223151_20_docs_41_db_db_06_api_and_operations-maintenance-and-rotation.md.md` | 7 | Procedure | Pending | — | — |
| `implementations/20261112-223151_23_tests_rag_ingestion_test_ingester_index_generation.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261112-223151_24_tests_mcp_servers_rag_pipeline_test_rag_pipeline_server_identity.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261112-223151_25_tests_mcp_servers_rag_pipeline_test_rag_pipeline_server_endpoints.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261112-223151_28_tests_db_test_rag_consistency.py.md` | 7 | Procedure | Pending | — | — |
| `implementations/20261112-223151_31_tests_db_test_recovery_drill.py.md` | 8 | Procedure | Pending | — | — |
| `implementations/20261112-223151_32_tests_deploy_test_init_db_schema_gate.py.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261112-223151_34_tests_agent_test_startup.py.md` | 9 | Procedure | Pending | — | — |
| `implementations/20261112-223151_35_tests_agent_test_startup_severity_classification.py.md` | 9 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261112-120011
- **Related target files**: `docs/10_adr/adr_02_06_010_rag-fallback.md`, `scripts/rag/pipeline.py`, `scripts/rag/models_result.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`, `scripts/rag/ingestion/ingester.py`, `scripts/agent/services/rag_maintenance_service.py`, `scripts/rag/corpus_identity.py`, `scripts/rag/identity_gate.py`, `scripts/db/rag_consistency_queries.py`, `scripts/db/rag_consistency.py`, `scripts/db/models.py`, `scripts/db/schema_sql.py`, `tools/check_db_separation.py`, `scripts/agent/startup_validation.py`, `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`, `docs/21_rag/rag_01_system_overview.md`, `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md`, `docs/21_rag/rag_04_dto-models-types.md`, `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`, `tests/rag/test_corpus_identity.py`, `tests/rag/test_identity_gate.py`, `tests/rag/ingestion/test_ingester_index_generation.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_identity.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`, `tests/agent/services/test_rag_index_integrity.py`, `tests/rag/ingestion/test_ingester.py`, `tests/db/test_rag_consistency.py`, `tests/db/test_db_recovery.py`, `tests/db/test_create_schema.py`, `tests/db/test_recovery_drill.py`, `tests/deploy/test_init_db_schema_gate.py`, `tests/agent/test_startup_validation.py`, `tests/agent/test_startup.py`, `tests/agent/test_startup_severity_classification.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; ADR-010 lines 252, 292-294 | `docs/10_adr/adr_02_06_010_rag-fallback.md` | 1 | AC-1 | `tools/check_adr_preservation.py` | Explicit in issue |
| REQ-002 | Implementation Intent (Option B); `pipeline.py:201,262` | `scripts/rag/pipeline.py` | 2 | AC-2 | `tests/rag` | Confirmed by repository evidence |
| REQ-002 | Implementation Intent; `models_result.py:91` | `scripts/rag/models_result.py` | 2 | AC-2 | `tests/rag` | Confirmed by repository evidence |
| REQ-003 | Implementation Intent; `rag_pipeline_server.py:73-114` | `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | 3 | AC-3 | server tests | Confirmed by repository evidence |
| REQ-003 | Implementation Intent; `rag_pipeline_models.py:259` | `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | 3 | AC-3 | server tests | Confirmed by repository evidence |
| REQ-003 | Testing Expectations | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_identity.py` | 3 | AC-3 | deletion | Confirmed by repository evidence |
| REQ-003 | Testing Expectations; endpoints lines 209-227 | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` | 3 | AC-3 | server tests | Confirmed by repository evidence |
| REQ-004 | Background; `ingester.py:20,190` | `scripts/rag/ingestion/ingester.py` | 4 | AC-4 | `tests/rag/ingestion` | Confirmed by repository evidence |
| REQ-004 | Testing Expectations | `tests/rag/ingestion/test_ingester_index_generation.py` | 4 | AC-4 | deletion | Explicit in issue |
| REQ-005 | Background; `rag_maintenance_service.py:16,60-78` | `scripts/agent/services/rag_maintenance_service.py` | 5 | AC-5 | `tests/agent/services` | Confirmed by repository evidence |
| REQ-005 | Testing Expectations; integrity test lines 555, 574 | `tests/agent/services/test_rag_index_integrity.py` | 5 | AC-5 | integrity tests | Explicit in issue |
| REQ-006 | Implementation Intent | `scripts/rag/corpus_identity.py` | 6 | AC-6 | acceptance search | Explicit in issue |
| REQ-006 | Implementation Intent | `scripts/rag/identity_gate.py` | 6 | AC-6 | acceptance search | Explicit in issue |
| REQ-006 | Testing Expectations | `tests/rag/test_corpus_identity.py` | 6 | AC-6 | deletion | Explicit in issue |
| REQ-006 | Derived from `identity_gate` consumers; `test_identity_gate.py` | `tests/rag/test_identity_gate.py` | 6 | AC-6 | deletion | Derived from confirmed evidence |
| REQ-006 | `test_init_db_schema_gate.py:39` imports the module | `tests/deploy/test_init_db_schema_gate.py` | 6 | AC-6 | gate tests | Confirmed by repository evidence |
| REQ-007 | Background; `rag_consistency_queries.py:283-300` | `scripts/db/rag_consistency_queries.py` | 7 | AC-7 | `tests/db` | Confirmed by repository evidence |
| REQ-007 | Background; `rag_consistency.py:374-447` | `scripts/db/rag_consistency.py` | 7 | AC-7 | `tests/db` | Confirmed by repository evidence |
| REQ-007 | `models.py:118` | `scripts/db/models.py` | 7 | AC-7 | `tests/db` | Confirmed by repository evidence |
| REQ-007 | `test_rag_consistency.py` lines 76, 183, 612 | `tests/db/test_rag_consistency.py` | 7 | AC-7 | `tests/db` | Confirmed by repository evidence |
| REQ-007 | `test_db_recovery.py:1117` | `tests/db/test_db_recovery.py` | 7 | AC-7 | `tests/db` | Confirmed by repository evidence |
| REQ-008 | Testing Expectations; `schema_sql.py:47-56` | `scripts/db/schema_sql.py` | 8 | AC-8 | `tests/db/test_create_schema.py` | Explicit in issue |
| REQ-008 | `check_db_separation.py:57`; ADR-008 line 409 | `tools/check_db_separation.py` | 8 | AC-8 | `check_db_separation.py` | Confirmed by repository evidence |
| REQ-008 | Testing Expectations (schema test) | `tests/db/test_create_schema.py` | 8 | AC-8 | itself | Explicit in issue |
| REQ-008 | `test_recovery_drill.py:101-104` | `tests/db/test_recovery_drill.py` | 8 | AC-8 | `tests/db` | Confirmed by repository evidence |
| REQ-008 | `test_ingester.py:64-71,105` own DDL copy | `tests/rag/ingestion/test_ingester.py` | 8 | AC-8 | `tests/rag/ingestion` | Confirmed by repository evidence |
| REQ-009 | `startup_validation.py:246-261`; startup tests | `scripts/agent/startup_validation.py` | 9 | AC-9 | startup tests | Confirmed by repository evidence |
| REQ-009 | `test_startup_validation.py:255,281` | `tests/agent/test_startup_validation.py` | 9 | AC-9 | itself | Confirmed by repository evidence |
| REQ-009 | `test_startup.py:643,657` | `tests/agent/test_startup.py` | 9 | AC-9 | itself | Confirmed by repository evidence |
| REQ-009 | `test_startup_severity_classification.py:530` | `tests/agent/test_startup_severity_classification.py` | 9 | AC-9 | itself | Confirmed by repository evidence |
| REQ-010 | Documentation Impact; `rag_05_07` lines 25-26, 33, 45, 103 | `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | 9 | AC-10 | docs checkers | Explicit in issue |
| REQ-010 | `rag_01_system_overview.md:180,189` | `docs/21_rag/rag_01_system_overview.md` | 9 | AC-10 | docs checkers | Derived from confirmed evidence |
| REQ-010 | `rag_03_03...:41` | `docs/21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md` | 2 | AC-10 | docs checkers | Derived from confirmed evidence |
| REQ-010 | `rag_04...:90` | `docs/21_rag/rag_04_dto-models-types.md` | 2 | AC-10 | docs checkers | Derived from confirmed evidence |
| REQ-010 | `db_06...:50` | `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` | 7 | AC-10 | docs checkers | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261112-223151 -->
