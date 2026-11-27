## Goal
- Replace the path-and-mtime derived `content_hash` in `mdq.sqlite` with a true content fingerprint, store truncation metadata per chunk, define one shared stale-state set used by both refresh and outline, and align the derived-database recreation runbook so same-mtime content changes, timestamp rollback, deleted files, and orphaned chunks are reliably detected.

## Priority
High

## Scope
- **In-Scope**:
  - `documents`: add `source_content_hash` computed from source bytes; store the path/mtime fingerprint in a separately named column; keep the indexed mtime and size.
  - `chunks`: store the original section hash and the stored chunk hash separately; add a truncation flag and the original and stored character counts.
  - Refresh decides skip or re-index from current mtime, size, and source hash, not from the stored mtime alone.
  - Outline inspects the filesystem for freshness; one shared stale-state set (`fresh`, `stale`, `missing`, `unknown`, `inconsistent`); chunks without a document row are `inconsistent`; the database-only stale SQL is redesigned.
  - Health and outline report from the same state definitions.
  - The mdq recreation runbook gains mdq-specific handling: `-wal`/`-shm` sidecar handling, re-index verification, and failure rollback.
- **Out-of-Scope**: FTS5 DDL identity and readiness (mdqmcp006); transaction atomicity (mdqmcp005); any ADR decision change (an ADR change needs a maintainer approval record; this Plan does not write or simulate one).
- **Dependencies**: depends on the mdqmcp003 plan (file-processing outcomes) for the per-file DTO statuses and counters the refresh tally uses; blocks mdqmcp005 and mdqmcp006; the health state codes extend the readiness reporting of mdqmcp001; the truncation fields are reused by mdqmcp008.
  - **Depends on**: `plans/20261127-163030_mdqmcp003_mdq-file-processing-outcomes.md` | all | the refresh comparison and the stale-state reporting tally per-file outcomes through the DTO statuses and counters that plan defines; executing before it would rewrite the same `indexer.py` and `mdq_models.py` lines twice

## Background
Source issue: `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md` (consolidated MDQ MCP backlog, Issue 4).

Adversarial verification against current source (evidence revision in Traceability):
- Confirmed: `scripts/mcp_servers/mdq/index_write.py` computes the document `content_hash` as `sha256(str(path) + str(mtime_ns))` (line 69) and `doc_id` as `sha256(str(path))` (line 65); the chunk hash covers the stored, possibly truncated content (line 89), and truncation happens before hashing (lines 87-88), so the stored hash matches the stored content but the original section hash is never stored. The issue's line citation `66-81` is off by a few lines; the claim itself holds.
- Confirmed: `scripts/mcp_servers/mdq/health_check.py` (line 48) and `scripts/mcp_servers/mdq/mdq_service.py` (line 343) count stale documents through `STALE_SQL_CONDITION` on database columns only; `is_stale()` (`scripts/mcp_servers/mdq/mdq_models.py` line 308) compares stored `mtime_ns` with `indexed_at` and never inspects the filesystem.
- Confirmed: incremental refresh skips a file when the stored `index_state` mtime equals the current mtime (`scripts/mcp_servers/mdq/indexer.py`, `_refresh_changed_file()`), so a same-mtime content change is never detected.
- Corrected: the issue's test claims (artificial timestamps, orphans treated as normal) were `Needs confirmation`; verified absent — no same-mtime, rollback, or deletion tests exist, and orphan coverage is limited to the legacy pre-FK guard in `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py`.
- Corrected: the recreation runbook already exists (`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` section 8e, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` section 11); mdq recovery is delete-and-re-index per ADR-008 Decision Detail 22. The gap is mdq-specific alignment: sidecar handling, re-index verification, and failure rollback are not defined for the mdq path. db_07 section 11 names `mdq.sqlite` only in subsection 11a (read-only schema inspection); its archive-delete-recreate procedure body covers the four domain stores and has no mdq steps.
- Corrected: ADR-008 already records the maintainer approvals for AAL-024 and AAL-025 (2026-11-24); no ADR decision change is required by this Plan — the alignment lands in the Reference docs named by the task mapping.

## Problem
Same-mtime content changes, timestamp rollback, changes after a stored truncation boundary, deleted files, and orphaned chunks cannot be reliably detected, and the name `content_hash` is misleading because it stores a path-plus-mtime fingerprint.

## Reason for Change
Data integrity. The schema change forces database recreation (ADR-008 treats `mdq.sqlite` as a derived store; no migration), so it must precede the transaction and schema-identity work (mdqmcp005, mdqmcp006).

## Implementation Intent
The database records what source content was indexed, what truncated content was stored, and what filesystem state was observed; refresh and outline compare against the current filesystem and use one shared set of stale states.

## Requirements
- `REQ-001`: `documents` stores `source_content_hash` computed from source bytes, and the path/mtime fingerprint is stored in a separately named column so no column named `content_hash` holds a non-content hash.
- `REQ-002`: `chunks` stores the original section hash (before truncation), the stored chunk hash, a truncation flag, and the original and stored character counts.
- `REQ-003`: refresh decides skip or re-index from current mtime, size, and source hash, not from the stored mtime alone.
- `REQ-004`: one shared stale-state set (`fresh`, `stale`, `missing`, `unknown`, `inconsistent`); chunks without a document row are `inconsistent`; outline inspects the filesystem; health and outline use the same definitions and the redesigned stale SQL.
- `REQ-005`: the mdq recreation runbook defines `-wal`/`-shm` sidecar handling, re-index verification, and failure rollback, and the docs align with it.

## Implementation Target Files
**Freeze status**: Frozen — `issue-to-plan` Step 8's Implementation Target Files
Validation passed for every row on 20261127; see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze).
Amended 2026-11-27 (fallout): added tests/mcp_servers/mdq/test_mdq_security_validation.py — Fixture DDL gains the new canonical columns: the minimal documents shape it builds must still satisfy the redesigned stale SQL after the documents column rename

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/db_schema.py` | Modify | Canonical DDL: add `source_content_hash` and the renamed path/mtime fingerprint column to `documents`; add the section hash, truncation flag, and original character count to `chunks` | REQ-001, REQ-002, AC-1, AC-2 | `_DOCUMENTS_DDL` (lines 26-35) has `content_hash` and no source-hash or truncation columns; `_CHUNKS_DDL` has `content_hash` and `char_count` but no section hash or truncation flag | `tests/mcp_servers/mdq/test_db_schema.py` | Verified |
| `scripts/mcp_servers/mdq/index_write.py` | Modify | Production writer: compute the source hash from file bytes, store the path/mtime fingerprint separately, and store the section hash, truncation flag, and original and stored character counts per chunk | REQ-001, REQ-002, AC-4 | `file_content_hash = hashlib.sha256((str(path) + str(now)).encode()).hexdigest()` (line 69); truncation at lines 87-88 before the hash at line 89 | `tests/mcp_servers/mdq/test_mdq_content_hash_semantics.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_models.py` | Modify | Define the shared stale-state set and the persisted-fingerprint fields on the models; redesign `STALE_SQL_CONDITION` against the new columns | REQ-001, REQ-002, REQ-004, AC-3 | `is_stale()` (line 308) and `STALE_SQL_CONDITION` (line 313) are the only stale definitions; `OutlineResponse.stale_warning` is `str \| None` (line 240) | `tests/mcp_servers/mdq/test_mdq_stale_detection.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_service.py` | Modify | Outline inspects the filesystem for freshness and reports the shared state; the stale count is computed from the state set | REQ-004, AC-3 | `outline()` uses `is_stale()` on stored columns only (line 249); the stale count query uses `STALE_SQL_CONDITION` (line 343) | `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py` | Verified |
| `scripts/mcp_servers/mdq/health_check.py` | Modify | Health reports the shared state set (per-state counts); `stale_document_count` stays as the count of documents in the `stale` state | REQ-004, AC-3 | `_check_stale_documents()` counts through `STALE_SQL_CONDITION` (line 48); the response key `stale_document_count` is published at line 110 | `tests/mcp_servers/mdq/test_mdq_health_stale.py` | Verified |
| `scripts/mcp_servers/mdq/indexer.py` | Modify | Refresh compares current mtime, size, and source hash before deciding skip or re-index | REQ-003, AC-1 | `_refresh_changed_file()` skips when `index_state` holds the current mtime only | `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` | Verified |
| `tests/mcp_servers/mdq/test_db_schema.py` | Modify | Canonical-shape assertions and the fingerprint-mismatch message test move onto the new columns | REQ-001, REQ-002, AC-4 | `test_db_schema.py:124` drops `content_hash` to prove the mismatch refusal; table-name assertions at lines 41 and 82 | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_stale_detection.py` | Modify | Add same-mtime content change, mtime rollback, deletion, and state-set cases with real files; keep the boundary characterization | REQ-001, REQ-004, AC-1, AC-3 | No `os.utime` or rollback test exists (verified absent); the file pins `is_stale` and `STALE_SQL_CONDITION` agreement | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_health_stale.py` | Modify | Health state reporting: per-state counts and the preserved `stale_document_count` semantics | REQ-004, AC-3 | Fixtures embed the current `documents` DDL (lines 29, 51); the count is asserted at line 105 | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py` | Modify | Orphan chunks without a document row become the explicit `inconsistent` state; filesystem-missing becomes `missing` | REQ-004, AC-3 | The file covers only the legacy pre-FK orphan guard (lines 49-51) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_schema_migration.py` | Modify | Schema recreation and production-writer contract tests against the new canonical shape | REQ-001, REQ-002, AC-4 | Fixtures embed the current `documents` and `chunks` DDL (lines 27, 46) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` | Modify | Refresh skip decision moves from mtime-only to mtime, size, and source hash | REQ-003, AC-1 | Consumer scan hit on `indexer.py`; the file pins the mtime-only skip behavior | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` | Modify | Fixture DDLs move onto the new canonical shape; the `stale_document_count` key-presence assertion stays | REQ-004, AC-3 | The file builds the current production schema in fixtures (lines 34-235) and in two in-test schemas at lines 427 and 489, and pins the key at line 340 | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_health.py` | Modify | Fixture DDLs move onto the new canonical shape | REQ-001, REQ-002, AC-4 | Fixtures embed the current `documents` and `chunks` DDL (lines 30, 52, 66) | itself | Verified |
| `tests/mcp_servers/mdq/test_index_delete.py` | Modify | Fixture inserts move onto the new canonical shape | REQ-001, REQ-002, AC-4 | Inserts list the current `documents` and `chunks` columns (lines 42, 52, 109) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_foreign_keys.py` | Modify | Fixture inserts move onto the new canonical shape | REQ-001, REQ-002, AC-4 | Insert lists the current `chunks` columns (line 107) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_content_hash_semantics.py` | Create | New file: production-writer tests with real filesystem modifications — same mtime with different content, mtime rollback, deletion, truncation-tail change, and the section-hash-versus-stored-hash distinction | REQ-001, REQ-002, AC-1, AC-2, AC-4 | Does not exist; `tests/mcp_servers/mdq/` holds 35 test files and none covers writer hash semantics (checked in Step 3) | itself | Verified |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | Define every persisted fingerprint and stale state; remove statements implying the path/mtime fingerprint is a content hash | REQ-001, REQ-004, AC-3 | Line 35 states `content_hash` is calculated on truncated content as if it were a content hash; line 66 describes the database-only stale check | `uv run python tools/check_docs_content_policy.py` | Verified |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Modify | Align the mdq runbook rows (sections 8d/8e) with the mdq-specific sidecar handling, re-index verification, and failure rollback | REQ-005, AC-5 | Section 8e says "Delete the file and re-index" with no sidecar, verification, or rollback steps for mdq | `uv run python tools/generate_reference_table.py --check` | Verified |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Modify | Section 11 gains the mdq steps: sidecar quarantine, re-index verification, and failure rollback for the delete-and-recreate path | REQ-005, AC-5 | Section 11's archive-delete-recreate procedure covers the four domain stores with no mdq steps; mdq appears only in subsection 11a (read-only inspection) | `uv run python tools/generate_reference_table.py --check` | Verified |
| `tests/mcp_servers/mdq/test_mdq_security_validation.py` | Modify | Fixture DDL gains the new canonical columns: the minimal documents shape it builds must still satisfy the redesigned stale SQL after the documents column rename | REQ-001, AC-4 | _create_db() builds documents with content_hash at lines 66-67 and check_health() is called through it at lines 381, 394, 406 | itself | Verified |

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
| `scripts/shared/schema_fingerprint.py` | The shared fingerprint defines what "canonical shape" means for the recreation gate; the new columns change the fingerprint inputs | REQ-001, REQ-002 |
| `docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md` | Canonical derived-store policy, Decision Detail 22, and the recorded AAL-024/AAL-025 approvals; read to confirm no ADR decision change is needed — not modified | REQ-005, UNK-03 |
| `scripts/mcp_servers/mdq/index_scan.py` | Confirm the scan path is not affected: discovery stays free of hashing and database access | REQ-003 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-003): same-mtime content changes and timestamp rollback are detected by the production writer and the refresh comparison, proven by real-file tests.
- `AC-2` (REQ-002): tail changes after a stored truncation boundary are detected; the original section hash and the stored chunk hash are distinct stored values.
- `AC-3` (REQ-004): deleted files and orphaned records have explicit states (`missing`, `inconsistent`); health and outline share the state definitions.
- `AC-4` (REQ-001, REQ-002): production-writer tests verify real hash semantics; the schema fingerprint gate accepts only the new canonical shape.
- `AC-5` (REQ-005): the runbook defines sidecar handling, re-index verification, and failure rollback for mdq, the docs align with it, and a scratch-database recreation run per `rules/persisted-schema-change.md` passes.

## Tests
- Real filesystem modifications; same mtime with different content; mtime rollback and deletion; truncation-tail changes; orphan document and chunk relationships (REQ-001, REQ-002, REQ-004; `tests/mcp_servers/mdq/test_mdq_content_hash_semantics.py`, `tests/mcp_servers/mdq/test_mdq_stale_detection.py`, `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py`).
- Schema recreation and production-writer contract tests (REQ-001, REQ-002; `tests/mcp_servers/mdq/test_db_schema.py`, `tests/mcp_servers/mdq/test_mdq_schema_migration.py`).
- Health and outline state-set agreement, including the preserved `stale_document_count` key (REQ-004; `tests/mcp_servers/mdq/test_mdq_health_stale.py`, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`).
- Run ruff, mypy, schema fingerprint checks, and the full test suite (`rules/toolchain.md` sequence via `uv run python tools/run_validation_gates.py`).

## Documentation Impact
Yes. Per `docs/00_index.md` "Document References by Task":
- MCP server spec row drives `docs/22_mcp/mcp_04_04_mdq.md`: define every persisted fingerprint and stale state and remove statements implying path/mtime fingerprints are content hashes (REQ-001, REQ-004).
- DB layer row drives `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` and `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`: the mdq runbook alignment (REQ-005).
- No ADR change: ADR-008 already owns the derived-store and archive-and-recreate policy with recorded approvals; an ADR change would need a maintainer approval record (governance_01, governance_05) and is not written or simulated here (UNK-03). Doc content policy applies; run `uv run python tools/check_docs_content_policy.py` per `rules/tool-gates.md`.

## Assumptions
- `mdq.sqlite` is a derived store; recreation without data carry-over is acceptable (ADR-008 Decision Detail 22), so column renames are safe without a migration path.
- The stale-state set does not conflict with existing health consumers: `stale_document_count` stays an integer count of documents in the `stale` state and per-state counts are additive; the issue's stop condition is not triggered.
- Overlap with the mdqmcp003 plan (`scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/indexer.py`, `scripts/mcp_servers/mdq/mdq_service.py`, `docs/22_mcp/mcp_04_04_mdq.md`) is a compatible ordering overlap: this Plan executes after that Plan per the dependency bullet.
- Bus factor is 1 for the mdq module set (single author across all commits).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether storing the full source hash requires reading files that exceed the size limit | No owner decision recorded | Plan default: the source hash is computed only for files that pass the size gate; oversized files are skipped before hashing, so no extra read is needed; confirm with the owner | False |
| UNK-02 | Operator timing for the database recreation | No operator schedule recorded | Confirm with the operator; the runbook alignment (REQ-005) is written regardless of timing | False |
| UNK-03 | Whether the runbook alignment requires an ADR change | No maintainer approval record exists for any new ADR wording | Default: no ADR decision change is needed because ADR-008 already owns the policy; if the alignment changes ADR-owned wording, a maintainer approval record is required and must not be written or simulated | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/db_schema.py` | Modify | mdq-mcp service only; forces recreation of the production `mdq.sqlite` | 2 | 1 | None: `deploy/init_db.sh` has no mdq gate; the schema is created at service open |
| `scripts/mcp_servers/mdq/index_write.py` | Modify | mdq-mcp writer path only | 0 | 1 | None |
| `scripts/mcp_servers/mdq/mdq_models.py` | Modify | mdq layer plus the health response shape (additive keys) | 0 | 1 | None |
| `scripts/mcp_servers/mdq/mdq_service.py` | Modify | mdq read path (outline, stale count) | 1 | 1 | None |
| `scripts/mcp_servers/mdq/health_check.py` | Modify | mdq `/health` consumers | 1 | 1 | None |
| `scripts/mcp_servers/mdq/indexer.py` | Modify | mdq refresh path | 0 | 1 | None |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | Documentation only | — | 1 | None |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Modify | Documentation only | — | 1 | None |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Modify | Documentation only | — | 1 | None |
| `tests/mcp_servers/mdq/test_mdq_security_validation.py` | Modify | Not assessed (amendment 2026-11-27) | N/A | N/A | Not assessed (amendment 2026-11-27) |

## Design
Path B classification rationale: a persisted-schema change plus more than three files.

Design decisions (narrow `python-design` application):
- Column naming: rename `documents.content_hash` to `path_mtime_fingerprint` and add `source_content_hash`; alternative considered — keep `content_hash` as the content hash and add a separate fingerprint column. The rename is chosen because the store is derived and recreation is forced anyway, so no compatibility shim is needed; the canonical DDL, the fingerprint gate, and the fixture tests move together.
- `chunks` keeps `content_hash` as the stored-content hash (already truthful) and gains `section_content_hash` (pre-truncation), `is_truncated`, and `original_char_count`.
- Stale states: one shared set defined in `scripts/mcp_servers/mdq/mdq_models.py`; health publishes per-state counts with `stale_document_count` preserved as the `stale`-state count; outline's `stale_warning` carries the state name. Consumer scan for `STALE_SQL_CONDITION` and `is_stale`: consumers are `scripts/mcp_servers/mdq/health_check.py`, `scripts/mcp_servers/mdq/mdq_service.py`, `scripts/mcp_servers/mdq/mdq_models.py`, `tests/mcp_servers/mdq/test_mdq_stale_detection.py` (all target rows); `tools/stale_detector.py` and `tests/tools/test_stale_detector.py` are not affected (their `is_stale` is the tool's own field, unrelated to mdq).
- Consumer scan for `content_hash`: `tools/generate_reference_table.py` and `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` are not affected (docs-fingerprint domain, not mdq); the test files embedding the mdq fixture DDL (`tests/mcp_servers/mdq/test_mdq_health.py`, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`, `tests/mcp_servers/mdq/test_index_delete.py`, `tests/mcp_servers/mdq/test_mdq_foreign_keys.py`) are target rows.
- Consumer scan for `documents`: `deploy/init_db.sh` is not affected (its expected-table list is the rag domain); `scripts/db/*` and `tests/db/*` candidates are the rag `documents` table, a different store per ADR-008 — not affected.
- Predictable fallout: module size — all target source files are under the 24576 B gate (largest `scripts/mcp_servers/mdq/mdq_service.py` at 15897 B) and stay under it with the expected growth, so no split row; skill size — not affected (no covered instruction file gains text); pinned counts — no test pins the `documents` column count; `tests/mcp_servers/mdq/test_db_schema.py` pins table names and the mismatch message and is a target row; tool inventory — not affected (no tool added or removed); generated blocks — the doc edits are prose, and `uv run python tools/generate_reference_table.py --check` is run as a validation gate.
- Import graph: `uv run lint-imports` reports 6 contracts kept; the mdq layer imports only `db` and `shared`; no new cross-layer import is introduced. Radon: the six target source files are grade A except two B functions (`mdq_service.py`, `health_check.py`); higher grades exist in the module outside the target set (`parser.py::parse_markdown` is D (24)). Vulture (min-confidence 80) and bandit on `scripts/mcp_servers/mdq/`: no findings.
- Runbook ownership: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` section 11 owns the recreation procedure and gains the mdq steps; `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` section 8e keeps the per-store table and cross-references it.

## Implementation steps
1. **Phase 1: Characterization tests first**
   - [ ] Pin the current writer hash semantics, the mtime-only refresh skip, and the health/outline consumers before any behavior change (REQ-001, REQ-003, REQ-004; `tests/mcp_servers/mdq/test_mdq_content_hash_semantics.py`, `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`)
2. **Phase 2: Canonical DDL and production writer**
   - [ ] Add `source_content_hash`, the renamed path/mtime fingerprint, and the chunk truncation fields to the canonical DDL (REQ-001, REQ-002; `scripts/mcp_servers/mdq/db_schema.py`)
   - [ ] Compute the source hash from bytes and store the section hash, truncation flag, and character counts (REQ-001, REQ-002; `scripts/mcp_servers/mdq/index_write.py`)
   - [ ] Move the fixture DDLs onto the new canonical shape (REQ-001, REQ-002, AC-4; `tests/mcp_servers/mdq/test_db_schema.py`, `tests/mcp_servers/mdq/test_mdq_schema_migration.py`, `tests/mcp_servers/mdq/test_mdq_health.py`, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`, `tests/mcp_servers/mdq/test_index_delete.py`, `tests/mcp_servers/mdq/test_mdq_foreign_keys.py`)
   - [ ] Modify (REQ-001; `tests/mcp_servers/mdq/test_mdq_security_validation.py`) — amendment 2026-11-27
3. **Phase 3: Shared stale-state set and consumers**
   - [ ] Define the state set and redesign `STALE_SQL_CONDITION` against the new columns (REQ-004; `scripts/mcp_servers/mdq/mdq_models.py`)
   - [ ] Outline inspects the filesystem and reports the shared state (REQ-004; `scripts/mcp_servers/mdq/mdq_service.py`)
   - [ ] Health reports per-state counts with `stale_document_count` preserved (REQ-004; `scripts/mcp_servers/mdq/health_check.py`)
   - [ ] Refresh compares current mtime, size, and source hash (REQ-003; `scripts/mcp_servers/mdq/indexer.py`)
   - [ ] Add the same-mtime, rollback, deletion, truncation-tail, and orphan-state tests with real files (REQ-001, REQ-002, REQ-004, AC-1, AC-2, AC-3; `tests/mcp_servers/mdq/test_mdq_stale_detection.py`, `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py`, `tests/mcp_servers/mdq/test_mdq_health_stale.py`)
4. **Phase 4: Runbook and documentation alignment**
   - [ ] Add the mdq sidecar, re-index verification, and failure-rollback steps to the recreation procedure (REQ-005; `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`) and align the mdq rows (REQ-005; `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`)
   - [ ] Define the persisted fingerprints and stale states and remove the misleading content-hash statements (REQ-001, REQ-004; `docs/22_mcp/mcp_04_04_mdq.md`)
5. **Phase 5: Recreation and full validation**
   - [ ] Scratch-database recreation run per `rules/persisted-schema-change.md` (never against a database under `/opt/llm/`); confirm the fingerprint gate accepts the new shape (REQ-001, REQ-005, AC-4, AC-5; `scripts/mcp_servers/mdq/db_schema.py`)
   - [ ] Deployment check: `deploy/init_db.sh` has no mdq gate, so the validation is the service restart plus re-index verification per the aligned runbook (REQ-005; `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`)
   - [ ] Run the full validation sequence: `uv run python tools/run_validation_gates.py`, then `uv run pytest` (all requirements)

### Release units
N/A: no release unit — every phase passes validation alone because the DDL, writer, and fixture tests land in the same phase.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/mdq/db_schema.py` | Unit: canonical shape plus fingerprint gate | `uv run pytest tests/mcp_servers/mdq/test_db_schema.py` | New shape accepted; a drifted shape refused with the archive-and-recreate message |
| `scripts/mcp_servers/mdq/index_write.py` | Integration: real files through the writer | `uv run pytest tests/mcp_servers/mdq/test_mdq_content_hash_semantics.py` | Source hash from bytes; same-mtime change and rollback detected |
| `scripts/mcp_servers/mdq/mdq_models.py` | Unit: state set and SQL agreement | `uv run pytest tests/mcp_servers/mdq/test_mdq_stale_detection.py` | SQL condition agrees with the Python state function |
| `scripts/mcp_servers/mdq/mdq_service.py` | Integration: outline against real filesystem | `uv run pytest tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py` | `missing` and `inconsistent` states explicit |
| `scripts/mcp_servers/mdq/health_check.py` | Integration: health response | `uv run pytest tests/mcp_servers/mdq/test_mdq_health_stale.py tests/mcp_servers/mdq/test_mdq_health_endpoint.py` | Per-state counts; `stale_document_count` key preserved |
| `scripts/mcp_servers/mdq/indexer.py` | Integration: refresh skip decision | `uv run pytest tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` | Same-mtime content change re-indexed |
| Docs rows | Content policy and reference-table drift | `uv run python tools/check_docs_content_policy.py`, `uv run python tools/generate_reference_table.py --check` | Pass |
| Whole module | Lint, types, security | `uv run python tools/run_validation_gates.py` | Pass |

## Risks
- **Risk**: the column rename forces recreation of the production `mdq.sqlite` and a full re-index → **Mitigation**: derived store with no lasting loss (ADR-008); the aligned runbook defines re-index verification and failure rollback; operator timing is UNK-02.
- **Risk**: the stale-state set could conflict with existing health consumers (the issue's stop condition) → **Mitigation**: `stale_document_count` semantics preserved as the `stale`-state count and per-state counts are additive; the conflict check found no existing consumer that would break (Assumptions).
- **Risk**: many test fixtures embed the current DDL and drift silently → **Mitigation**: all fixture-embedding test files are target rows; impact-based test execution plus the full suite.
- **Risk**: overlap with the mdqmcp003 plan on `scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/indexer.py`, `scripts/mcp_servers/mdq/mdq_service.py`, `docs/22_mcp/mcp_04_04_mdq.md` → **Mitigation**: execution order fixed by the dependency bullet; Step 8b overlap check records the judgement.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: characterization tests first | In Progress | — | — | Writer hash semantics, mtime-only skip, and health/outline consumers pinned before behavior change |
| 2 | Phase 2: canonical DDL and production writer | In Progress | — | — | New columns plus fixture DDLs land together |
| 3 | Phase 3: shared stale-state set and consumers | In Progress | — | — | State set, filesystem inspection, health counts, refresh comparison |
| 4 | Phase 4: runbook and documentation alignment | In Progress | — | — | mdq steps in db_07 section 11; mdq rows in db_03; misleading statements removed in the mdq doc |
| 5 | Phase 5: recreation and full validation | Pending | — | — | Scratch-database run, deployment check, full validation sequence |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261127-234020_01_scripts_mcp_servers_mdq_db_schema.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261127-234020_02_scripts_mcp_servers_mdq_index_write.py.md` | 1, 2 | Procedure | Pending | — | — |
| `implementations/20261127-234020_03_scripts_mcp_servers_mdq_mdq_models.py.md` | 1, 3 | Procedure | Pending | — | — |
| `implementations/20261127-234020_04_scripts_mcp_servers_mdq_mdq_service.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261127-234020_05_scripts_mcp_servers_mdq_health_check.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261127-234020_06_scripts_mcp_servers_mdq_indexer.py.md` | 1, 3 | Procedure | Pending | — | — |
| `implementations/20261127-234020_11_tests_mcp_servers_mdq_test_mdq_schema_migration.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261127-234020_13_tests_mcp_servers_mdq_test_mdq_health_endpoint.py.md` | 1, 2 | Procedure | Pending | — | — |
| `implementations/20261127-234020_14_tests_mcp_servers_mdq_test_mdq_health.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261127-234020_15_tests_mcp_servers_mdq_test_index_delete.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261127-234020_16_tests_mcp_servers_mdq_test_mdq_foreign_keys.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261127-234020_18_docs_22_mcp_mcp_04_04_mdq.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261127-234020_19_docs_41_db_db_03_architecture_and_schema-migration-and-scaling.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261127-234020_20_docs_41_db_db_07_api_and_operations-recovery-and-reference.md.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261127-234020_21_tests_mcp_servers_mdq_test_mdq_security_validation.py.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-170412
- **Evidence revision**: 41b423e73a5c2d98ae017a67a6059fcb3c75fd81
- **Related target files**: `scripts/mcp_servers/mdq/db_schema.py`, `scripts/mcp_servers/mdq/index_write.py`, `scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/mdq_service.py`, `scripts/mcp_servers/mdq/health_check.py`, `scripts/mcp_servers/mdq/indexer.py`, `tests/mcp_servers/mdq/test_db_schema.py`, `tests/mcp_servers/mdq/test_mdq_stale_detection.py`, `tests/mcp_servers/mdq/test_mdq_health_stale.py`, `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py`, `tests/mcp_servers/mdq/test_mdq_schema_migration.py`, `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`, `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`, `tests/mcp_servers/mdq/test_mdq_health.py`, `tests/mcp_servers/mdq/test_index_delete.py`, `tests/mcp_servers/mdq/test_mdq_foreign_keys.py`, `tests/mcp_servers/mdq/test_mdq_content_hash_semantics.py`, `docs/22_mcp/mcp_04_04_mdq.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `tests/mcp_servers/mdq/test_mdq_security_validation.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; `source_content_hash` from source bytes and a separate path/mtime fingerprint | `scripts/mcp_servers/mdq/db_schema.py` | Phase 2 | AC-1, AC-4 | `tests/mcp_servers/mdq/test_db_schema.py` | Confirmed by repository evidence |
| REQ-001 | Background; verified `content_hash` is `sha256(str(path) + str(mtime_ns))` at `index_write.py` line 69 | `scripts/mcp_servers/mdq/index_write.py` | Phase 2 | AC-4 | `tests/mcp_servers/mdq/test_mdq_content_hash_semantics.py` | Confirmed by repository evidence |
| REQ-001 | Documentation Impact; remove statements implying path/mtime fingerprints are content hashes | `docs/22_mcp/mcp_04_04_mdq.md` | Phase 4 | AC-3 | `uv run python tools/check_docs_content_policy.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; section hash and stored chunk hash stored separately with truncation metadata | `scripts/mcp_servers/mdq/db_schema.py` | Phase 2 | AC-2 | `tests/mcp_servers/mdq/test_db_schema.py` | Confirmed by repository evidence |
| REQ-002 | Background; verified truncation at `index_write.py` lines 87-88 before the stored hash at line 89 | `scripts/mcp_servers/mdq/index_write.py` | Phase 2 | AC-2 | `tests/mcp_servers/mdq/test_mdq_content_hash_semantics.py` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; schema recreation and production-writer contract tests | `tests/mcp_servers/mdq/test_mdq_schema_migration.py` | Phase 2 | AC-4 | itself | Confirmed by repository evidence |
| REQ-003 | Problem; same-mtime content changes undetectable — verified mtime-only skip in `_refresh_changed_file()` | `scripts/mcp_servers/mdq/indexer.py` | Phase 3 | AC-1 | `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; the five-state set and the redesigned stale SQL | `scripts/mcp_servers/mdq/mdq_models.py` | Phase 3 | AC-3 | `tests/mcp_servers/mdq/test_mdq_stale_detection.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; filesystem inspection for outline freshness | `scripts/mcp_servers/mdq/mdq_service.py` | Phase 3 | AC-3 | `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; health and outline use the same state definitions | `scripts/mcp_servers/mdq/health_check.py` | Phase 3 | AC-3 | `tests/mcp_servers/mdq/test_mdq_health_stale.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; chunks without a document row are `inconsistent` | `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py` | Phase 3 | AC-3 | itself | Confirmed by repository evidence |
| REQ-005 | Required Changes; sidecar handling, re-index verification, and failure rollback for the mdq path | `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Phase 4 | AC-5 | `uv run python tools/generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-005 | Required Changes; alignment of the mdq runbook rows | `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Phase 4 | AC-5 | `uv run python tools/generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations; production-writer contract tests with real files | `tests/mcp_servers/mdq/test_mdq_content_hash_semantics.py` | Phase 1 | AC-2, AC-4 | itself | Confirmed by repository evidence |
| REQ-001 | Design; fixture DDLs embed the current canonical shape and must move with it | `tests/mcp_servers/mdq/test_mdq_health.py` | Phase 2 | AC-4 | itself | Confirmed by repository evidence |
| REQ-002 | Design; fixture DDLs embed the current canonical shape and must move with it | `tests/mcp_servers/mdq/test_mdq_health.py` | Phase 2 | AC-4 | itself | Confirmed by repository evidence |
| REQ-001 | Design; fixture DDLs embed the current canonical shape and must move with it | `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` | Phase 2 | AC-4 | itself | Confirmed by repository evidence |
| REQ-002 | Design; fixture DDLs embed the current canonical shape and must move with it | `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` | Phase 2 | AC-4 | itself | Confirmed by repository evidence |
| REQ-001 | Design; fixture inserts list the current columns | `tests/mcp_servers/mdq/test_index_delete.py` | Phase 2 | AC-4 | itself | Confirmed by repository evidence |
| REQ-002 | Design; fixture inserts list the current columns | `tests/mcp_servers/mdq/test_index_delete.py` | Phase 2 | AC-4 | itself | Confirmed by repository evidence |
| REQ-001 | Design; fixture inserts list the current columns | `tests/mcp_servers/mdq/test_mdq_foreign_keys.py` | Phase 2 | AC-4 | itself | Confirmed by repository evidence |
| REQ-002 | Design; fixture inserts list the current columns | `tests/mcp_servers/mdq/test_mdq_foreign_keys.py` | Phase 2 | AC-4 | itself | Confirmed by repository evidence |
| REQ-001 | Amendment 2026-11-27: Fixture DDL gains the new canonical columns: the minimal documents shape it builds must still satisfy the redesigned stale SQL after the documents column rename | `tests/mcp_servers/mdq/test_mdq_security_validation.py` | Phase 2 | AC-4 | itself | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261127-234020 -->