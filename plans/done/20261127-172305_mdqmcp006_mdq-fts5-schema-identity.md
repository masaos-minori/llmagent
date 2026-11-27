## Goal
- Prove MDQ readiness against the real FTS5 definition and trigger synchronization, publish a canonical MDQ schema identity, include that identity in execution snapshots, and align the recreation runbook so an operator has one authoritative sequence.

## Priority
High

## Scope
- **In-Scope**:
  - Readiness compares the actual stored FTS5 definition (columns, tokenizer, options) and the trigger SQL, not table and trigger names.
  - Functional insert, update, and delete synchronization probes on a scratch apply of the canonical DDL; the live database is only inspected.
  - A canonical `mdq_schema_id` computed from the single canonical DDL source and published through the health capability metadata.
  - The execution snapshot gains the MDQ schema identity as a component.
  - Documents or chunks with an unexpectedly empty FTS index are not ready.
  - The readiness conditions map onto the existing closed capability-state vocabulary.
  - The mdq recreation runbook is aligned with the identity and readiness conditions.
- **Out-of-Scope**: file fingerprint columns (mdqmcp004); transaction ownership (mdqmcp005); any ADR decision change or approval record; new health vocabulary (owner decision required).
- **Dependencies**: depends on the mdqmcp004 plan (the canonical columns the identity is computed from) and the mdqmcp005 plan (the transaction the readiness postconditions describe); uses the error classification of the mdqmcp002 plan and the readiness reporting of the mdqmcp001 plan. Blocks mdqmcp008 and mdqmcp010.
  - **Depends on**: `plans/20261127-170412_mdqmcp004_mdq-file-identity-stale.md` | all | the canonical DDL the identity is computed from changes there; computing the identity before that plan lands would freeze an identity that the same work then invalidates
  - **Depends on**: `plans/20261127-171503_mdqmcp005_mdq-transaction-atomicity.md` | all | the trigger synchronization readiness proves is only meaningful over the single file transaction that plan establishes
  - **Depends on**: `plans/20261127-160114_mdqmcp001_mdq-server-boundary.md` | all | readiness is reported through the capability-state vocabulary and the non-sensitive health shape that plan defines; this Plan adds no new vocabulary

## Background
Source issue: `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md` (consolidated MDQ MCP backlog, Issue 6).

Adversarial verification against current source (evidence revision in Traceability):
- Confirmed: `scripts/mcp_servers/mdq/db_schema.py` defines `chunks_fts` as an FTS5 virtual table (lines 58-67) and the three sync triggers (lines 70-92), and passes the same statements to the shared fingerprint as the canonical shape (lines 103-109, 132-134).
- Confirmed: the shared fingerprint compares virtual tables by name only (`scripts/shared/schema_fingerprint.py` docstring lines 12-20; `_is_name_only`, `_name_only_names`, and the skip in `_raise_first_difference` lines 308-310), so a plain table named `chunks_fts` passes `assert_matches`. The behavior is pinned by `tests/shared/test_schema_fingerprint.py` (lines 171-185).
- Confirmed: `scripts/mcp_servers/mdq/health_check.py` checks table names (lines 64-69) and trigger names (lines 71-79) only, then runs one FTS probe query (lines 81-87). A plain table named `chunks_fts` with a `chunks_fts` column passes readiness — the health test fixtures themselves build a plain table (`tests/mcp_servers/mdq/test_mdq_health.py` line 60, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` lines 68-79). No-op triggers pass because only their names are compared.
- Corrected: the issue's claim that trigger drift is undetected holds for readiness, not for the fingerprint gate — `scripts/shared/schema_fingerprint.py::_triggers()` compares normalized trigger SQL for non-virtual tables, so a no-op trigger on `chunks` is refused by `assert_matches`. The gap is readiness, which never compares trigger SQL.
- Confirmed: an empty FTS index while documents or chunks exist is reported as a posture WARNING, not as not ready (`scripts/mcp_servers/mdq/mdq_security_validation.py` lines 218-234); `ready` is derived from the dependency map alone (`scripts/mcp_servers/health_response.py` line 65).
- Confirmed: the execution snapshot has no MDQ identity. `scripts/shared/execution_snapshot.py` reads `user_version` from the file header for `rag`, `session`, and `workflow` only (lines 13-15, 44-50, 57-66); `mdq.sqlite` is absent from the path map, and ADR-008 forbids version stamping, so there is no header field to read.
- Corrected: the closed capability-state vocabulary is `ok`, `degraded`, `unavailable` (`scripts/shared/mcp_health_contract.py` lines 43-54) and the degraded reason codes are a closed set (lines 30-39). The issue's five readiness names cannot be added as states without a contract change; they are recorded as internal condition names mapped onto the existing vocabulary, and the vocabulary change itself is an unknown requiring the contract owner.
- Corrected: the recovery wording is not contradictory in the ADR itself — ADR-008 Decision Detail 22 (archive and recreate, no in-place migration, approved 2026-11-24 as AAL-025) and the derived-store row for `mdq.sqlite` in `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` section 8e (delete the file and re-index) describe the same operation at different granularity. The gap is that the mdq path has no re-index verification step and no single named runbook; the runbook already exists in db_03 section 8e and db_07 section 11 and is aligned, not redefined (see the mdqmcp004 plan). The ADR is not modified here: an ADR decision change needs a maintainer approval record.

## Problem
Readiness can report healthy over a plain table named `chunks_fts` and no-op triggers; schema identity is absent from execution snapshots; and an operator has no single named recovery sequence for a drifted MDQ store.

## Reason for Change
A search service that reports ready while FTS is broken or desynchronized gives operators no reliable signal, and replay equality cannot see a schema change in the MDQ store.

## Implementation Intent
Ready only when the expected FTS5 definition exists and insert, update, and delete synchronization work; a stable identity computed from the canonical DDL is published safely and included in execution snapshots; one documented stop, archive or recreate, re-index, verify, restart sequence.

## Requirements
- `REQ-001`: readiness compares the stored FTS5 definition (columns, tokenizer, options) and the trigger SQL, not names.
- `REQ-002`: functional insert, update, and delete synchronization probes prove the trigger logic; the live database is only inspected, never written by a readiness probe.
- `REQ-003`: a canonical `mdq_schema_id` is computed from the single canonical DDL source (tables, FTS5 definition, indexes, constraints, foreign keys, triggers) and published through the health body `details` map; the capability entry carries only state and reason code, so no metadata field is added.
- `REQ-004`: the execution snapshot includes the MDQ schema identity as a component.
- `REQ-005`: documents or chunks with an unexpectedly empty FTS index are not ready.
- `REQ-006`: the readiness conditions (healthy, rebuild in progress, degraded, inconsistent, failed) map onto the existing closed capability-state vocabulary; no new vocabulary is invented.
- `REQ-007`: the mdq recreation runbook is one named sequence — stop, archive or recreate, re-index, verify, restart — aligned with the identity and the readiness conditions.

## Implementation Target Files
**Freeze status**: Frozen — `issue-to-plan` Step 8's Implementation Target Files
Validation passed for every row on 20261127; see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze).
Amended 2026-11-28 (scope): added scripts/shared/mdq_schema.py — The shared-is-leaf import-linter contract forbids scripts/shared/execution_snapshot.py from importing mcp_servers.mdq.db_schema, so the canonical DDL and its identity hash must live in a shared module that both the mdq schema entry point and the snapshot builder import (maintainer decision, 2026-11-28)
Amended 2026-11-28 (fallout): added tests/mcp_servers/mdq/test_mdq_security_validation.py — The assertion that pins the current WARNING status lives in this file, not in tests/mcp_servers/mdq/test_mdq_health_posture.py, so the status change REQ-005 requires breaks it; the file must be updated to keep the suite passing (fallout, reported after amending)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/db_schema.py` | Modify | Keep `_CREATE_STATEMENTS` as the single canonical source and add the canonical `mdq_schema_id` computation over the normalized DDL | REQ-003, REQ-001, AC-2 | `_CREATE_STATEMENTS` (lines 103-109) is already the single source passed to `assert_matches` (lines 132-134); no identity value is produced today | `tests/mcp_servers/mdq/test_mdq_schema_identity.py` | Verified |
| `scripts/shared/schema_fingerprint.py` | Modify | Compare an FTS5 virtual table by its normalized stored DDL text (columns, tokenizer, options) instead of name only; keep the name-only treatment for extension-backed virtual tables and the shadow-table omission | REQ-001, AC-2 | The docstring states virtual tables are compared by name only (lines 12-20); `_raise_first_difference` skips every name-only entry (lines 308-310), so a plain table named `chunks_fts` passes | `tests/shared/test_schema_fingerprint.py` | Verified |
| `scripts/shared/execution_snapshot.py` | Modify | Add the MDQ schema identity as a snapshot component, read without opening a sqlite3 connection | REQ-004, AC-3 | `COMPONENT_KEYS` (lines 44-50) has no mdq entry; `_DB_PATH_KEYS` (lines 57-66) omits mdq; the module reads the `user_version` header only (lines 13-15) | `tests/shared/test_execution_snapshot.py` | Verified |
| `scripts/mcp_servers/mdq/health_check.py` | Modify | Readiness compares the stored FTS5 definition and trigger SQL, runs the functional synchronization probe, publishes the identity through the health body `details` map, and reports the readiness conditions through the closed capability vocabulary | REQ-001, REQ-002, REQ-003, REQ-006, AC-1, AC-2 | Table names are checked at lines 64-69 and trigger names at lines 71-79; only one probe query runs (lines 81-87); `ready` is derived from the dependency map in `scripts/mcp_servers/health_response.py` (line 65) | `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`, `tests/mcp_servers/mdq/test_mdq_fts_schema.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_security_validation.py` | Modify | An empty FTS index while documents or chunks exist becomes a not-ready finding instead of a WARNING | REQ-005, AC-4 | `_index_check()` returns `SecurityCheckStatus.WARNING` with `REASON_DEPENDENCY_UNREACHABLE` (lines 218-234) | `tests/mcp_servers/mdq/test_mdq_health_posture.py` | Verified |
| `tests/mcp_servers/mdq/test_mdq_fts_schema.py` | Create | New file: readiness refuses a plain table named `chunks_fts`, tokenizer, column, and option drift, and no-op triggers | REQ-001, AC-1, AC-2 | Does not exist; `tests/mcp_servers/mdq/` holds 35 test files and none compares the stored FTS5 definition | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_fts_trigger_sync.py` | Create | New file: functional insert, update, and delete probes against a scratch apply of the canonical DDL | REQ-002, AC-2 | Does not exist; the only FTS trigger-sync tests are the rag domain tests in `tests/rag/test_fts_sync.py`, which use a different schema | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_schema_identity.py` | Create | New file: identity stability across formatting, identity change on a schema change, and the snapshot component | REQ-003, REQ-004, AC-3 | Does not exist; `tests/shared/test_execution_snapshot.py` pins the component set at line 103 | itself | Verified |
| `tests/shared/test_schema_fingerprint.py` | Modify | The name-only virtual-table pins move to the FTS5 text comparison; the extension-backed name-only case stays pinned | REQ-001, AC-2 | `tests/shared/test_schema_fingerprint.py` lines 171-185 pin the name-only treatment for `chunks_vec` and `chunks_fts` | itself | Verified |
| `tests/shared/test_execution_snapshot.py` | Modify | The component set and the mismatch naming gain the mdq identity | REQ-004, AC-3 | The component set is asserted at line 103 and `schema_versions` at lines 108-125 | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_health.py` | Modify | Fixtures move from a plain table named `chunks_fts` to the real FTS5 definition; the readiness assertions follow | REQ-001, AC-1 | The fixture builds a plain table named `chunks_fts` (line 60) with a `chunks_fts` column (line 68) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` | Modify | The plain-table fixtures and the corrupt-FTS5 case move onto the definition comparison; the key-presence assertions stay | REQ-001, REQ-006, AC-1 | Plain-table fixtures at lines 68-79, 128-136, 165-173; the corrupt case is `test_fts5_query_failure_returns_ready_false` (line 551) on the fixture at lines 219-223, and it passes today because the probe query fails on the missing `chunks_fts` column, not because the stored definition is compared | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_health_posture.py` | Modify | The bind gate gains the not-validated case for an empty FTS index over rows; the WARNING assertion itself is not in this file | REQ-005, AC-4 | The bind gate asserts the shipped posture is validated (line 34); the empty-FTS-index WARNING assertion is in `tests/mcp_servers/mdq/test_mdq_security_validation.py` line 279 (amended row 19), so this file only gains the not-validated bind case | itself | Verified |
| `tests/mcp_servers/mdq/test_db_schema.py` | Modify | The canonical-shape and mismatch-refusal assertions cover the FTS5 definition comparison | REQ-001, REQ-003, AC-2 | The file pins table names (lines 41, 82) and the mismatch refusal by dropping `content_hash` (line 124) | itself | Verified |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | Document what readiness actually guarantees, the identity, and the readiness-condition mapping | REQ-001, REQ-003, REQ-006, AC-1, AC-2 | The doc has no readiness-guarantee or identity statement today | `uv run python tools/check_docs_content_policy.py` | Verified |
| `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md` | Modify | Record the readiness conditions as the documented mapping onto the closed capability vocabulary; no new vocabulary is added | REQ-006, AC-4 | The doc owns the closed degraded reason-code vocabulary referenced by `scripts/shared/mcp_health_contract.py` (lines 30-39) | `uv run python tools/check_docs_content_policy.py` | Verified |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Modify | State the FTS5 definition comparison and align the mdq runbook rows with the identity and the readiness conditions | REQ-001, REQ-007, AC-4 | Section 8e owns the per-store archive-and-recreate table and the mdq row has no re-index verification step | `uv run python tools/generate_reference_table.py --check` | Verified |
| `docs/41_db/db_09_mcp_dedup_and_execution_snapshot.md` | Modify | Document the MDQ schema identity as a snapshot component | REQ-004, AC-3 | The doc states "five component keys" (line 159) and lists them without mdq; the code lists the components in the module docstring (lines 7-21) and `COMPONENT_KEYS` (lines 44-50) | `uv run python tools/generate_reference_table.py --check` | Verified |
| `scripts/shared/mdq_schema.py` | New file: own the canonical mdq DDL text and the normalized-DDL identity computation, so the shared snapshot builder can read the identity without importing the mdq layer | The shared-is-leaf import-linter contract forbids scripts/shared/execution_snapshot.py from importing mcp_servers.mdq.db_schema, so the canonical DDL and its identity hash must live in a shared module that both the mdq schema entry point and the snapshot builder import (maintainer decision, 2026-11-28) | REQ-003 / N/A: none cites REQ-003 | Precedent: scripts/shared/mcp_dedup_schema.py owns canonical DDL in the shared layer (docs/41_db/db_08_active_databases.md line 70); .importlinter contract shared-is-leaf (lines 20-28) forbids shared importing mcp_servers or db | `tests/mcp_servers/mdq/test_mdq_schema_identity.py` | Verified |
| `tests/mcp_servers/mdq/test_mdq_security_validation.py` | The empty-FTS-index assertion moves from WARNING to FAILED, since only FAILED blocks Ready | The assertion that pins the current WARNING status lives in this file, not in tests/mcp_servers/mdq/test_mdq_health_posture.py, so the status change REQ-005 requires breaks it; the file must be updated to keep the suite passing (fallout, reported after amending) | REQ-005 / N/A: none cites REQ-005 | test_empty_index_over_documents_is_a_warning asserts SecurityCheckStatus.WARNING at line 279; scripts/shared/security/result_dto.py line 98 states only FAILED blocks Ready | itself | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.
- Write every `File Path` cell, every `tests/...py` path in `Related Tests`, and every path in
  `Implementation steps` in backticks: `tools/close_procedures_batch.py` and the companion check read
  only backticked paths. `uv run python tools/backtick_plan_related_tests.py plans/{filename}.md`
  normalizes a Plan, and `tools/check_workitem_structure.py` reports a plain path
  (`plain-path-citation`).

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/mcp_health_contract.py` | The closed capability-state and reason-code vocabularies the readiness conditions must map onto; read to confirm no vocabulary change is needed | REQ-006, UNK-02 |
| `scripts/mcp_servers/health_response.py` | Owns the `ready` derivation the readiness conditions feed | REQ-006 |
| `docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md` | Decision Detail 22 and the recorded AAL-024/AAL-025 approvals; read to confirm no ADR decision change is needed — not modified | REQ-007, UNK-03 |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Section 11 owns the recreation procedure the runbook aligns with; the mdq steps are added by the mdqmcp004 plan, so this Plan only cross-references them | REQ-007 |
| `tests/rag/test_fts_sync.py` | The existing FTS5 trigger-sync pattern to follow for the mdq probe | REQ-002 |

## Acceptance Criteria
- `AC-1` (REQ-001): a plain table named `chunks_fts` and no-op triggers cannot pass readiness.
- `AC-2` (REQ-001, REQ-002, REQ-003): tokenizer, column, option, and trigger drift are detected; FTS synchronization is verified functionally; the identity changes only when the canonical shape changes.
- `AC-3` (REQ-004): execution snapshots change when the MDQ schema identity changes.
- `AC-4` (REQ-005, REQ-006, REQ-007): an empty FTS index with rows present is not ready; the readiness conditions map onto the closed vocabulary; one authoritative runbook exists and the docs align with it.

## Tests
- Real FTS5 integration tests for a plain table, no-op trigger, tokenizer, column, and option drift; insert, update, and delete probes (REQ-001, REQ-002; `tests/mcp_servers/mdq/test_mdq_fts_schema.py`, `tests/mcp_servers/mdq/test_mdq_fts_trigger_sync.py`).
- Execution-snapshot identity tests (REQ-004; `tests/shared/test_execution_snapshot.py`, `tests/mcp_servers/mdq/test_mdq_schema_identity.py`).
- Readiness and posture agreement, including the preserved health keys (REQ-005, REQ-006; `tests/mcp_servers/mdq/test_mdq_health.py`, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`, `tests/mcp_servers/mdq/test_mdq_health_posture.py`).
- A scripted recovery verification per the aligned runbook on a scratch database (REQ-007; never against a database under `/opt/llm/`).
- Run ruff, mypy, the fingerprint and docs checkers, and the full test suite (`rules/toolchain.md` sequence via `uv run python tools/run_validation_gates.py`).

## Documentation Impact
Yes. Per `docs/00_index.md` "Document References by Task":
- MCP server spec row drives `docs/22_mcp/mcp_04_04_mdq.md` (readiness guarantees and the identity) and `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md` (the readiness-condition mapping onto the closed vocabulary).
- DB layer row drives `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (the FTS5 definition comparison and the mdq runbook rows) and `docs/41_db/db_09_mcp_dedup_and_execution_snapshot.md` (the snapshot component).
- No ADR change: ADR-008 already owns the archive-and-recreate policy with recorded approvals; an ADR change needs a maintainer approval record (governance_01, governance_05) and is not written or simulated here (UNK-03). Doc content policy applies; run `uv run python tools/check_docs_content_policy.py` per `rules/tool-gates.md`.

## Assumptions
- The identity is computed from the canonical DDL text, not from the live database: the shared boundary rule forbids opening a sqlite3 connection in `scripts/shared/execution_snapshot.py`, and a live database that differs from the canonical shape is already refused at open, so the canonical text is the only stable identity source.
- Readiness probes never write to the production store; the functional probe runs against a scratch apply of the canonical DDL, consistent with the fingerprint module's inspect-only rule.
- The five readiness names are internal condition names mapped onto `ok`, `degraded`, and `unavailable`; no new state or reason code is added without the contract owner's decision.
- Recorded decisions (2026-11-28, maintainer): the canonical mdq DDL text and its identity hash move to `scripts/shared/mdq_schema.py` so the shared snapshot builder can read the identity without importing the mdq layer (amended row); and the identity is published through the health body `details` map, not through a capability metadata field, because `CapabilityState` carries only state and reason code.
- Overlap with the mdqmcp001 plan on `scripts/mcp_servers/mdq/health_check.py` and `docs/22_mcp/mcp_04_04_mdq.md`, and with the mdqmcp004 plan on `scripts/mcp_servers/mdq/db_schema.py`, `scripts/mcp_servers/mdq/health_check.py`, `tests/mcp_servers/mdq/test_mdq_health.py`, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`, and `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, is a compatible ordering overlap: this Plan executes after both per the dependency bullets.
- Bus factor is 1 for the mdq module set and the shared fingerprint module (single author across all commits).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the FTS5 definition comparison should extend to every virtual table or stay limited to FTS5 | No owner decision recorded | Plan default: compare FTS5 by stored DDL text (no extension needed) and keep `vec0` name-only; confirm with the shared-fingerprint owner before widening | False |
| UNK-02 | Whether the five readiness names require new capability states or reason codes in the closed vocabulary | No owner decision recorded for the health contract | Plan default: map onto the existing `ok`/`degraded`/`unavailable` states and the existing closed reason codes; a vocabulary change requires the contract owner and is not invented here | False |
| UNK-03 | Which document governs AAL-024 and AAL-025, and whether the runbook alignment requires an ADR change | No governing document named; the ADR records the approvals at lines 414-415 and `docs/00_governance/governance_03_issue-and-uncertainty-management.md` mentions them | Ask the maintainer; the plan writes no approval record and changes no ADR decision, so the alignment lands in the docs named by the task mapping | False |
| UNK-04 | Where the MDQ re-index verification runbook lives | No mdq-specific verification step recorded in db_03 section 8e or db_07 section 11 | Plan default: the verification step is added by the mdqmcp004 plan in db_07 section 11; this Plan cross-references it and adds the identity and readiness-condition wording in db_03 | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/db_schema.py` | Modify | mdq-mcp service only; the identity value is new published metadata | 2 | 1 | None: `deploy/init_db.sh` has no mdq gate |
| `scripts/shared/schema_fingerprint.py` | Modify | Every store that uses the shared fingerprint: rag, session, workflow, eventbus, mdq | 1 | 1 | Indirect: `deploy/init_db.sh` runs the gate for the three domain stores; the FTS5 comparison can refuse a previously accepted rag database, so the deploy pre-flight result can change |
| `scripts/shared/execution_snapshot.py` | Modify | Snapshot equality consumers (replay-equality decisions, audit) | 0 | 1 | None |
| `scripts/mcp_servers/mdq/health_check.py` | Modify | mdq `/health` consumers and the health registry | 1 | 1 | None |
| `scripts/mcp_servers/mdq/mdq_security_validation.py` | Modify | mdq posture gate (pre-bind) | 0 | 1 | None |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | Documentation only | — | 1 | None |
| `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md` | Modify | Documentation only | — | 1 | None |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Modify | Documentation only | — | 1 | None |
| `docs/41_db/db_09_mcp_dedup_and_execution_snapshot.md` | Modify | Documentation only | — | 1 | None |
| `scripts/shared/mdq_schema.py` | Create | Not assessed (amendment 2026-11-28) | N/A | N/A | Not assessed (amendment 2026-11-28) |
| `tests/mcp_servers/mdq/test_mdq_security_validation.py` | Modify | Not assessed (amendment 2026-11-28) | N/A | N/A | Not assessed (amendment 2026-11-28) |

## Design
Path B classification rationale: a shared-module contract change (`scripts/shared/`) plus more than three files, and a change that can alter the fingerprint gate's accept/refuse outcome for other stores.

Design decisions (narrow `python-design` application):
- Identity source: `mdq_schema_id` is SHA-256 over the normalized canonical DDL text produced from `_CREATE_STATEMENTS`. Alternative considered — derive it from the live database through `build_fingerprint()`; rejected because `scripts/shared/execution_snapshot.py` must not open a sqlite3 connection (shared boundary rule) and a live shape that differs from canonical is already refused at open, so the live read adds no information. The DDL text and the hash live in `scripts/shared/mdq_schema.py` (amendment 2026-11-28, maintainer decision): `scripts/mcp_servers/mdq/db_schema.py` imports that module and `scripts/shared/execution_snapshot.py` reads the identity from it, because the shared-is-leaf import-linter contract forbids `shared` importing `mcp_servers`.
- FTS5 comparison: read the stored `sqlite_master` DDL text for a virtual table whose module is FTS5 and compare it normalized; keep the name-only treatment for extension-backed virtual tables (`vec0`) and keep the shadow-table omission. Alternative considered — compare every virtual table through PRAGMA; rejected because it requires loading an extension in a leaf module.
- Readiness probes: functional insert, update, and delete probes run against a scratch in-memory apply of the canonical DDL, so readiness never mutates the production store; the live check compares the stored definition text, the trigger SQL, and the FTS row count against the chunk count. Alternative considered — probe rows in the live store; rejected (inspect-only rule, and a probe write would itself need a transaction owned by the mdqmcp005 design).
- Readiness vocabulary: the five conditions map onto the closed capability states — healthy to `ok`, rebuild in progress and degraded to `degraded`, inconsistent to `degraded`, failed to `unavailable` — with the existing closed reason codes. No new state or code is added (UNK-02).
- Consumer scan for `schema_fingerprint`: consumers are `scripts/mcp_servers/mdq/db_schema.py`, the `scripts/db/` schema entry points, `scripts/eventbus/schema.py`, and `deploy/init_db.sh`; the last three compare stores with no FTS5 virtual table, so only the rag store can change outcome (`tests/rag/` fixtures embed an FTS5 `chunks_fts`); `tests/shared/test_schema_fingerprint.py` is a target row.
- Consumer scan for `COMPONENT_KEYS`: consumers are `tests/shared/test_execution_snapshot.py` (target row) and the audit writers that name mismatching components; adding a component changes the equality output, which is the intended behavior, and no consumer asserts a fixed component count.
- Predictable fallout: module size — all target source files are under the 24576 B gate (largest `scripts/shared/schema_fingerprint.py` at 13563 B) and stay under it; skill size — not affected; pinned counts — `tests/shared/test_execution_snapshot.py` pins the component set (line 103) and `tests/mcp_servers/mdq/test_db_schema.py` pins table names and the mismatch message; both are target rows; tool inventory — not affected; generated blocks — the doc edits are prose, and `uv run python tools/generate_reference_table.py --check` is run as a validation gate.
- Import graph: `uv run lint-imports` reports 6 contracts kept; `scripts/shared/` stays a leaf (no new import from `db` or `mcp_servers`), and the mdq layer imports only `db` and `shared`. Radon: the FTS5 comparison helper is a small function that keeps grade A. Vulture (min-confidence 80) and bandit on `scripts/shared/schema_fingerprint.py`, `scripts/shared/execution_snapshot.py`, and `scripts/mcp_servers/mdq/`: no findings.
- Runbook ownership: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` section 11 owns the procedure; `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` section 8e keeps the per-store table and cross-references it. The mdq-specific steps (sidecar quarantine, re-index verification, failure rollback) are added by the mdqmcp004 plan; this Plan aligns the identity and readiness wording and does not create a second runbook.

## Implementation steps
1. **Phase 1: Characterization tests first**
   - [ ] Pin the current name-only FTS5 comparison and the plain-table readiness pass before any behavior change (REQ-001, AC-1; `tests/shared/test_schema_fingerprint.py`, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`)
2. **Phase 2: FTS5 definition comparison and functional probes**
   - [ ] Compare the stored FTS5 DDL text and the trigger SQL for FTS5 virtual tables (REQ-001; `scripts/shared/schema_fingerprint.py`)
   - [ ] Readiness uses the definition comparison, the trigger SQL, and the functional insert, update, and delete probe on a scratch apply (REQ-001, REQ-002; `scripts/mcp_servers/mdq/health_check.py`)
   - [ ] An empty FTS index with rows present becomes not ready (REQ-005; `scripts/mcp_servers/mdq/mdq_security_validation.py`)
   - [ ] Move the plain-table fixtures onto the real FTS5 definition and add the drift cases (REQ-001, REQ-002, AC-1, AC-2; `tests/mcp_servers/mdq/test_mdq_fts_schema.py`, `tests/mcp_servers/mdq/test_mdq_fts_trigger_sync.py`, `tests/mcp_servers/mdq/test_mdq_health.py`, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`, `tests/mcp_servers/mdq/test_mdq_health_posture.py`, `tests/mcp_servers/mdq/test_db_schema.py`)
   - [ ] The empty-FTS-index assertion moves from WARNING to FAILED, since only FAILED blocks Ready (REQ-005; `tests/mcp_servers/mdq/test_mdq_security_validation.py`) — amendment 2026-11-28
3. **Phase 3: Canonical identity and snapshot component**
   - [ ] Compute `mdq_schema_id` from the normalized canonical DDL (REQ-003; `scripts/mcp_servers/mdq/db_schema.py`)
   - [ ] Add the MDQ identity as an execution-snapshot component (REQ-004; `scripts/shared/execution_snapshot.py`)
   - [ ] Add the identity stability and snapshot-change tests (REQ-003, REQ-004, AC-3; `tests/mcp_servers/mdq/test_mdq_schema_identity.py`, `tests/shared/test_execution_snapshot.py`)
   - [ ] New file: own the canonical mdq DDL text and the normalized-DDL identity computation, so the shared snapshot builder can read the identity without importing the mdq layer (REQ-003; `scripts/shared/mdq_schema.py`) — amendment 2026-11-28
4. **Phase 4: Readiness vocabulary and runbook alignment**
   - [ ] Map the readiness conditions onto the closed capability vocabulary without adding vocabulary (REQ-006; `scripts/mcp_servers/mdq/health_check.py`)
   - [ ] Align the mdq runbook rows with the identity and the readiness conditions and cross-reference the procedure owned by db_07 section 11 (REQ-007; `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`)
   - [ ] Document the readiness guarantees, the identity, and the condition mapping (REQ-001, REQ-003, REQ-006, AC-4; `docs/22_mcp/mcp_04_04_mdq.md`, `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md`, `docs/41_db/db_09_mcp_dedup_and_execution_snapshot.md`)
5. **Phase 5: Recovery verification and full validation**
   - [ ] Scripted recovery verification on a scratch database per the aligned runbook (never against a database under `/opt/llm/`); confirm the gate refuses a plain-table `chunks_fts` and accepts the canonical shape (REQ-001, REQ-007, AC-1, AC-4; `scripts/mcp_servers/mdq/db_schema.py`)
   - [ ] Deployment check: `deploy/init_db.sh` has no mdq gate, but the shared fingerprint change can change the rag pre-flight outcome; run the deploy pre-flight against a scratch rag database (REQ-001; `scripts/shared/schema_fingerprint.py`)
   - [ ] Run the full validation sequence: `uv run python tools/run_validation_gates.py`, then `uv run pytest` (all requirements)

### Release units
N/A: no release unit — every phase passes validation alone because the fingerprint change and its pinned tests land in the same phase.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/schema_fingerprint.py` | Unit: FTS5 text comparison, extension-backed name-only case, shadow-table omission | `uv run pytest tests/shared/test_schema_fingerprint.py` | A plain table named `chunks_fts` is refused; `vec0` stays name-only |
| `scripts/mcp_servers/mdq/db_schema.py` | Unit: identity stability and change | `uv run pytest tests/mcp_servers/mdq/test_mdq_schema_identity.py tests/mcp_servers/mdq/test_db_schema.py` | Identity changes only when the canonical shape changes |
| `scripts/mcp_servers/mdq/health_check.py` | Integration: readiness against drifted definitions and functional probes | `uv run pytest tests/mcp_servers/mdq/test_mdq_fts_schema.py tests/mcp_servers/mdq/test_mdq_fts_trigger_sync.py tests/mcp_servers/mdq/test_mdq_health_endpoint.py` | Drift and no-op triggers refuse readiness |
| `scripts/mcp_servers/mdq/mdq_security_validation.py` | Unit: posture status | `uv run pytest tests/mcp_servers/mdq/test_mdq_health_posture.py` | Empty FTS index with rows present is not ready |
| `scripts/shared/execution_snapshot.py` | Unit: component set and mismatch naming | `uv run pytest tests/shared/test_execution_snapshot.py` | The mdq identity is a named component |
| Docs rows | Content policy and reference-table drift | `uv run python tools/check_docs_content_policy.py`, `uv run python tools/generate_reference_table.py --check` | Pass |
| Whole module | Lint, types, security, import contracts | `uv run python tools/run_validation_gates.py`, `uv run lint-imports` | Pass |

## Risks
- **Risk**: the FTS5 definition comparison can refuse previously accepted databases, including the rag store, forcing recreation → **Mitigation**: the change is limited to FTS5 text comparison; the affected stores are derived stores under ADR-008 with the archive-and-recreate runbook; the deploy pre-flight is run against a scratch database before any production store is touched.
- **Risk**: adding a snapshot component changes replay-equality results for existing audit rows → **Mitigation**: equality is per component and each differing component is named; the change is the intended behavior, and no consumer asserts a fixed component count.
- **Risk**: the readiness vocabulary mapping could conflict with the mdqmcp001 plan's health shape → **Mitigation**: this Plan adds no vocabulary and only supplies the states that plan's reporting already uses; the overlap is recorded as a compatible ordering overlap.
- **Risk**: a functional probe that writes to the production store would violate the inspect-only rule → **Mitigation**: probes run against a scratch apply of the canonical DDL only.
- **Risk**: overlap with the mdqmcp001 and mdqmcp004 plans on `scripts/mcp_servers/mdq/health_check.py`, `scripts/mcp_servers/mdq/db_schema.py`, the health test files, and `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` → **Mitigation**: execution order fixed by the dependency bullets; Step 8b overlap check records the judgement.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: characterization tests first | In Progress | — | — | Name-only comparison and plain-table readiness pass pinned before behavior change |
| 2 | Phase 2: FTS5 definition comparison and functional probes | In Progress | — | — | FTS5 text comparison, trigger SQL, functional probes, empty-index not ready |
| 3 | Phase 3: canonical identity and snapshot component | In Progress | — | — | Identity from canonical DDL; snapshot component added |
| 4 | Phase 4: readiness vocabulary and runbook alignment | In Progress | — | — | Mapping onto the closed vocabulary; docs alignment |
| 5 | Phase 5: recovery verification and full validation | In Progress | — | — | Scratch-database recovery run; deploy pre-flight check; full validation |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261128-003946_01_scripts_mcp_servers_mdq_db_schema.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261128-003946_02_scripts_shared_schema_fingerprint.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261128-003946_03_scripts_shared_execution_snapshot.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261128-003946_04_scripts_mcp_servers_mdq_health_check.py.md` | 2, 4 | Procedure | Pending | — | — |
| `implementations/20261128-003946_05_scripts_mcp_servers_mdq_mdq_security_validation.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261128-003946_06_tests_mcp_servers_mdq_test_mdq_fts_schema.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261128-003946_07_tests_mcp_servers_mdq_test_mdq_fts_trigger_sync.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261128-003946_08_tests_mcp_servers_mdq_test_mdq_schema_identity.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261128-003946_11_tests_mcp_servers_mdq_test_mdq_health.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261128-003946_14_tests_mcp_servers_mdq_test_db_schema.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261128-003946_15_docs_22_mcp_mcp_04_04_mdq.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261128-003946_16_docs_22_mcp_mcp_06_10_health-reasons-and-error-kinds.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261128-003946_17_docs_41_db_db_03_architecture_and_schema-migration-and-scaling.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261128-003946_18_docs_41_db_db_09_mcp_dedup_and_execution_snapshot.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261128-003946_19_scripts_shared_mdq_schema.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261128-003946_20_tests_mcp_servers_mdq_test_mdq_security_validation.py.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-172305
- **Evidence revision**: 41b423e73a5c2d98ae017a67a6059fcb3c75fd81
- **Related target files**: `scripts/mcp_servers/mdq/db_schema.py`, `scripts/shared/schema_fingerprint.py`, `scripts/shared/execution_snapshot.py`, `scripts/mcp_servers/mdq/health_check.py`, `scripts/mcp_servers/mdq/mdq_security_validation.py`, `tests/mcp_servers/mdq/test_mdq_fts_schema.py`, `tests/mcp_servers/mdq/test_mdq_fts_trigger_sync.py`, `tests/mcp_servers/mdq/test_mdq_schema_identity.py`, `tests/shared/test_schema_fingerprint.py`, `tests/shared/test_execution_snapshot.py`, `tests/mcp_servers/mdq/test_mdq_health.py`, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`, `tests/mcp_servers/mdq/test_mdq_health_posture.py`, `tests/mcp_servers/mdq/test_db_schema.py`, `docs/22_mcp/mcp_04_04_mdq.md`, `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `docs/41_db/db_09_mcp_dedup_and_execution_snapshot.md`, `scripts/shared/mdq_schema.py`, `tests/mcp_servers/mdq/test_mdq_security_validation.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; normalize and compare actual and canonical DDL including columns, tokenizer, options, and trigger SQL | `scripts/shared/schema_fingerprint.py` | Phase 2 | AC-2 | `tests/shared/test_schema_fingerprint.py` | Confirmed by repository evidence |
| REQ-001 | Problem; readiness may not prove canonical columns, tokenizer, or trigger synchronization | `scripts/mcp_servers/mdq/health_check.py` | Phase 2 | AC-1 | `tests/mcp_servers/mdq/test_mdq_fts_schema.py` | Confirmed by repository evidence |
| REQ-001 | Testing Expectations; plain table, no-op trigger, tokenizer, column, and option drift | `tests/mcp_servers/mdq/test_mdq_fts_schema.py` | Phase 1 | AC-1 | itself | Confirmed by repository evidence |
| REQ-001 | Design; the FTS5 definition comparison is documented in the DB layer reference | `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Phase 4 | AC-4 | `uv run python tools/generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-002 | Required Changes; run functional insert, update, and delete probes | `tests/mcp_servers/mdq/test_mdq_fts_trigger_sync.py` | Phase 2 | AC-2 | itself | Confirmed by repository evidence |
| REQ-002 | Design; probes run on a scratch apply so readiness never mutates the store | `scripts/mcp_servers/mdq/health_check.py` | Phase 2 | AC-2 | `tests/mcp_servers/mdq/test_mdq_fts_trigger_sync.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; generate a canonical `mdq_schema_id` from the canonical DDL | `scripts/mcp_servers/mdq/db_schema.py` | Phase 3 | AC-2 | `tests/mcp_servers/mdq/test_mdq_schema_identity.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; publish it through the health body `details` map (the capability entry has no metadata field) | `scripts/mcp_servers/mdq/health_check.py` | Phase 3 | AC-2 | `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` | Confirmed by repository evidence |
| REQ-004 | Problem; schema identity is missing from execution snapshots | `scripts/shared/execution_snapshot.py` | Phase 3 | AC-3 | `tests/shared/test_execution_snapshot.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; an unexpectedly empty FTS index is not ready | `scripts/mcp_servers/mdq/mdq_security_validation.py` | Phase 2 | AC-4 | `tests/mcp_servers/mdq/test_mdq_health_posture.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes; define the readiness states | `scripts/mcp_servers/mdq/health_check.py` | Phase 4 | AC-4 | `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` | Confirmed by repository evidence |
| REQ-006 | Design; the states map onto the existing closed vocabulary, recorded in the health-reasons doc | `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md` | Phase 4 | AC-4 | `uv run python tools/check_docs_content_policy.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes; one documented stop, archive or recreate, re-index, verify, restart sequence | `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Phase 4 | AC-4 | `uv run python tools/generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-003 | Documentation Impact; document actual readiness guarantees and schema identity | `docs/22_mcp/mcp_04_04_mdq.md` | Phase 4 | AC-4 | `uv run python tools/check_docs_content_policy.py` | Confirmed by repository evidence |
| REQ-004 | Documentation Impact; the snapshot component is documented | `docs/41_db/db_09_mcp_dedup_and_execution_snapshot.md` | Phase 4 | AC-3 | `uv run python tools/generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-001 | Design; the health fixtures must stop using a plain table named `chunks_fts` | `tests/mcp_servers/mdq/test_mdq_health.py` | Phase 2 | AC-1 | itself | Confirmed by repository evidence |
| REQ-001 | Design; the canonical-shape and mismatch-refusal assertions cover the FTS5 comparison | `tests/mcp_servers/mdq/test_db_schema.py` | Phase 2 | AC-2 | itself | Confirmed by repository evidence |
| REQ-003 | Amendment 2026-11-28: The shared-is-leaf import-linter contract forbids scripts/shared/execution_snapshot.py from importing mcp_servers.mdq.db_schema, so the canonical DDL and its identity hash must live in a shared module that both the mdq schema entry point and the snapshot builder import (maintainer decision, 2026-11-28) | scripts/shared/mdq_schema.py | Phase 3 | N/A: none cites REQ-003 | tests/mcp_servers/mdq/test_mdq_schema_identity.py | Confirmed by repository evidence |
| REQ-005 | Amendment 2026-11-28: The assertion that pins the current WARNING status lives in this file, not in tests/mcp_servers/mdq/test_mdq_health_posture.py, so the status change REQ-005 requires breaks it; the file must be updated to keep the suite passing (fallout, reported after amending) | tests/mcp_servers/mdq/test_mdq_security_validation.py | Phase 2 | N/A: none cites REQ-005 | itself | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261128-003946 -->