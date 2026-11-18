## Goal
- ADR-008 states, for each of the six SQLite databases (`rag`, `session`, `workflow`, `eventbus`, `mcp_dedup`, `mdq`), the schema-mismatch rule, the retention rule, and the canonical and derived stores, and ADR-006, ADR-001, the data-layer and migration guides, ARCH-003, and the schema comments agree with it.

## Priority
High

## Scope
- **In-Scope**:
  - ADR-008: six-database scope and title, table inventory built from the DDL sources, per-database schema-mismatch rule (archive and recreate), per-database retention rule (EventBus unbounded growth recorded as an accepted risk), canonical memory store (SQLite), reference and terminology fixes, pending approval records.
  - ADR-006: the no-event-loss statements become conditional on the schema-mismatch rule; retention as an accepted risk; title reference.
  - ADR-001 terminology, `agent_09_01`, the migration guide `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (location resolved in Step 3), ARCH-003, and the comments of `scripts/db/schema_sql.py` and `scripts/eventbus/schema.sql`.
  - Scope amendments against the Issue's Target Files, each a consequence of the maintainer's decisions in this cycle: `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (ledger rows), `tools/check_docs_structure.py` (ADR-008 size ceiling), `docs/10_adr/adr_01_index.md` and `docs/41_db/db_08_active_databases.md` (the ADR-008 title appears there).
- **Out-of-Scope**:
  - Any DDL change (comments only; comments are stripped before the schema fingerprint is computed, checked in Step 3).
  - Running or planning the deployment; archiving or recreating any production database.
  - Implementing retention, drain, or migration; renaming the ADR-008 file (`4db` stays in the file name, which about 30 documents reference).
  - Writing approval text for any decision or changing the Known Issue SHARED-002 status before approval is recorded.
- **Dependencies**: N/A: none open. The schema-fingerprint reconcile issue (adrchk009, its Phase 7) and the EventBus task-supervision issue (adrchk017, its schema task) wait for this decision record; they are dependents, not prerequisites. The approval-governance issue (adrchk011) is implemented and archived.

## Background
Filed from the consolidated ADR review (package ADRCHK2-H08). Re-verification against current source and the production database files (read-only, `immutable=1`) in Steps 2 and 3 changed several claims:
- Scope: the ADR-008 body already treats `mcp_dedup.sqlite` and `mdq.sqlite` as stores outside the four domains and the Recovery Policy Matrix already has an `mcp_dedup` column. Remaining mismatches: the title and Summary say "Four", the Scope section lists four targets, and ARCH-003 says "four-database separation". The maintainer chose to widen the scope to six databases.
- Schema mismatch: ADR-008 Constraints and `db_03` section 8e already state one rule for all databases (the startup gate refuses a mismatching file; the operator archives and recreates it; no migration; data loss is possible). It conflicts with ADR-006 ("losses are not tolerated", INV-07) and with the `schema_sql.py` comment that session data must not be recreated silently. The maintainer chose archive-and-recreate for all databases.
- Production state: `/opt/llm/db/workflow.sqlite` has the legacy tables `schema_migrations` and `workflow_schema_version` and no `tool_call_state` (2 `tasks`, 5 `processed_events`); `eventbus.sqlite` lacks `dlq_outbox` (0 `events`); `session.sqlite` has every canonical table (0 `sessions`, `messages`, `memories`; WAL content not read). Both workflow and eventbus will be refused by the next fingerprint gate.
- Retention: no code deletes `events`, `consumer_delivery`, or `dlq_outbox` rows (no `DELETE FROM` for them in `scripts/eventbus`); `schema.sql` keeps `done` rows as the reconciliation record. Session (`purge_old_sessions`, `retention_days`), workflow (`purge_finished_workflow_events`), and mcp_dedup (`purge_expired`) have purge code. The maintainer chose to record unbounded EventBus growth as an accepted risk.
- Memory store: `jsonl_store.py`, `write_ops.py` (SQLite first, then the JSONL append), and `agent_09_01` already treat SQLite `memories` as canonical, `memories_fts` and `memories_vec` as derived, and the JSONL file as an append-only archive. ADR-008 (Recovery Policy Matrix, Known Issue SHARED-002) classifies `memories_vec` as both canonical and derived and omits `memories_fts`, `memory_links`, `session_diagnostics`, and the JSONL archive. The maintainer chose SQLite as canonical.
- Inventory and references (confirmed): Decision Detail #4 names `dlq_outbox` but INV-04 does not; the Summary says "Decision Details #14 to #20" while #21 exists; the operator-restore glossary cites "#14/#17" although #14 is DB-state classification; `workflow` also owns `tool_call_state`, and Implementation References omit the tables listed in REQ-001; ADR-001 line "Whether the DB schema version matches" uses version terminology.

## Problem
ADR-008 gives no per-database rule for schema mismatch, retention, or canonical store, lists the wrong set of databases and tables, and contradicts ADR-006 and the schema comments; the next deployment will refuse two databases that hold data.

## Reason for Change
INV-09 requires a retention rule per database, ADR-006 promises no event loss, and the schema gate recreates databases; the three statements cannot all hold without recorded conditions. Schema-changing work (adrchk009, adrchk017) is blocked until the rules are recorded.

## Implementation Intent
- Record the maintainer's decisions in ADR-008 and propagate them to ADR-006, the guides, ARCH-003, and the comments, as pending decision-text changes with ledger rows; fix the confirmed reference and terminology errors directly.

## Requirements
- `REQ-001`: ADR-008 contains a table inventory per database built from `scripts/db/schema_sql.py`, `scripts/eventbus/schema.sql`, `scripts/mcp_servers/mdq/db_schema.py`, and the mcp_dedup DDL in `scripts/shared/mcp_dedup.py`, including `memories_fts`, `memory_links`, `session_diagnostics`, `processed_events`, `tool_call_state`, `consumer_delivery`, `consumer_offsets`, and `dlq_outbox`.
- `REQ-002`: ADR-008 reference errors are fixed: Summary decision range, operator-restore glossary citations, INV-04 naming `dlq_outbox`, and the stale line reference in Known Issue SHARED-002.
- `REQ-003`: ADR-001 uses the schema-fingerprint term instead of "DB schema version".
- `REQ-004`: ADR-008, ARCH-003, and every document that quotes the ADR-008 title name the same six databases; the title is "Separating SQLite into Six Databases".
- `REQ-005`: ADR-008 has one schema-mismatch rule for each of the six databases (archive and recreate, with the per-database precondition), ADR-006 states its no-loss claims under that rule, and the schema comments and `db_03` match.
- `REQ-006`: ADR-008 has one retention rule for each database: EventBus `events`, `consumer_delivery`, and `dlq_outbox` growth is an accepted risk; the other databases cite their current purge or rebuild behavior; `db_03` section 11 no longer presents unimplemented cleanup as in force.
- `REQ-007`: ADR-008 names SQLite `memories` and `memory_links` as canonical, `memories_fts` and `memories_vec` as derived, and the JSONL file as an append-only archive; `agent_09_01` and `db_03` agree.
- `REQ-008`: Every decision-text change is recorded as a pending approval bullet citing a ledger id that exists in `governance_03` Part 5; no approval text is written; the ADR-008 size ceiling is updated to the accepted size.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify: add ledger rows AAL-024 to AAL-029 to Part 5 | Pending bullets in ADR-008 and ADR-006 must cite existing ids (scope amendment) | REQ-008 / AC-8 | Part 5 ends at AAL-023; the entry form has six fields (checked in Step 3) | `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify: title, Summary, Scope, Recovery Policy Matrix (mdq column, memory classification), Decision Details, INV-04 and INV-09, glossary citations, Known Deviations wording, Out of Scope, Implementation References, pending approval bullets | Six-database scope, per-database rules, inventory, reference errors | REQ-001, REQ-002, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008 / AC-1, AC-2, AC-4, AC-5, AC-6, AC-7, AC-8 | Title and Summary say "Four"; Matrix has no `mdq` column and lists `memories_vec` as both canonical and derived; Summary range `#14 to #20` while #21 exists; glossary cites #14 for operator-restore; INV-04 omits `dlq_outbox` (checked in Step 2) | `tools/check_adr_structure.py`, `tools/check_adr_preservation.py`, `tools/check_db_separation.py` | Verified |
| `tools/check_docs_structure.py` | Modify: set the `adr_02_05_008_db-sqlite-4db-separation.md` entry in the size exceptions to the accepted size | The file is at its ceiling (37259 of 37291 bytes) and the edits add content (scope amendment) | REQ-008 / AC-8 | `SIZE_EXCEPTIONS` records 37291 for this file; the default limit is 32768 (checked in Step 3) | `tests/tools/test_check_docs_structure.py` | Verified |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify: condition the no-loss statements on the ADR-008 schema-mismatch rule; state retention as an accepted risk; update the ADR-008 title; pending approval bullets | Contradiction between "losses are not tolerated" and the recreate gate | REQ-004, REQ-005, REQ-006, REQ-008 / AC-4, AC-5, AC-6, AC-8 | Decision 9 and INV-07 state no loss; the startup bullet states fingerprint refusal; Related ADRs quotes the old title; Review Triggers lists automatic retention (checked in Step 2) | `tools/check_adr_structure.py`, `tools/check_adr_preservation.py` | Verified |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify: replace "DB schema version" with the schema-fingerprint wording (terminology only) | Version terminology is not used by the canonical gate | REQ-003 / AC-3 | Health-check list contains "Whether the DB schema version matches" (checked in Step 2) | `tools/check_adr_structure.py` | Verified |
| `docs/23_agent/agent_09_01_data-layer-session-db.md` | Modify: point to the ADR-008 mismatch, retention, and canonical-store rules for `session.sqlite` and memory | The guide must agree with ADR-008 | REQ-005, REQ-006, REQ-007 / AC-5, AC-6, AC-7 | Guide already names SQLite `memories` canonical, JSONL archive, derived `memories_fts`/`memories_vec`; says nothing on the recreate rule (checked in Step 2) | `tools/check_docs_structure.py` | Verified |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Modify: state the six-database mismatch rule table, and that section 11 cleanup is not implemented (accepted risk) | The migration guide must agree with ADR-008 (location resolved: `docs/41_db/`) | REQ-004, REQ-005, REQ-006 / AC-4, AC-5, AC-6 | Section 8e table lists five databases; section 11 lists mitigation strategies without saying they are not implemented (checked in Step 2) | `tools/check_docs_structure.py` | Verified |
| `docs/41_db/db_08_active_databases.md` | Modify: update the ADR-008 link text | Title propagation (scope amendment) | REQ-004 / AC-4 | Line quoting "Separating SQLite into Four Databases" (checked in Step 3) | `tools/check_docs_structure.py` | Verified |
| `docs/10_adr/adr_01_index.md` | Modify: update the ADR-008 row title | Title propagation (scope amendment) | REQ-004 / AC-4 | Index row quotes the old title (checked in Step 3) | `tools/check_adr_reference.py` | Verified |
| `config/adr_authority.toml` | Modify: ARCH-003 `current_value` and review trigger name the six-database set | ARCH-003 and ADR-008 must agree | REQ-004 / AC-4 | ARCH-003 says "ADR-008 four-database separation" (checked in Step 2) | `tools/generate_adr_authority.py --check` | Verified |
| `scripts/db/schema_sql.py` | Modify: rewrite the `session.sqlite` recreate comment to state the ADR-008 rule (comment only) | The comment says the recreate decision is deferred | REQ-005 / AC-9 | Comment before `_SESSION_SCHEMA_TEMPLATE` states deferral; comments are stripped by `_COMMENT_RE` in `schema_fingerprint.py` (checked in Step 3) | `tools/check_db_separation.py`, `tests/db/test_create_schema.py` | Verified |
| `scripts/eventbus/schema.sql` | Modify: comment on `dlq_outbox` and the event tables states the retention rule (comment only) | Retention is undocumented at the DDL | REQ-006 / AC-9 | `dlq_outbox` comment says `done` rows are retained; no comment on `events` or `consumer_delivery` (checked in Step 3) | `tools/check_db_separation.py`, `tests/eventbus/` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/mdq/db_schema.py` | mdq table inventory (`documents`, `chunks`, `chunks_fts`, `index_state`, triggers) | REQ-001 |
| `scripts/shared/mcp_dedup.py` | mcp_dedup DDL (`tool_call_state`) and `purge_expired` | REQ-001, REQ-006 |
| `scripts/shared/schema_fingerprint.py` | Proves comments do not change the fingerprint | REQ-005 |
| `scripts/agent/memory/jsonl_store.py` | JSONL archive semantics (append-only, no mutation record) | REQ-007 |
| `scripts/agent/memory/write_ops.py` | SQLite-first write order and the `delete` change event | REQ-007 |
| `scripts/agent/memory/import_ops.py` | JSONL replay into SQLite | REQ-007 |
| `scripts/db/maintenance.py` | `purge_old_sessions`, `RetentionConfig`, `purge_corrupt_archives` | REQ-006 |
| `scripts/agent/workflow/state_store.py` | `purge_finished_workflow_events` | REQ-006 |
| `tools/check_db_separation.py` | Static ownership check that must still pass | REQ-004, REQ-005 |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Says mcp_dedup is "a fifth database file outside the original four-database set" (UNK-03) | REQ-004 |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | ADR-004 terms and the pending-bullet form | REQ-008 |

## Acceptance Criteria
- AC-1 (REQ-001): every table name created by the four DDL sources appears in ADR-008's inventory under its database; checked with `rg` over the sources and the ADR.
- AC-2 (REQ-002): the Summary range ends at #21; each glossary citation names a Decision Detail that states the cited behavior; INV-04 names `dlq_outbox`; no line number remains in SHARED-002.
- AC-3 (REQ-003): ADR-001 no longer contains "schema version".
- AC-4 (REQ-004): the ADR-008 title, Summary, Scope, Matrix, ARCH-003, `adr_01_index.md`, `db_08`, and ADR-006 Related ADRs name the same six databases; `generate_adr_authority.py --check` reports no drift.
- AC-5 (REQ-005): ADR-008 has one mismatch rule per database; ADR-006 Decision 9 and INV-07 state the no-loss claim as holding "unless the database is archived and recreated under ADR-008"; the `schema_sql.py` comment matches.
- AC-6 (REQ-006): ADR-008 has one retention rule per database and records the EventBus growth as an accepted risk; `db_03` section 11 says the cleanup is not implemented.
- AC-7 (REQ-007): ADR-008, `agent_09_01`, and `db_03` classify `memories`/`memory_links` as canonical and `memories_fts`/`memories_vec` as derived; `memories_vec` is not canonical anywhere.
- AC-8 (REQ-008): `check_adr_structure.py` passes; every pending bullet cites an existing AAL id; `check_docs_structure.py` passes with the updated ADR-008 ceiling.
- AC-9 (REQ-005, REQ-006): the schema fingerprints of `schema_sql.py` and `schema.sql` are identical before and after the comment edits; `check_db_separation.py` reports no violation; the comments carry no history wording.

## Tests
- Documentation and comments only: no new tests. Run `tests/tools/test_check_docs_structure.py`, `tests/tools/test_check_db_separation.py`, `tests/db/test_create_schema.py`, and `tests/eventbus/` as regression checks for REQ-004, REQ-005, REQ-006, REQ-008.
- AC-9 is verified by a one-off fingerprint comparison with `shared.schema_fingerprint` before and after (record both values in the procedure Notes; no test is added).

## Documentation Impact
Yes. ADR-008, ADR-006, ADR-001 (terminology), `agent_09_01`, `db_03`, `db_08`, `adr_01_index.md`, and ARCH-003 per `routing.md` Docs mapping and `docs/00_index.md`; REQ-001 to REQ-008 drive them. Run the checkers `routing.md` Tools lists after each `docs/` edit, plus `tools/check_db_separation.py` after the schema comments change.

## Assumptions
- The ledger ids AAL-024 to AAL-029 are the next free ids (the ledger ends at AAL-023; checked in Step 3). Their use: AAL-024 ADR-008 six-database scope and title; AAL-025 ADR-008 schema-mismatch rule; AAL-026 ADR-008 retention rule; AAL-027 ADR-008 memory canonical store; AAL-028 ADR-008 INV-04 naming `dlq_outbox`; AAL-029 ADR-006 conditional no-loss and retention risk.
- The retention rule of `rag`, `session`, `workflow`, `mcp_dedup`, and `mdq` is recorded from current behavior (the purge or rebuild code named in Reference Files); the maintainer decided only the EventBus tables, so the rest rides in the same pending bullet for confirmation.
- Known Issue SHARED-002 stays open in `governance_03` Part 1 until the memory classification is approved (a documentation-only edit cannot close it, `governance_03` Resolution Rules); its closure is a follow-up.
- Production state (evidence only, read-only `immutable=1`, WAL content not read): workflow and eventbus will be refused by the fingerprint gate at the next deployment; the operator runs the archive-and-recreate runbook (`db_03` section 8e). No production file is changed by this Plan.
- No overlap with another Frozen Plan (checked in Step 8b).
- Step 3a of plan-to-implementation-procedure found that ADR-008 contains statements that are correct only for the four `DbTarget` databases (INV-01 to INV-08, Implementation Notes, the boundary Verification row); REQ-004 therefore means the title, Summary, Scope, Matrix, and ARCH-003 name the same six databases, and does not rewrite those four-database statements.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Closure of Known Issue SHARED-002 and removal of its Known Deviations line after approval | Maintainer approval of the memory classification is not recorded | Follow-up after the approval is recorded (edit `governance_03` Part 1 and ADR-008 Known Deviations together) | False |
| UNK-02 | How an `adr_authority.toml` assumption change (ARCH-003) is approved | `governance_01`/`governance_05` define approval for ADR decisions, not for assumptions | Maintainer; the Plan changes the text only and reports the question | False |
| UNK-03 | Whether `db_03_07` ("a fifth database file outside the original four-database set") and `agent_04_03` ("four SQLite databases (`DbTarget`)") need wording changes for the six-database scope | `DbTarget` really has four members, so those sentences may stay true | Maintainer; not edited here (outside the frozen scope) | False |
| UNK-04 | Whether the production workflow and eventbus data (2 tasks, 5 processed events, 0 events) matter before the next deployment | WAL content and live process state not read | Operator decision at deployment; archive-and-recreate runbook | False |
| UNK-05 | Whether the ADR-008 file name (`4db`) should change | About 30 documents link to it; renaming is a separate task | Maintainer; not part of this Plan | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | Low | 16 | N/A | None: documentation only |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify | High (ADR quoted by about 30 documents) | 18 | N/A | None: documentation only |
| `tools/check_docs_structure.py` | Modify | Medium (gate for every document) | 39 | N/A | None: tool run in development and CI |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Medium | 17 | N/A | None: documentation only |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify | Low | 12 | N/A | None: documentation only |
| `docs/23_agent/agent_09_01_data-layer-session-db.md` | Modify | Low | 6 | N/A | None: documentation only |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Modify | Medium | 18 | N/A | None: documentation only |
| `docs/41_db/db_08_active_databases.md` | Modify | Low | 4 | N/A | None: documentation only |
| `docs/10_adr/adr_01_index.md` | Modify | Medium (index consumed by `check_adr_reference.py`) | 18 | N/A | None: documentation only |
| `config/adr_authority.toml` | Modify | Medium (source of generated authority tables) | 5 | N/A | `config/` file but not read by any service; deploy is not needed |
| `scripts/db/schema_sql.py` | Modify | Low (comment only; fingerprint unchanged) | 17 | N/A | `scripts/` change: deploy to `/opt/llm` is the user's decision (`skills/deploy/SKILL.md`) |
| `scripts/eventbus/schema.sql` | Modify | Low (comment only; fingerprint unchanged) | 10 | N/A | `scripts/` change: same hand-off |

## Design
Path B (more than 3 target files). Analyses were run once each (checked in Step 3 and Step 5): `lint-imports` is unaffected (no Python import changes); the only Python edit is a comment; `tools/check_db_separation.py` reports no violation at baseline; `tools/generate_adr_authority.py --check` reports no drift at baseline; the consumer scan found the ADR-008 title in `adr_01_index.md`, `db_08_active_databases.md`, and ADR-006 (the file name is referenced by about 30 documents and stays); churn is in the Affected areas table; the production databases were read read-only with `immutable=1` and nothing was changed.

Decisions (made by the maintainer in this cycle; the Plan only records them):
1. Scope: six databases, as four platform-domain databases (`DbTarget`: `rag`, `session`, `workflow`, `eventbus`) plus two non-domain stores (`mcp_dedup`, `mdq`); the technical statements that are true only of the four domain databases (Constraints on `SQLiteHelper` targets, INV-01 to INV-08, Implementation Notes, the four-database boundary check row) keep their four-database wording; title "Separating SQLite into Six Databases"; Matrix gets an `mdq` column; the "Derived Stores Outside the Four Domains" section becomes part of the main scope; Out of Scope drops `mdq.sqlite` and keeps its schema details out of this ADR. Alternative (four plus outside stores) not chosen.
2. Mismatch rule: for every database the gate refuses a non-matching file and the operator archives and recreates it (rag, session: current create-only shape; workflow, eventbus: shared fingerprint; mdq: shared fingerprint on every start; mcp_dedup: recreated empty). Preconditions: session needs `/session export` and the JSONL archive for memory; workflow and eventbus data are not carried over. Alternative (drain then recreate) not chosen.
3. Retention: EventBus `events`, `consumer_delivery`, `dlq_outbox` grow without bound, recorded as an accepted risk against INV-09 and tied to the ADR-006 Review Trigger "Automatic event retention or pruning becomes necessary". Others: current purge or rebuild behavior.
4. Memory: SQLite `memories` and `memory_links` canonical; `memories_fts`, `memories_vec` derived; JSONL is an append-only archive with delete and pin change events, replayed by `/memory rebuild`.
5. Approval: every decision-text change is a pending bullet with a ledger row (REQ-008); wording-only corrections (REQ-002, REQ-003, comments) are not.
6. Size: the ADR-008 ceiling is raised to the accepted size; ADR-008 edits and the ceiling edit form one release unit because `check_docs_structure.py` fails between them.

## Implementation steps
1. **Phase 1: Ledger rows**
   - [ ] Add AAL-024 to AAL-029 to Part 5 with `Approver` and `Date` `Not recorded` (REQ-008; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
2. **Phase 2: ADR-008**
   - [ ] Apply the scope, inventory, mismatch, retention, canonical-store, reference, and pending-bullet edits (REQ-001, REQ-002, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008; `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`)
3. **Phase 3: Size ceiling**
   - [ ] Set the ADR-008 entry of the size exceptions to the accepted size (REQ-008; `tools/check_docs_structure.py`)
4. **Phase 4: ADR-006**
   - [ ] Condition the no-loss statements, record the retention risk, update the title reference, add pending bullets (REQ-004, REQ-005, REQ-006, REQ-008; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`)
5. **Phase 5: ADR-001 terminology**
   - [ ] Replace "DB schema version" (REQ-003; `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`)
6. **Phase 6: Guides and index**
   - [ ] Align the session data-layer guide (REQ-005, REQ-006, REQ-007; `docs/23_agent/agent_09_01_data-layer-session-db.md`)
   - [ ] Align the migration guide (REQ-004, REQ-005, REQ-006; `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`)
   - [ ] Update the title in the active-databases guide and the ADR index (REQ-004; `docs/41_db/db_08_active_databases.md`, `docs/10_adr/adr_01_index.md`)
7. **Phase 7: ARCH-003**
   - [ ] Update `current_value` and the review trigger, then run `generate_adr_authority.py --check` (REQ-004; `config/adr_authority.toml`)
8. **Phase 8: Schema comments**
   - [ ] Rewrite the session recreate comment and add the EventBus retention comments; record the fingerprints before and after (REQ-005, REQ-006; `scripts/db/schema_sql.py`, `scripts/eventbus/schema.sql`)
9. **Phase 9: Deployment & Verification**
   - [ ] Run the validation sequence (`rules/toolchain.md`), `tools/check_db_separation.py`, and the doc checkers; after the change is committed and pushed, hand off to `skills/deploy/SKILL.md` for the `scripts/` comment changes (deploying is the user's decision; REQ-005, REQ-006; files of Phase 8)

### Release units
**Unit**: adr008-size | **Phases**: 2, 3 | **Reason**: the ADR-008 edits grow the file past its recorded size ceiling, so `check_docs_structure.py` fails until the ceiling edit lands.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| ADR-008, ADR-006, ADR-001, `adr_01_index.md` | Documentation | `uv run python tools/check_adr_structure.py`, `check_adr_reference.py`, `check_adr_invariant_matrix.py`, `check_adr_preservation.py` (report) | No findings; preservation reports recorded |
| `governance_03`, `agent_09_01`, `db_03`, `db_08` | Documentation | `uv run python tools/check_docs_structure.py` and the checkers `routing.md` Tools lists | No findings |
| `tools/check_docs_structure.py` | Unit | `uv run pytest tests/tools/test_check_docs_structure.py` | Passes |
| `config/adr_authority.toml` | Generated-file check | `uv run python tools/generate_adr_authority.py --check` | No drift |
| `scripts/db/schema_sql.py`, `scripts/eventbus/schema.sql` | Static and unit | `uv run python tools/check_db_separation.py`, `uv run pytest tests/db/test_create_schema.py tests/eventbus/ tests/tools/test_check_db_separation.py`, fingerprint comparison | No violation; identical fingerprints |
| Whole change | Full suite and coverage | `rules/toolchain.md` validation sequence; `diff-cover` records `N/A` (no Python line changes) | All pass |

## Risks
- **Risk**: The ADR-008 title and scope change breaks documents that quote the old title or rely on "four databases" (likelihood medium) → **Mitigation**: the consumer scan found three title consumers (all in the targets); `check_adr_reference.py`, `check_docs_consistency.py`, and `check_docs_structure.py` run after each edit; UNK-03 lists the two sentences intentionally left.
- **Risk**: ADR-008 growth fails the size gate between phases (likelihood high) → **Mitigation**: Phases 2 and 3 are one release unit; the ceiling is set to the accepted size.
- **Risk**: The Plan restates the maintainer's four decisions and the other databases' retention from current behavior; a misreading becomes a recorded rule (likelihood low) → **Mitigation**: all of it is a pending bullet (AAL-024 to AAL-029) that the maintainer approves or withdraws; no approval text is written.
- **Risk**: The next deployment refuses workflow and eventbus with data in them (likelihood high) → **Mitigation**: evidence recorded here (UNK-04); the operator runs the archive-and-recreate runbook; this Plan changes no production file and the report states it.
- **Risk**: A comment edit changes a schema fingerprint (likelihood low) → **Mitigation**: `_COMMENT_RE` strips comments before hashing; AC-9 compares the fingerprints before and after.
- **Risk**: Another Plan edits ADR-008, ADR-006, or `governance_03` (likelihood medium) → **Mitigation**: re-run the Acceptance Criteria searches before editing; a defect already gone is recorded with evidence and skipped.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: add ledger rows AAL-024 to AAL-029 in governance_03 | In Progress | — | — |  |
| 2 | Phase 2: ADR-008 scope, inventory, mismatch, retention, memory, references | In Progress | — | — |  |
| 3 | Phase 3: ADR-008 size ceiling in check_docs_structure.py | In Progress | — | — |  |
| 4 | Phase 4: ADR-006 conditional no-loss, retention risk, title | In Progress | — | — |  |
| 5 | Phase 5: ADR-001 terminology | In Progress | — | — |  |
| 6 | Phase 6: session guide, migration guide, active-databases guide, ADR index | In Progress | — | — |  |
| 7 | Phase 7: ARCH-003 in adr_authority.toml | In Progress | — | — |  |
| 8 | Phase 8: schema comments in schema_sql.py and schema.sql | In Progress | — | — |  |
| 9 | Phase 9: full validation and deploy hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261118-143801_01_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261118-143801_02_docs_10_adr_adr_02_05_008_db-sqlite-4db-separation.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261118-143801_03_tools_check_docs_structure.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261118-143801_04_docs_10_adr_adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261118-143801_05_docs_10_adr_adr_02_02_001_agent-workflow-engine-mandatory.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261118-143801_06_docs_23_agent_agent_09_01_data-layer-session-db.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261118-143801_07_docs_41_db_db_03_architecture_and_schema-migration-and-scaling.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261118-143801_08_docs_41_db_db_08_active_databases.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261118-143801_09_docs_10_adr_adr_01_index.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261118-143801_10_config_adr_authority.toml.md | 7 | Procedure | Pending | — | — |
| implementations/20261118-143801_11_scripts_db_schema_sql.py.md | 8 | Procedure | Pending | — | — |
| implementations/20261118-143801_12_scripts_eventbus_schema.sql.md | 8 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123008_adrchk008_db-data-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261118-142957
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`; `tools/check_docs_structure.py`; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`; `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`; `docs/23_agent/agent_09_01_data-layer-session-db.md`; `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`; `docs/41_db/db_08_active_databases.md`; `docs/10_adr/adr_01_index.md`; `config/adr_authority.toml`; `scripts/db/schema_sql.py`; `scripts/eventbus/schema.sql`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (table inventory from the DDL sources) | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | 2 | AC-1 | `tools/check_adr_structure.py` and the `rg` inventory check | Confirmed by repository evidence |
| REQ-002 | Reason for Change (references and terms) | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | 2 | AC-2 | `tools/check_adr_structure.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes (ADR-001 terminology) | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | 5 | AC-3 | `tools/check_adr_structure.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes (scope and title decision); Acceptance Criteria (ARCH-003 agrees) | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | 2 | AC-4 | `tools/check_adr_reference.py` | Explicit in issue |
| REQ-004 | Target Files (ARCH-003) | `config/adr_authority.toml` | 7 | AC-4 | `tools/generate_adr_authority.py --check` | Explicit in issue |
| REQ-004 | Title propagation (consumer scan) | `docs/10_adr/adr_01_index.md` | 6 | AC-4 | `tools/check_adr_reference.py` | Derived from confirmed evidence |
| REQ-004 | Title propagation (consumer scan) | `docs/41_db/db_08_active_databases.md` | 6 | AC-4 | `tools/check_docs_structure.py` | Derived from confirmed evidence |
| REQ-004 | Title in Related ADRs | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | 4 | AC-4 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-004 | Migration guide agrees on the database set | `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | 6 | AC-4 | `tools/check_docs_structure.py` | Derived from confirmed evidence |
| REQ-005 | Required Changes (mismatch rule per database) | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | 2 | AC-5 | `tools/check_adr_structure.py` | Explicit in issue |
| REQ-005 | Acceptance Criteria (ADR-006 no longer claims no loss unconditionally) | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | 4 | AC-5 | `tools/check_adr_structure.py` | Explicit in issue |
| REQ-005 | Required Changes (update `agent_09_01` and the comments) | `docs/23_agent/agent_09_01_data-layer-session-db.md` | 6 | AC-5 | `tools/check_docs_structure.py` | Explicit in issue |
| REQ-005 | Migration guide section 8e | `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | 6 | AC-5 | `tools/check_docs_structure.py` | Confirmed by repository evidence |
| REQ-005 | `schema_sql.py` comment says the decision is deferred | `scripts/db/schema_sql.py` | 8 | AC-9 | `tools/check_db_separation.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes (retention decision) | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | 2 | AC-6 | `tools/check_adr_structure.py` | Explicit in issue |
| REQ-006 | ADR-006 Review Trigger and retention risk | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | 4 | AC-6 | `tools/check_adr_structure.py` | Confirmed by repository evidence |
| REQ-006 | Session retention and memory prune wording | `docs/23_agent/agent_09_01_data-layer-session-db.md` | 6 | AC-6 | `tools/check_docs_structure.py` | Confirmed by repository evidence |
| REQ-006 | Storage Growth section lists unimplemented mitigations | `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | 6 | AC-6 | `tools/check_docs_structure.py` | Confirmed by repository evidence |
| REQ-006 | `dlq_outbox` rows kept as the reconciliation record | `scripts/eventbus/schema.sql` | 8 | AC-9 | `tools/check_db_separation.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes (canonical memory store) | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | 2 | AC-7 | `tools/check_adr_structure.py` | Explicit in issue |
| REQ-007 | Guide already names SQLite canonical | `docs/23_agent/agent_09_01_data-layer-session-db.md` | 6 | AC-7 | `tools/check_docs_structure.py` | Confirmed by repository evidence |
| REQ-008 | Constraints (approval record, no approval text) | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | 2 | AC-8 | `tools/check_adr_structure.py` | Explicit in issue |
| REQ-008 | Constraints (approval record, no approval text) | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | 4 | AC-8 | `tools/check_adr_structure.py` | Explicit in issue |
| REQ-008 | Pending bullets cite existing ledger ids | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | 1 | AC-8 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-008 | ADR-008 size ceiling | `tools/check_docs_structure.py` | 3 | AC-8 | `uv run pytest tests/tools/test_check_docs_structure.py` | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261118-143801 -->