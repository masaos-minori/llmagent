## Goal

- Update the deployment runbook to the post-cutover behavior: remove the "Records the schema version" claim and the removed `Workflow schema version mismatch` FATAL row, and align the init_db/setup_services prose with the fixed refusal wording (amended plan row: REQ-009).

## Scope
**Release unit**: current-schema-only-cutover

- Prose-only edits in `docs/90_deployment/deployment_01_deployment.md`; the behaviors it documents are implemented by siblings 06, 07, 10, 12, 30.

## Assumptions

- Stale spots verified 2026-11-07: line 306 `- Records the schema version` (init_db.sh bullet list — after sibling 12 init_db.sh records nothing), line 343 failure-table row `[FATAL] Workflow schema version mismatch: expected <X>, found <Y>.` (setup_services.sh — gate removed by sibling 30), and prose lines 299-310 mixing correct (eventbus `PRAGMA user_version`, fingerprint gate) with removed claims ("it refuses to record the current version over a different one" — recording no longer exists; the stamp-compare refusal belongs to `create_eventbus_schema()`/`_init_schema`, siblings 06/07).
- Fixed refusal wording is the single guidance sentence used by all gates (siblings 06/07/10/12).

## Design decisions

- Preserve the correct current-state sentences (eventbus `PRAGMA user_version` self-stamp in schema.sql, fingerprint `assert_matches()` gate, rotate-then-delete recreate order) and touch only the removed-behavior claims — no broad rewrite (repo rule 5).

## Alternatives considered

- Rewriting the whole init_db/setup_services section: rejected — most of it already matches post-cutover behavior verified during Phase 1-3 implementation.

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md`

### Procedure
1. Apply the three edits (Method); grep-verify no version-recording or old-message claims remain in the file.
2. Run the docs checks and the docs-tree grep sweep.

### Method
- Delete the `- Records the schema version` bullet (line 306).
- Failure table (line 343): replace the removed `[FATAL] Workflow schema version mismatch...` row with the refusal the deployment scripts actually emit — the init_db.sh/setup_services.sh gate line quoting "does not match the current schema" / legacy marker guidance, response "archive the existing database if required, remove or rename it, and create a new database using the current schema".
- Prose (lines 299-310): adjust "it refuses to record the current version over a different one" to the post-cutover refusal (an existing stamped or marker-carrying database is refused by the create/startup gates; nothing is recorded during init_db.sh).

### Companion test files
- N/A: documentation-only change (Plan Phase 4 docs rows carry no pytest companions).

## Compatibility considerations

- The failure table is also referenced from `docs/23_agent/agent_10_04...md` (sibling 33) — keep cross-reference anchors intact.

## Security considerations

- Guidance names paths and the manual recreate procedure, no credentials.

## Rollback considerations

- Revert the commit restores the previous runbook text (single-commit change within the release unit).

## Validation plan

- `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py docs/90_deployment/deployment_01_deployment.md`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_consistency.py` (docs gate; corrected 2026-11-07 — `check_docs_crossrefs.py` and `check_docs_index.py` do not exist in `tools/`).
- `grep -n "Records the schema version\|Workflow schema version mismatch" docs/90_deployment/deployment_01_deployment.md` returns no hits.

## Completion criteria

- The runbook describes only current-schema-only behavior: no version recording, fixed refusal wording in the failure table, archive-before-remove recreate order (AC-009).

## Out of Scope

- Gate implementations — siblings 06, 07, 10, 12, 30.
- `docs/23_agent/agent_10_04...md` troubleshooting text — sibling 33.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the three stale-claim edits (Plan Phase 4) | Completed | — | 20261107-132408 | Release unit "current-schema-only-cutover" version bullet+failure row+prose+checklist+setup_services bullet rewritten to marker-refusal wording; extra stale bullet at setup_services responsibilities fixed |
| 2 | Run docs checkers green | Completed | — | 20261107-132408 | all checkers green; SIZE_EXCEPTIONS ceiling re-recorded 26347->26761 per checker's documented process; Validation plan corrected (crossrefs/index tools do not exist) |
| 3 | Run the validation sequence (`rules/toolchain.md`) in the Phase 5 unit pass | Completed | — | 20261107-134719 | grep sweep: no hits; four docs checkers green |

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
- **Requirement ID**: REQ-009 / AC-009 (documentation reflects current-schema-only policy)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md (amended 2026-11-07, fallout row)
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-135500
- **Related target files**: `docs/90_deployment/deployment_01_deployment.md`