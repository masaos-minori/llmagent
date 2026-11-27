# Implementation Procedure — scripts/shared/mdq_schema.py

## Goal

Own the canonical mdq DDL text and the normalized-DDL identity computation in the shared layer, so the
mdq schema entry point and the execution-snapshot builder read the same source without the shared layer
importing the mdq layer (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-003 (canonical identity from the single DDL source). Acceptance criterion: AC-2.

## Assumptions
- Full form: this is a new shared module that defines a public contract (the canonical text and the
  identity value) read by two consumers.
- The `.importlinter` contract `shared-is-leaf` (lines 20-28) forbids `shared` importing `mcp_servers`
  or `db`, which is why the text cannot stay in `scripts/mcp_servers/mdq/db_schema.py` (row 1).
- Precedent: `scripts/shared/mcp_dedup_schema.py` owns canonical DDL and its fingerprint in the shared
  layer (`_SCHEMA_FINGERPRINT` at line 104), and `docs/41_db/db_08_active_databases.md` line 70 records
  it as the schema authority for that store.
- The module is a leaf: it holds statement text and the identity function, opens no connection, and
  performs no config discovery.
- Normalization is the one row 2 owns, exposed as `normalize_ddl` (new), so the identity hash and the
  comparison use the same normalization.

## Design decisions
- The module exposes the statement list and the identity, not an execution path: creation stays with
  `create_production_tables()` in the mdq layer, so the shared module does not become a second writer.
- The identity is computed over the normalized text, so formatting, comments, and line breaks do not
  change it (AC-2).
- The identity is computed at import time as a module-level constant, matching the dedup precedent, so
  consumers read a value rather than recompute a hash.

## Alternatives considered
- Keep the DDL in the mdq layer and let `scripts/shared/execution_snapshot.py` import it: rejected,
  because it breaks `shared-is-leaf`.
- Duplicate the DDL text in the shared module and keep the mdq constants: rejected, because two sources
  defeat REQ-003.

## Implementation
### Target file
`scripts/shared/mdq_schema.py` (new)

### Procedure
- Create the module with the canonical statement constants and `MDQ_CANONICAL_DDL` (new), the joined
  canonical text, and `mdq_schema_id` (new), the identity over the normalized text.
- Statement order: documents, chunks, chunks_fts, the three FTS synchronization triggers, index_state —
  the order row 1 executes.

### Method
- `mdq_schema_id` (new) hashes `normalize_ddl` (new) of the canonical text with `hashlib.sha256` and
  returns the 64-character hex string, consistent with the dedup precedent.
- The module docstring carries the header path and states that the mdq layer imports the text rather
  than the reverse.

### Details
- The trigger statements are part of the canonical text, so the identity covers the trigger definitions
  as well as the tables.

## Compatibility considerations
- Consumers: `scripts/mcp_servers/mdq/db_schema.py` (row 1) imports the text,
  `scripts/shared/execution_snapshot.py` (row 3) reads the identity, and
  `docs/41_db/db_09_mcp_dedup_and_execution_snapshot.md` (row 18) documents the component.
- `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` line 109 names the mdq schema
  creation source; row 17 aligns it with the shared module.

## Security considerations
- N/A: the module holds DDL text and a hash; no path, permission, secret, or row content.

## Rollback considerations
- Reverting this module requires row 1 to restore its local constants, so rollback is a coordinated
  revert of both rows; a database built from the shared text matches the same shape, so no data change
  is involved.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_schema_identity.py`
- `uv run lint-imports` — `shared-is-leaf` stays KEPT.
- `uv run python tools/check_module_size.py` (new module under the 24576 B gate),
  `uv run python tools/check_docstrings.py`.
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- The canonical text and the identity live in this module and nowhere else, and the identity changes only
  when the canonical shape changes (AC-2).

## Out of Scope
- The definition comparison (row 2); the snapshot component (row 3); the health publication (row 4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 3 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by Plan row 8 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `lint-imports` and the module size gate included |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | `docs/41_db/db_09_mcp_dedup_and_execution_snapshot.md` (row 18) |

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
- **Requirement ID**: REQ-003 (canonical `mdq_schema_id` (new) from the single DDL source)
- **Source issue**: `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-003946
- **Related target files**: `scripts/shared/mdq_schema.py`
