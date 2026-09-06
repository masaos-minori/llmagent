## Goal
Add two canonical-source entries to `config/documentation_canonical_sources.toml`:
`eventbus.core-behavior` (runtime-behavior, source `scripts/eventbus/`) and
`eventbus.persistence-schema` (database-schema, sources `scripts/db/schema_sql.py`,
`scripts/eventbus/db.py`), migrating the two confirmed-unambiguous findings from
REQ-005.

## Scope
- **In-Scope**: create `config/documentation_canonical_sources.toml` with the two
  EventBus entries per REQ-005; TOML format matching M-01-04's registry schema.
- **Out-of-Scope**: every other registry entry (Agent `tool-routing` already exists);
  updating `docs/06_eventbus_00_document-guide.md` (REQ-006, separate procedure);
  marking stale Area Canonical Maps paths (REQ-009, separate procedure).

## Assumptions
- M-01-04's registry schema is known from `issues/done/20260903-103027_m0104_introduce-machine-readable-canonical-source-registry.md` and `plans/20260905-165405_plan.md`; the file does not exist yet so it must be created from scratch.
- The TOML structure follows M-01-04's precedent: top-level `[canonical_sources]` table with array-of-tables entries containing `decision_target`, `claim_type`, `source_paths`, `area`, `notes`.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Create the file rather than appending — no existing registry file exists; M-01-04's
  registry is new infrastructure being introduced in this cycle.
- Use `source_paths` (plural) for `eventbus.persistence-schema` since two files share
  authority; `eventbus.core-behavior` uses a single directory path.

## Alternatives considered
N/A: straightforward creation of the registry file with two entries; no alternative
approach applies.

## Implementation
### Target file
`config/documentation_canonical_sources.toml`

### Procedure
1. Create `config/documentation_canonical_sources.toml` with the M-01-04 registry schema.
2. Add `eventbus.core-behavior` entry: decision_target=`eventbus.core-behavior`,
   claim_type=`runtime-behavior`, source_paths=[`scripts/eventbus/`], area=`EventBus`,
   notes referencing `docs/06_eventbus_00_document-guide.md` line 41.
3. Add `eventbus.persistence-schema` entry: decision_target=`eventbus.persistence-schema`,
   claim_type=`database-schema`, source_paths=[`scripts/db/schema_sql.py`,
   `scripts/eventbus/db.py`], area=`Shared/DB`, notes referencing
   `docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md` line 49 and ADR-008.

### Method
Create via Write tool using TOML syntax consistent with M-01-04's registry schema.

### Details
- Both entries have no conflicts (Migration Inventory shows `None` conflict status).
- `eventbus.core-behavior`: `docs/06_eventbus_00_document-guide.md` line 41 states code
  (`scripts/eventbus/`) is canonical for behavior.
- `eventbus.persistence-schema`: `docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md`
  line 49 states `scripts/db/schema_sql.py::build_eventbus_schema_sql()` and
  `scripts/eventbus/db.py` are schema authority, backed by ADR-008.

## Compatibility considerations
N/A: governance-tooling config; no runtime reader (per M-01-04's own Design note).

## Security considerations
N/A.

## Rollback considerations
- Delete `config/documentation_canonical_sources.toml` to revert; independent of every
  other procedure document (this file has no callers outside the validator).

## Validation plan
- `uv run python tools/check_canonical_source_conflicts.py` — exits 0, both entries pass.
- Manual diff review confirming changes scoped to canonical-source declarations only (AC9).

## Completion criteria
- `config/documentation_canonical_sources.toml` contains exactly two entries with correct
  decision-target names, claim types, and source paths (AC1).
- `uv run python tools/check_canonical_source_conflicts.py` passes (AC2).

## Out of scope
- Every other registry entry (Agent `tool-routing` already registered).
- Updating `docs/06_eventbus_00_document-guide.md` (REQ-006, separate procedure).
- Marking stale Area Canonical Maps paths (REQ-009, separate procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: config-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-005` (migrate two confirmed-unambiguous canonical-source mappings into registry)
- **Source issue**: issues/20260903-103029_m0106_inventory-and-migrate-existing-canonical-source-declarations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-185329_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185329
- **Related target files**: config/documentation_canonical_sources.toml
