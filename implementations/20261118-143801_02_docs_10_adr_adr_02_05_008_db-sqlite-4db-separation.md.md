## Goal
Record the maintainer's decisions in ADR-008 (`REQ-004` six-database scope, `REQ-005` schema-mismatch rule, `REQ-006` retention, `REQ-007` memory canonical store), add the table inventory (`REQ-001`), fix the confirmed reference errors (`REQ-002`), and show every decision-text change as pending (`REQ-008`).

## Scope
**Release unit**: adr008-size
- In scope: the ADR-008 sections named in Procedure. The size ceiling is raised by procedure 03 in the same release unit.

## Assumptions
- Procedure 01 has landed: AAL-024 to AAL-028 exist in `governance_03` Part 5.
- The six databases are four platform-domain databases (`rag`, `session`, `workflow`, `eventbus`; `DbTarget`) plus two non-domain stores (`mcp_dedup`, `mdq`). Statements true only of the four domain databases stay in four-database wording: the `SQLiteHelper` target sentence in Constraints, INV-01 to INV-08, Implementation Notes, and the four-database boundary row in Verification (Step 3a finding).
- Retention claims for the databases the maintainer did not decide are taken from current code (checked in Step 3a): `rag` documents and chunks have no automatic purge (no `DELETE FROM documents`/`chunks` in `scripts/` outside mdq); `session` has `purge_old_sessions()` on demand and a `retention_days` lazy purge of diagnostics, memory is pruned only by `/memory prune`; `workflow` has the startup-only `purge_finished_workflow_events()` (terminal tasks past the horizon; `tasks` and `attempts` are never purged); `mcp_dedup` has `purge_expired()`; `mdq` is rebuilt from the Markdown files.
- ADR-008 is 37259 bytes; the file keeps growing past its recorded ceiling until procedure 03 lands.

## Design decisions
- New Decision Details are appended as #22 (schema-mismatch rule), #23 (retention), #24 (memory canonical store) so existing citations of #1 to #21 stay valid; the Matrix gains two rows (`Schema-mismatch rule`, `Retention rule`) so each database has one rule per field.
- The `Derived Stores Outside the Four Domains` section becomes `Stores Outside the Four Platform Domains` and keeps its `mdq.sqlite` and `mcp_dedup.sqlite` bullets.

## Alternatives considered
N/A: decided by the maintainer (Plan Design, decisions 1 to 4).

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure
1. Title: change the front matter `title` and the `#` heading to `ADR-008: Separating SQLite into Six Databases`; update the `Summary` to name the four platform domains and the two non-domain stores, and change the range to `Decision Details #14 to #21`.
2. Recovery Policy Matrix: add an `mdq.sqlite` column and fill every row from the `mdq.sqlite` bullet of the stores section (not backed up or restored; rebuilt from the Markdown files by `index_paths` and `refresh_index`; owned by mdq-mcp; use `not applicable` where the `mcp_dedup` column does); change the `session.sqlite` cells: system of record `sessions`, `messages`, `memories`, `memory_links`, `session_diagnostics`; derived `memories_fts`, `memories_vec` (from `memories`); add a row `Schema-mismatch rule` and a row `Retention rule` with one cell per database (Method).
3. Decision Details: append #22, #23, #24 (Method); extend #2 with the memory canonical statement; keep #1 to #21 numbering.
4. Invariants: INV-04 names the `dlq_outbox` durable promotion record; INV-09 adds that EventBus `events`, `consumer_delivery`, and `dlq_outbox` growth is an accepted risk (Decision Detail #23).
5. Glossary: `operator-restore` cites `Decision Details #15 to #17 and #20; Invariant INV-18` (each verified against the Decision Detail text).
6. Scope: `Target data` lists the six database files; `Out of Scope` drops the `mdq.sqlite` bullet; `Data Ownership and Persistence` names the four platform databases as systems of record and the two non-domain stores as disposable or derived, and lists `memories_fts`, `memories_vec`, and the `mdq.sqlite` contents under Derived Data.
7. Stores section: rename it to `Stores Outside the Four Platform Domains` and update the two references to the old heading.
8. Implementation References: replace the five table bullets with the inventory (Method).
9. Known Deviations: in SHARED-002 replace `(lines 92-93)` with `(Recovery Policy Matrix, system of record and derived rows)` and state that the Matrix now classifies `memories_vec` as derived, pending AAL-027; the Known Issue stays open.
10. Approval Record: add five pending bullets in the form `- **Current Decision Approval (pending)**: ... is a decision-text change awaiting maintainer approval; the approver, date, and scope are not recorded, and it is tracked by AAL-0NN. No approval is recorded here.` for AAL-024 (scope), AAL-025 (mismatch rule), AAL-026 (retention), AAL-027 (memory store), AAL-028 (INV-04).

### Method
- Decision Detail #22: every database is accepted only when its shape matches the canonical shape (shared fingerprint for `workflow`, `eventbus`, `mdq`; the create-only shape for `rag` and `session`); a refused file is archived and recreated by the operator, no migration exists, data is not carried over. Preconditions: `session` needs `/session export` and the JSONL archive (memory is recovered with `/memory rebuild`, session history is not restored); `workflow` is archived with `rotate_all_dbs()`; `eventbus` with `python -m eventbus.db_tools rotate`; `mcp_dedup` is recreated empty; `mdq` is deleted and re-indexed; `rag` is archived and the corpus re-ingested. Cite `db_03` section 8e instead of repeating the runbook.
- Decision Detail #23: EventBus `events`, `consumer_delivery`, and `dlq_outbox` rows are never deleted and grow without bound, recorded as an accepted risk; the other databases follow the retention behavior in Assumptions.
- Decision Detail #24: SQLite `memories` and `memory_links` are canonical; `memories_fts` and `memories_vec` are derived and rebuilt from `memories`; the JSONL file `memories.jsonl` is an append-only archive of memory lines and `delete`/`pin`/`unpin` change events (written after the SQLite commit), outside any database.
- Inventory (from the DDL sources): `rag`: `documents`, `chunks`, `chunks_fts`, `chunks_vec`; `session`: `sessions`, `messages`, `memories`, `memory_links`, `session_diagnostics`, `memories_fts`, `memories_vec`; `workflow`: `tasks`, `attempts`, `processed_events`, `artifacts`, `tool_call_state`; `eventbus`: `events`, `consumer_delivery`, `consumer_offsets`, `dlq_outbox`; `mcp_dedup`: `tool_call_state` (`scripts/shared/mcp_dedup.py`); `mdq`: `documents`, `chunks`, `chunks_fts`, `index_state`. Re-read the four DDL sources before writing and add any table they now define.
- `workflow` and `mcp_dedup` both own a table named `tool_call_state`; say so once to avoid confusion.

### Details
- The statements listed in Assumptions that stay four-database wording are not edited.
- Do not edit the existing `Current Decision Approval` bullets, and write no `Approved By` or date.
- `tools/check_docs_structure.py` fails on this file until procedure 03 runs (release unit).

## Compatibility considerations
- Text only; the four-database invariants and the Decision Details #1 to #21 numbering are unchanged.

## Security considerations
- No approval statement is written or simulated.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_reference.py`, `check_adr_invariant_matrix.py`, `check_adr_preservation.py` (report), `check_known_deviation_sync.py`, `check_db_separation.py`, and the checkers `routing.md` Tools lists for a `docs/` edit (`uv run python tools/run_validation_gates.py` runs the ones the changed files trigger); `check_docs_structure.py` is run after procedure 03 (release unit).
- AC-1: `rg` each table name of the DDL sources in the ADR.

## Completion criteria
- Title, Summary, Scope, Matrix, and stores section name the same six databases; the Matrix has one mismatch rule and one retention rule per database; Decision Details #22 to #24 exist; INV-04 and INV-09 are updated; glossary citations and the Summary range are correct; the inventory lists every DDL table; five pending bullets cite AAL-024 to AAL-028; the checkers report no finding (preservation reports recorded).

## Out of Scope
- ADR-006 (procedure 04), the size ceiling (procedure 03), closing SHARED-002, renaming the file, any approval text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the title, Matrix, Decision Detail, invariant, scope, reference, and approval edits (Implementation > Procedure) | Pending | — | — | |
| 2 | Run the ADR and documentation checkers (Validation plan) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008
- **Source issue**: issues/20261117-123008_adrchk008_db-data-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-142957_adrchk008_db-data-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-143801
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
