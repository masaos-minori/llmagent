## Goal

- Update the agent workflow troubleshooting document to the current-schema-only gate: remove the `workflow_schema_version` diagnostic query and replace the "Schema Version Mismatch" section with the legacy-marker refusal guidance (fixed refusal wording, archive-and-recreate procedure) (amended plan row: REQ-009).

## Scope
**Release unit**: current-schema-only-cutover

- Prose-only edit in `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md`; the gate behavior it documents is implemented by sibling 10 (`scripts/agent/services/workflow_schema.py`).

## Assumptions

- Stale spots verified 2026-11-07: line 52-55 diagnostic block (`# Check workflow DB schema tables and versions` + `sqlite3 <workflow_db_path> "SELECT * FROM workflow_schema_version ORDER BY applied_at DESC;"`) and lines 89-93 (`#### Schema Version Mismatch` symptom quoting `Workflow schema version mismatch: expected <X>, found <Y>` with response "Re-run the deployment scripts to apply migrations").
- The gate now refuses marker-carrying databases with `Legacy migration marker table(s) present: ...` + the fixed refusal wording (sibling 10); marker-free current-shape databases pass with no version comparison.

## Design decisions

- Keep the section heading structure (`#### <Symptom>`) and replace content in place instead of deleting the section: operators still hit legacy databases at startup and need the refusal response documented (AC-009).

## Alternatives considered

- Deleting the section entirely: rejected — the failure mode (legacy DB refused at startup) still exists after the cutover; only its message and remediation change.

## Implementation
### Target file
`docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md`

### Procedure
1. Rewrite the two stale spots (Method); grep-verify no other `workflow_schema_version`/`migrate` guidance remains in the file.
2. Run the docs checks and re-grep the docs tree for the removed message.

### Method
- Diagnostic block (lines 52-55): drop the `workflow_schema_version` SELECT and the "and versions" comment; keep `.tables` inspection, optionally showing that `schema_migrations`/`workflow_schema_version` must be absent.
- `#### Schema Version Mismatch` (lines 89-93): retitle to the refusal the gate actually emits (e.g. `#### Legacy Migration Marker Refusal`); symptom quotes `Legacy migration marker table(s) present: ...` from `check_workflow_schema`; response states the fixed procedure: stop the service, archive the existing database if required, remove or rename it, and create a new database with the current schema — no migration is attempted (AC-005, AC-006).

### Companion test files
- N/A: documentation-only change (Plan Phase 4 docs rows carry no pytest companions).

## Compatibility considerations

- Cross-link from `docs/90_deployment/deployment_01_deployment.md` line 346 points at the "Workflow Deployment Runbook" anchor in this file — keep that anchor heading unchanged (sibling 34 owns the cross-linking doc).

## Security considerations

- Failure guidance names paths and the manual recreate procedure, no credentials (REQ-004 style).

## Rollback considerations

- Revert the commit restores the previous troubleshooting text (single-commit change within the release unit).

## Validation plan

- `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_consistency.py --domain agent` (docs gate; corrected 2026-11-07 — `check_docs_crossrefs.py` and `check_docs_index.py` do not exist in `tools/`).
- `grep -rn "Workflow schema version mismatch" docs/` returns no hits in this file after siblings 32/34 land (final sweep gate in Phase 5).

## Completion criteria

- The document contains no `workflow_schema_version` query or version-mismatch symptom, and documents the marker refusal with the fixed archive-and-recreate wording (AC-009).

## Out of Scope

- Gate implementation — sibling 10.
- `docs/90_deployment/deployment_01_deployment.md` failure table — sibling 34.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the diagnostic block and mismatch section (Plan Phase 4) | Completed | — | 20261107-132027 | Release unit "current-schema-only-cutover" marker-absence comment replaces SELECT; Schema Version Mismatch -> Legacy Migration Marker Refusal with literal gate messages |
| 2 | Run docs checkers green | Completed | — | 20261107-132027 | quality/structure/content-policy/consistency --domain agent green; Validation plan corrected (crossrefs/index tools do not exist) |
| 3 | Run the validation sequence (`rules/toolchain.md`) in the Phase 5 unit pass | Completed | — | 20261107-134719 | grep sweep: no hits; docs consistency, structure, quality, content-policy green (the crossref and index checkers named in the plan do not exist; the four real docs checkers were used) |

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
- **Related target files**: `docs/23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md`