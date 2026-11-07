## Goal

- Delete `tests/deploy/test_init_db_ledger_gate.py` (338 lines) — the integration test of the ledger-presence gate that the Plan inverts (REQ-007 / AC-002: the removed gate's test is replaced by the marker-absence gate test).

## Scope
**Release unit**: current-schema-only-cutover

- Whole-file test deletion in Phase 1, simultaneous with the creation of its replacement `tests/deploy/test_init_db_schema_gate.py` (own document, seq 18; named by two rows so not a companion here).

## Assumptions

- The module also covers the opt-in `RUN_RECOVERY_DRILL=1` hook (its docstring, REQ-007 drill hook of the deploy script); the replacement document 18 carries that hook coverage forward so no deploy-script coverage is lost.

## Design decisions

- Delete-and-replace in one Phase 1 commit (Plan Phase 1 names both actions together), rather than editing in place: the sandbox driver is reusable but the assertions invert (ledger present → FATAL becomes marker present → FATAL), matching document 12's gate rewrite.

## Alternatives considered

- Editing this file into the new gate test: rejected — the Plan lists a new file name (row 18 CREATE) and a DELETE row for this one; keeping the old name would keep "ledger gate" vocabulary in the suite.

## Implementation
### Target file
`tests/deploy/test_init_db_ledger_gate.py`

### Procedure
1. `git rm tests/deploy/test_init_db_ledger_gate.py` in the Phase 1 commit, together with document 18 creating the replacement (Plan Phase 1).

### Method
- Port the sandbox driver pattern (DEPLOY_SCRIPTS/DEPLOY_DB/LLMAGENT_CONFIG_DIR overrides, config copy under `tmp_path`) into document 18's file before deleting this one.

### Details
- No other file changes in this document.

## Compatibility considerations

- N/A: test-only deletion.

## Security considerations

- N/A: test-only deletion.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `grep -rn "test_init_db_ledger_gate" tests/ tools/ .github/` — no residual reference after deletion.
- `uv run pytest tests/deploy/` — replacement test (document 18) covers the gate after document 12 lands.

## Completion criteria

- The file is absent, its driver pattern survives in the replacement test, and no suite entry references it (AC-002, AC-003).

## Out of Scope

- The gate inversion itself — sibling document 12.
- The replacement test file — own document (seq 18).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Port sandbox driver into document 18, then `git rm tests/deploy/test_init_db_ledger_gate.py` (Plan Phase 1) | Completed | — | — | Release unit "current-schema-only-cutover" Driver pattern ported into test_init_db_schema_gate.py (config rewrite, stub scripts, uv subprocess env), then git rm. Only remaining textual reference is the new module's docstring provenance note. |
| 2 | Verify no residual reference (grep) | Completed | — | — | grep: no residual suite/CI references. |

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
- **Requirement ID**: REQ-007 (replace the removed gate's tests), REQ-005 (deploy gate inversion it tests)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-081028
- **Related target files**: `tests/deploy/test_init_db_ledger_gate.py`