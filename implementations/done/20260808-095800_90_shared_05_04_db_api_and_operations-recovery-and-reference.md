## Goal
- Restructure `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` to remove overly detailed call-site code examples, dataclass definitions, full error behavior mapping tables, DB recreation procedure shell command details, test command lists, and AI reference tables while explicitly preserving recover_corruption intended scope, known limitation when passing workflow/eventbus, known issue of DatabaseError propagation on physical corruption, DB recreation doesn't migrate existing data, archive needed before recreation, schema initialization is idempotent but doesn't transform existing data, validation plan as high-level quality gate.

## Scope
- **In-Scope**: 
  - `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/DB chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and this chapter should describe recovery operation boundaries as authoritative reference
- Scope limitations and known issue statements must not be weakened (operators depend on this information during actual incidents)
- Existing internal links and cross-references must remain valid after editing

## Design decisions
### Part 1 (Recovery):
- Compress Section 9 recover_corruption call site code example (lines 26-42): replace with prose describing recovery API usage at conceptual level
- Compress Section 9 RecoveryResult dataclass definition (lines 46-53): replace with prose describing result structure
- Compress Section 10 error behavior mapping table (lines 59-68): replace with prose describing each error type's handling
- Compress Section 11 DB recreation procedure shell commands (lines 78-109): replace with prose describing recreation steps
- Compress Section 12 test command list (lines 115-129): replace with prose describing verification approach
- Compress Section 13 AI reference table (lines 135-145): replace with prose descriptions where tabular format adds no reference value beyond what's already described in other sections
- Preserve: recover_corruption intended scope, known limitation when passing workflow/eventbus, known issue of DatabaseError propagation on physical corruption, DB recreation doesn't migrate existing data, archive needed before recreation, schema initialization is idempotent but doesn't transform existing data, validation plan as high-level quality gate

## Alternatives considered
- Remove Section 9 entirely: rejected — recovery operation boundaries are fundamental architecture decision
- Replace all tables with prose: rejected — tabular format for error handling is efficient for reference
- Remove Section 11 entirely: rejected — DB recreation procedure is critical operational guidance
- Remove Section 12 entirely: rejected — verification plan as high-level quality gate is important

## Implementation
### Target files
- `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`

### Procedure
1. **Phase 1: Preparation**
   - Analyze current document structure and identify which recovery and reference design judgments are scattered across sections
   - Check SHARED-001 related section to identify duplicate known issues

2. **Phase 2: Core Logic Implementation**
   - Part 1: Compress Section 9 recover_corruption call site code example (lines 26-42)
   - Part 1: Compress Section 9 RecoveryResult dataclass definition (lines 46-53)
   - Part 1: Compress Section 10 error behavior mapping table (lines 59-68)
   - Part 1: Compress Section 11 DB recreation procedure shell commands (lines 78-109)
   - Part 1: Compress Section 12 test command list (lines 115-129)
   - Part 1: Compress Section 13 AI reference table (lines 135-145)
   - Preserve: recover_corruption intended scope, known limitation when passing workflow/eventbus, known issue of DatabaseError propagation on physical corruption, DB recreation doesn't migrate existing data, archive needed before recreation, schema initialization is idempotent but doesn't transform existing data, validation plan as high-level quality gate

3. **Phase 3: Deployment & Verification**
   - Confirm scope limitations and known issue statements not weakened
   - Confirm no duplication with SHARED-001
   - Confirm cross-references to `scripts/db/recovery.py` exist
   - Validate internal Markdown links and cross-references
   - Confirm compliance with post-edit chapter structure template from `memo-doc-shared-review.md`

### Method
- Table reduction: convert full-field tables to category-level descriptions
- Code block removal: replace inline Python definitions with prose summaries of field semantics
- Pseudo-code removal: replace procedural pseudo-code with behavioral descriptions
- Prose compression: convert field-by-field enumeration to grouped descriptions by purpose

### Details
#### Part 1 (Recovery):
- Section 9 (Corruption Recovery): replace with prose: "from db.recovery import recover_corruption; from db.models import RecoveryResult; result = recover_corruption(backup_path='/opt/llm/db/backup/rag.sqlite', target='rag', dry_run=False). target assumes only 'rag' (default) or 'session'; implementation uses two-way branch checking target=='rag' to determine db_path for display purposes, so passing 'workflow' or 'eventbus' causes fallback to session_db_path on display while actual DB connection resolved by string ('workflow'/'eventbus') passed to SQLiteHelper(target); both mismatching, do not pass anything other than 'rag'/'session' to target (Explicit in code — db/recovery.py::recover_corruption). RecoveryResult(dataclass frozen=True): success bool, action str ('vacuum'|'vacuum_failed'|'restored'|'no_backup'|'error'), detail str|None, dry_run bool=False."
- Section 10 (Error Handling): replace with prose: "sqlite3.OperationalError (busy/locked): automatic wait via PRAGMA busy_timeout (default 30 seconds); sqlite3.IntegrityError: propagates to caller; does not occur in upsert path; sqlite-vec load error: sqlite3.OperationalError → connection failure; schema DDL failure: exception re-thrown from executescript(); integrity check failure: log error + attempt restore from backup; prune_old_memories failure: STRICT — exception propagates; BEST_EFFORT — returns MaintenanceResult(success=False); commit() error: WARNING logged + sqlite3.OperationalError re-thrown; close() error: WARNING logged only; no exception thrown."
- Section 11 (DB Recreation): replace with prose: "Schema change requires DB recreation — migration feature does not exist. Step 1: Archive — execute rotate_all_dbs() to archive all three production DBs. Step 2: Delete — manually delete DB files; paths resolved from agent.toml rag_db_path/session_db_path/workflow_db_path/eventbus_db_path keys (db/config.py::DbConfig); create_schema() also recreates eventbus.sqlite, so include /opt/llm/db/eventbus.sqlite if deleting (Explicit in code — db/create_schema.py). Step 3: Recreate — execute create_schema() to initialize empty DBs. Important notes: recreated DB is empty — existing records not automatically migrated; create_schema() is wrapper calling create_rag_schema()→create_session_schema()→create_workflow_schema()→create_eventbus_schema() unconditionally sequentially; each schema DDL protected by IF NOT EXISTS so idempotent even against existing files (Explicit in code — db/create_schema.py); condition 'initialize only if eventbus.sqlite does not exist' does not exist in implementation; if only one DB needs recreation use individual functions: create_rag_schema(), create_session_schema(), create_workflow_schema(), create_eventbus_schema()."
- Section 12 (Verification Plan): replace with prose: "Schema initialization: pytest tests/test_create_schema.py; DB maintenance: pytest tests/test_db_maintenance.py; Type check: mypy scripts/db/; Full integration: create DB → check all tables exist — python -c 'from db.create_schema import create_schema; create_schema()'; sqlite3 /opt/llm/db/rag.sqlite '.tables'; sqlite3 /opt/llm/db/session.sqlite '.tables'."
- Section 13 (AI Reference Guide): replace with prose: "Open DB connection: with SQLiteHelper('rag').open(row_factory=True) as db:. Write atomically: open(write_mode=True) context within with db.begin_immediate():. What does target='workflow' connect to: workflow.sqlite — task tracking DB. How to validate embedding BLOB: db.store's validate_embedding_blob(blob). How to purge old sessions: purge_old_sessions(db, RetentionConfig(...)) — returns MaintenanceResult; check .success. How to recover from corruption: recover_corruption(backup_path=..., target='rag'). Does prune_old_memories catch exceptions: STRICT (default) — propagates; BEST_EFFORT — caught and stored in MaintenanceResult. How to use BEST_EFFORT mode: pass mode=MaintenanceMode.BEST_EFFORT to vacuum_db, purge_old_sessions, prune_old_memories. How to verify RAG consistency: check_rag_consistency(db) → is_consistent(report) + summarize_issues(report)."
- Remove Related Documents and Keywords sections — content duplicated in frontmatter

## Compatibility considerations
- Cross-references to `scripts/db/recovery.py`, `scripts/db/models.py`, `scripts/db/rotation.py`, `scripts/db/create_schema.py`, `scripts/db/config.py`, `scripts/db/helper.py`, `scripts/db/maintenance.py`, `scripts/db/store.py`, `scripts/db/store_protocols.py`, `scripts/db/store_impl.py`, `scripts/db/rag_consistency.py` must remain valid after restructuring
- Internal Markdown links must be verified against actual file paths in `docs/90_shared_*` directories
- No change to source code contracts — document-only modification

## Security considerations
- N/A — document-only modification, no security-sensitive content affected

## Rollback considerations
- If restructuring causes link breakage, revert to original structure and apply targeted compression instead of full rewrite
- All removed details point to source files for verification

## Validation plan
| Check | Tool | Target |
|---|---|---|
| recover_corruption Scope Limitation | Manual | Explicitly preserved |
| Physical-Corruption Exception Propagation | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to scripts/db/recovery.py |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |

## Out of scope
- Source code changes
- Test modifications
- Cross-chapter structural changes beyond this file
- Auto-generation of documentation (future work)

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-212947_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-095800
- Related target files: docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md
