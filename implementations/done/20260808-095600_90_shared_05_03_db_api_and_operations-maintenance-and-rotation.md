## Goal
- Restructure `docs/90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md` to remove overly detailed function signatures, dataclass definitions, purge/prune verbose processing explanations, rotation function lists, RagConsistencyReport full field listings, and usage example code while explicitly preserving maintenance function operational purposes, STRICT vs BEST_EFFORT distinction, result.success check required under BEST_EFFORT, WAL checkpoint/VACUUM/purge/prune operational notes, DB rotation backup/archive purpose, SQLite online backup API preserves WAL integrity, RAG consistency check is read-only and doesn't repair, operational judgment when FTS/vec inconsistency found, embed_failed is caller-provided information (not auto-detected).

## Scope
- **In-Scope**: 
  - `docs/90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/DB chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and this chapter should describe maintenance operation boundaries as authoritative reference
- BEST_EFFORT result-checking requirement must not be weakened (silent failure risk)
- Existing internal links and cross-references must remain valid after editing

## Design decisions
### Part 1 (Maintenance Functions):
- Compress Section 7 maintenance function signature table (lines 27-32): replace with prose describing each function's operational purpose
- Compress Section 7 MaintenanceMode/MaintenanceResult dataclass definitions (lines 40-52): replace with prose describing mode semantics and result structure
- Compress Section 7 RetentionConfig dataclass definition (lines 74-78): replace with prose describing config parameters
- Compress Section 7 purge_old_sessions behavior steps (lines 83-89): replace with prose describing purge logic at conceptual level
- Compress Section 7 prune_old_memories behavior steps (lines 91-97): replace with prose describing prune logic at conceptual level
- Compress Section 7a rotation function list (lines 103-123): replace with prose describing rotation capabilities
- Compress Section 7b RagConsistencyReport full field listing (lines 152-166): replace with prose describing report fields by category
- Compress Section 7b is_consistent determination condition (lines 174-182): replace with prose describing consistency criteria
- Compress Section 7b usage example code (lines 186-193): replace with prose describing usage pattern
- Compress Section 7b recovery flow pseudo-code (lines 201-205): replace with prose describing recovery sequence
- Preserve: maintenance function operational purposes, STRICT vs BEST_EFFORT meaning, result.success check required under BEST_EFFORT, WAL checkpoint/VACUUM/purge/prune operational notes, DB rotation backup/archive purpose, SQLite online backup API preserves WAL integrity, RAG consistency check is read-only and doesn't repair, operational judgment when FTS/vec inconsistency found, embed_failed is caller-provided information (not auto-detected)

## Alternatives considered
- Remove Section 7 entirely: rejected — maintenance operation boundaries are fundamental architecture decision
- Replace all tables with prose: rejected — tabular format for function signatures is efficient for reference
- Remove Section 7b entirely: rejected — RAG consistency check operational role is critical for understanding data integrity monitoring

## Implementation
### Target files
- `docs/90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md`

### Procedure
1. **Phase 1: Preparation**
   - Analyze current document structure and identify which maintenance and rotation design judgments are scattered across sections

2. **Phase 2: Core Logic Implementation**
   - Part 1: Compress Section 7 maintenance function signature table (lines 27-32)
   - Part 1: Compress Section 7 MaintenanceMode/MaintenanceResult dataclass definitions (lines 40-52)
   - Part 1: Compress Section 7 RetentionConfig dataclass definition (lines 74-78)
   - Part 1: Compress Section 7 purge_old_sessions behavior steps (lines 83-89)
   - Part 1: Compress Section 7 prune_old_memories behavior steps (lines 91-97)
   - Part 1: Compress Section 7a rotation function list (lines 103-123)
   - Part 1: Compress Section 7b RagConsistencyReport full field listing (lines 152-166)
   - Part 1: Compress Section 7b is_consistent determination condition (lines 174-182)
   - Part 1: Compress Section 7b usage example code (lines 186-193)
   - Part 1: Compress Section 7b recovery flow pseudo-code (lines 201-205)
   - Preserve: maintenance function operational purposes, STRICT vs BEST_EFFORT meaning, result.success check required under BEST_EFFORT, WAL checkpoint/VACUUM/purge/prune operational notes, DB rotation backup/archive purpose, SQLite online backup API preserves WAL integrity, RAG consistency check is read-only and doesn't repair, operational judgment when FTS/vec inconsistency found, embed_failed is caller-provided information (not auto-detected)

3. **Phase 3: Deployment & Verification**
   - Confirm BEST_EFFORT result-checking requirement not weakened
   - Confirm RAG consistency check is read-only clearly stated
   - Confirm cross-references to `scripts/db/maintenance.py`, `scripts/db/rotation.py`, `scripts/db/rag_consistency.py` exist
   - Validate internal Markdown links and cross-references
   - Confirm compliance with post-edit chapter structure template from `memo-doc-shared-review.md`

### Method
- Table reduction: convert full-field tables to category-level descriptions
- Code block removal: replace inline Python definitions with prose summaries of field semantics
- Pseudo-code removal: replace procedural pseudo-code with behavioral descriptions
- Prose compression: convert field-by-field enumeration to grouped descriptions by purpose

### Details
#### Part 1 (Maintenance Functions):
- Section 7 (maintenance functions): replace with prose: "All functions accept SQLiteHelper instance and delegate low-level operations to it. checkpoint_wal(db, mode=None) → WalCheckpointCounts: flushes WAL; default mode from agent.toml::sqlite_wal_checkpoint_mode (default TRUNCATE); invalid string raises ValueError via SQLiteHelper.checkpoint() _CHECKPOINT_MODES check. vacuum_db(db, mode=STRICT) → MaintenanceResult: delegates to db.vacuum(); call outside transaction. purge_old_sessions(db, cfg=None, mode=STRICT) → MaintenanceResult: age-based + count-based session purge; commits internally. prune_old_memories(db, older_than_days, mode=STRICT) → MaintenanceResult: deletes old memories via SQLiteMemoryDeleteStore."
- Section 7 (MaintenanceMode/MaintenanceResult): replace with prose: "MaintenanceMode(StrEnum): STRICT='strict' (exceptions propagate, default, preserves existing behavior), BEST_EFFORT='best_effort' (exceptions caught, logged, returned in MaintenanceResult). MaintenanceResult(dataclass frozen=True): success bool, action str ('vacuum'|'vacuum_failed'|'purge'|'purge_failed'|'prune'|'prune_failed'), mode MaintenanceMode, detail str|None (exception message on failure), data dict|None (e.g. {'age_deleted': N, 'count_deleted': N} or {'deleted': N}). Mode semantics: STRICT (default): same behavior as before mode introduction — exceptions propagate directly; success returns MaintenanceResult(success=True). BEST_EFFORT: exceptions caught, logged as ERROR, returned as MaintenanceResult(success=False, detail=str(exc)); caller MUST check result.success. Usage: from db.maintenance import MaintenanceMode, MaintenanceResult, vacuum_db; result = vacuum_db(db); assert result.success (STRICT); result = vacuum_db(db, mode=MaintenanceMode.BEST_EFFORT); if not result.success: logger.error('vacuum failed: %s', result.detail)."
- Section 7 (RetentionConfig): replace with prose: "RetentionConfig(dataclass frozen=True): max_sessions int=100 (max sessions to retain), max_age_days int=90 (purge sessions older than N days, 0=disabled). RetentionConfig.from_config() reads agent.toml::sqlite_retention_max_sessions / sqlite_retention_max_age_days."
- Section 7 (purge_old_sessions): replace with prose: "Behavior: if max_age_days > 0, delete sessions older than N days (age_deleted); if remaining count exceeds max_sessions, delete oldest excess sessions (count_deleted); assumes messages has ON DELETE CASCADE set; calls db.conn.commit() last; returns MaintenanceResult(success=True, data={'age_deleted': N, 'count_deleted': N})."
- Section 7 (prune_old_memories): replace with prose: "Behavior: collect memory_ids older than older_than_days; delete from memories/memories_fts/memories_vec; call db.commit(); return MaintenanceResult(success=True, data={'deleted': N}); on failure: STRICT mode propagates exception; BEST_EFFORT returns success=False."
- Section 7a (rotation): replace with prose: "from db.rotation import rotate_session_db, rotate_workflow_db, rotate_all_dbs, rotate_db; Archive only session DB: session_dest = rotate_session_db(); Archive rag+session DBs: rag_dest, session_dest = rotate_db(); Archive all three DBs: rag_dest, session_dest, workflow_dest = rotate_all_dbs(). Function list: rotate_session_db(archive_dir=None)→Path — archive session.sqlite with timestamp suffix via SQLite online backup API; rotate_workflow_db(archive_dir=None)→Path — archive workflow.sqlite with timestamp suffix; rotate_all_dbs(archive_dir=None)→tuple[Path,Path,Path] — archive all three DBs, returns (rag_dest, session_dest, workflow_dest); rotate_db(archive_dir=None)→tuple[Path,Path] — archive both rag and session DBs, returns (rag_dest, session_dest). Archive directory defaults to /opt/llm/db/archive (from agent.toml::sqlite_archive_dir). Rotate archive format: {stem}_{YYYYMMDD_HHMMSS}{suffix} in archive_dir (default: agent.toml::sqlite_archive_dir → /opt/llm/db/archive). Uses SQLite online backup API to preserve WAL integrity."
- Section 7b (RAG Consistency Checks): replace with prose: "from db.rag_consistency import RagConsistencyReport, check_rag_consistency, is_consistent, summarize_issues; with SQLiteHelper('rag').open() as db: report: RagConsistencyReport = check_rag_consistency(db); if not is_consistent(report): for issue in summarize_issues(report): print(issue). Function list: check_rag_consistency(db, embed_failed=0)→RagConsistencyReport — read-only: chunks/FTS/vec row counts + orphan detection; is_consistent(report)→bool — True if no orphans and FTS gap=0; summarize_issues(report)→list[str] — human-readable issue descriptions. check_rag_consistency stores embed_failed (embedding failures known to caller, default 0) into RagConsistencyReport.embed_failed without detecting embedding failures itself. RagConsistencyReport(dataclass frozen=True): chunks int, fts int, vec int, orphan_vec_count int, fts_gap int (chunks-fts; positive=missing FTS entries), fts_orphan_count int (fts-chunks; positive=extra FTS entries, data loss risk), embed_failed int=0 (embedding failures during ingestion, caller-supplied informational), issues tuple[str,...]=() (summarize_issues(report) result; check_rag_consistency fills automatically), affected_chunk_ids tuple[int,...]|None (chunk_ids missing from FTS, max 10), affected_doc_ids tuple[int,...]|None (doc_ids those chunks belong to, max 10), affected_orphan_chunk_ids tuple[int,...]|None (chunk_ids only in chunks_vec, max 10), affected_orphan_urls tuple[str,...]|None (orphan vec row source URLs, max 10). affected_* fields are diagnostic identifier lists filled only when fts_gap>0 or orphan_vec_count>0 (otherwise None). issues auto-filled by check_rag_consistency calling summarize_issues(report) internally — caller can get same content from report.issues without separate summarize_issues() call. is_consistent determination criteria (implementation basis): fts_gap==0 and fts_orphan_count==0 and orphan_vec_count==0 and vec==chunks. Document summary 'no orphans and FTS gap=0' is simplification; actually includes vec==chunks (vector count and chunk count exact match). Operational judgment when inconsistencies found: fts_gap>0 → FTS trigger missed some inserts; fix: /session rag-rebuild-fts; fts_orphan_count>0 → FTS has more entries than chunks ([CRITICAL]); data loss risk; fix: /session rag-rebuild-fts immediately; orphan_vec_count>0 → vec trigger failed; fix: re-ingest affected URLs with ingester.py --force; vec!=chunks (non-orphan mismatch) also reported as [WARNING], also prompts re-ingestion with ingester.py --force. Read-only; does not repair inconsistencies. Recovery flow: PRAGMA integrity_check on target DB; dry_run=True → return result without modifying DB; result 'ok' → run VACUUM; return action='vacuum' (or 'vacuum_failed'); result not 'ok' → archive corrupt file as {stem}_corrupt_{timestamp}{suffix}; copy backup_path; return action='restored' (or 'no_backup'/'error')."
- Remove Related Documents and Keywords sections — content duplicated in frontmatter

## Compatibility considerations
- Cross-references to `scripts/db/maintenance.py`, `scripts/db/rotation.py`, `scripts/db/rag_consistency.py`, `scripts/db/helper.py`, `scripts/db/config.py`, `scripts/db/store.py`, `scripts/db/store_protocols.py`, `scripts/db/store_impl.py` must remain valid after restructuring
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
| BEST_EFFORT Result-Checking Requirement | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to scripts/db/maintenance.py / scripts/db/rotation.py / scripts/db/rag_consistency.py |
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
- Source plan: plans/20260807-212008_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-095600
- Related target files: docs/90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md
