## Goal

- Create `tests/deploy/test_init_db_schema_gate.py` — the replacement deploy-gate integration test: `deploy/init_db.sh` fails on databases carrying legacy marker tables and passes on marker-free current-shape databases (REQ-005 / AC-002).

## Scope
**Release unit**: current-schema-only-cutover

- New test file (Phase 1, written RED against the current script), reusing the sandbox driver of the deleted `tests/deploy/test_init_db_ledger_gate.py` (document 17).

## Assumptions

- The sandbox recipe of the old module is valid as-is: `init_db.sh` honors `DEPLOY_SCRIPTS`/`DEPLOY_DB`/`LLMAGENT_CONFIG_DIR` overrides; nothing under `/opt/llm/db` is touched (old module docstring, ported per document 17).
- The test is RED until document 12 inverts the gate in Phase 3 — intentional within the release unit.

## Design decisions

- New file name (row 18 CREATE) instead of editing the ledger-gate module: keeps deploy-test vocabulary aligned with the marker-absence gate (document 17 Design decisions).

## Alternatives considered

- Extending `tests/deploy/test_init_db_eventbus_schema.py`: rejected — that file covers fingerprint derivation for fresh init, not the legacy-database gate matrix.

## Implementation
### Target file
`tests/deploy/test_init_db_schema_gate.py` (new)

### Procedure
1. Copy the sandbox driver (config rewrite, throwaway db dir under `tmp_path`, uv-spawned subprocess handling) from `tests/deploy/test_init_db_ledger_gate.py` before document 17 deletes it (Plan Phase 1).
2. Write the gate cases (below); run and confirm RED against the un-inverted script.

### Method
- Case matrix: (a) `workflow.sqlite` seeded with `schema_migrations` → script exits non-zero, `[FATAL]` marker message on stderr; (b) `workflow.sqlite` seeded with `workflow_schema_version` → same; (c) `eventbus.sqlite` seeded with `schema_migrations` → same; (d) both marker-free current-shape (created by the sandboxed `create_schema.py` path once siblings land; before that, seed canonical DDL text directly) → script gate passes; (e) seeded databases' file hashes unchanged by the FATAL run (AC-005 at deploy level); (f) carry over the `RUN_RECOVERY_DRILL=1` opt-in hook coverage from the deleted module.
- Assertion strings follow document 12's fixed guidance text (archive → remove/rename → recreate), not the deleted CLI bootstrap strings.

### Details
- No fixture may touch `/opt/llm/db` or live archives (Plan Phase 1 note: scratch-database recipe, never run against `/opt/llm/`).

## Compatibility considerations

- Runs only against sandbox copies; deploy behavior for operators is guidance text (REQ-004).

## Security considerations

- Test fixtures use throwaway paths only.

## Rollback considerations

- N/A: revert the commit (new file).

## Validation plan

- `uv run pytest tests/deploy/test_init_db_schema_gate.py` — RED in Phase 1 (against the ledger gate), green after document 12 (Plan Validation plan row: marker present → FATAL; marker-free → OK).
- `uv run pytest tests/deploy/` — whole deploy suite green in the Phase 5 unit pass.

## Completion criteria

- The matrix (a)-(f) passes against the inverted gate and each rejection run leaves the seeded database byte-identical (AC-002, AC-005).

## Out of Scope

- The gate inversion in `deploy/init_db.sh` — sibling document 12.
- Deleting the old ledger-gate test — sibling document 17.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the file with sandbox driver ported from the ledger-gate module (Plan Phase 1) | Completed | — | — | Release unit "current-schema-only-cutover": intentionally RED until document 12 Created with matrix (a)-(f): marker-free pass, workflow marker x2 param, eventbus marker, no-write hash checks, RUN_RECOVERY_DRILL hook carried over. Confirmed RED (5 failed) against the ledger gate, green after doc 12 inversion. 5 passed, ruff clean. |
| 2 | Confirm expected RED against the current ledger gate | Completed | — | — | Created with matrix (a)-(f): marker-free pass, workflow marker x2 param, eventbus marker, no-write hash checks, RUN_RECOVERY_DRILL hook carried over. Confirmed RED (5 failed) against the ledger gate, green after doc 12 inversion. 5 passed, ruff clean. |
| 3 | After document 12 lands, confirm green | Completed | — | — | Created with matrix (a)-(f): marker-free pass, workflow marker x2 param, eventbus marker, no-write hash checks, RUN_RECOVERY_DRILL hook carried over. Confirmed RED (5 failed) against the ledger gate, green after doc 12 inversion. 5 passed, ruff clean. |

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
- **Requirement ID**: REQ-005 (deploy gate fails on legacy marker tables), REQ-007 (replacement test)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-081028
- **Related target files**: `tests/deploy/test_init_db_schema_gate.py`