# Implementation Procedure — scripts/mcp_servers/mdq/db_schema.py

## Goal

Read the canonical mdq shape from the shared module so the same text is both the create-path DDL
and the identity source, and expose `mdq_schema_id` (new) through this module (REQ-003, REQ-001).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-003 (canonical identity from the single DDL source), REQ-001 (definition
comparison). Acceptance criterion: AC-2.

## Assumptions
- Full form: this row moves the canonical DDL text out of the mdq layer, which changes the module's
  persistence and import contract.
- The mdqmcp004 plan executes first (Plan dependency bullet), so the DDL constants this row moves
  already carry the renamed `documents` columns and the new `chunks` columns.
- The DDL text and the hash live in `scripts/shared/mdq_schema.py` (new) (Plan row 19); this
  document does not define that module's contents.
- `tests/mcp_servers/mdq/test_db_schema.py` is a Plan row with its own document (row 14), so it is
  not a companion here.

## Design decisions
- No DDL literal stays in this file: the module imports the shared text and passes it to
  `assert_matches`, so the create path and the fingerprint input cannot drift apart.
- The identity value is computed by the shared module and only read here, which keeps `shared` a
  leaf under the `shared-is-leaf` contract.

## Alternatives considered
- Keep the DDL constants here and let the snapshot builder read them: rejected, because
  `.importlinter` (lines 20-28) forbids `shared` importing `mcp_servers`.

## Implementation
### Target file
`scripts/mcp_servers/mdq/db_schema.py`

### Procedure
- Replace the five DDL constants (`_DOCUMENTS_DDL` line 26, `_CHUNKS_DDL` line 37,
  `_CHUNKS_FTS_DDL` line 58, `_FTS_SYNC_TRIGGERS_DDL` line 70, `_INDEX_STATE_DDL` line 94) with the
  shared module's text: `from shared.mdq_schema import MDQ_CANONICAL_DDL, mdq_schema_id (new)`.
- Keep `create_production_tables()` (line 112) as the create-and-validate entry point; the
  `assert_matches` call at lines 132-134 passes the shared text instead of the locally joined
  string.

### Method
- The create branch executes the shared statements in the order the shared module declares them, so
  a fresh database is built from the same text the fingerprint compares.
- The module-level docstring (lines 6-9) is updated to say the canonical shape is owned by the
  shared module.

### Details
- Statement order stays documents, chunks, chunks_fts, the three triggers, index_state, so the
  existing read-path `SELECT` shapes and the trigger bodies are unaffected.
- The refusal label `mdq.sqlite` at line 133 is unchanged.

## Compatibility considerations
- `tests/mcp_servers/mdq/test_db_schema.py` pins the table names (lines 41, 82) and the mismatch
  message (line 124); the shape is unchanged, so those assertions keep passing.
- `deploy/init_db.sh` has no mdq gate; the identity is new published metadata only.

## Security considerations
- N/A: no path, permission, or secret handling changes; the published identity is a hash.

## Rollback considerations
- Reverting the import restores the local constants; a database built from the shared text matches
  the same shape, so no recreation is required by this row alone.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_schema_identity.py tests/mcp_servers/mdq/test_db_schema.py`
- `uv run lint-imports` — `shared-is-leaf` stays KEPT.
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- The file contains no DDL literal and imports the shared canonical text.
- The identity value this module exposes changes only when the canonical shape changes (AC-2).

## Out of Scope
- The shared module itself (Plan row 19); the FTS5 comparison (row 2); readiness and the health
  publication (row 4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by Plan rows 8 and 14 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `uv run lint-imports` included |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | `docs/22_mcp/mcp_04_04_mdq.md` (row 15) |

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
- **Requirement ID**: REQ-003 (canonical identity from the single DDL source), REQ-001
  (definition comparison)
- **Source issue**: `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-003946
- **Related target files**: `scripts/mcp_servers/mdq/db_schema.py`
