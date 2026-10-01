# Implementation Procedure: Update Registry for eventbus.persistence-schema split and fix stale notes

## Goal

Update `config/documentation_canonical_sources.toml` so the Registry validator passes: split `eventbus.persistence-schema` into two Decision Targets (bootstrap DDL vs incremental migration), fix nonexistent paths in both entries' `notes` fields, remove embedded line numbers, and align the `area` field to `EventBus` for all three entries.

## Scope

- Modify only `config/documentation_canonical_sources.toml`.
- In-Scope: Splitting `eventbus.persistence-schema` into two entries; fixing `eventbus.core-behavior` notes path; removing embedded line numbers from all notes; aligning area field to EventBus.
- Out-of-Scope: Aligning referencing documents (REQ-002–REQ-004); adding Canonical Source Conflict entry (REQ-005).

## Assumptions

- ADR-008 INV-04 establishes `eventbus.sqlite` as the system of record for Events, Offsets, Delivery, and DLQ state.
- The split between bootstrap DDL (`scripts/db/schema_sql.py::build_eventbus_schema_sql()`) and incremental migration (`scripts/eventbus/db.py`) represents two distinct operational concerns.
- `docs/41_db/db_02_architecture_and_schema-schema-reference.md` is the correct replacement for the nonexistent `docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md`.
- `docs/24_eventbus/eventbus_00_document-guide.md` is the correct replacement for the nonexistent `docs/06_eventbus_00_document-guide.md`.
- The `migration-script` claim type is recognized by the validator (not restricted like `database-schema`).

## Design decisions

- **Approach**: Split the `eventbus.persistence-schema` Decision Target into two separate entries — one for bootstrap DDL (`claim_type='database-schema'`, single source `scripts/db/schema_sql.py`) and one for incremental migration (`claim_type='migration-script'`, single source `scripts/eventbus/db.py`). This resolves the validator failure without changing the exemption set.
- **Alternative considered**: Registering both under a single `claim_type='runtime-behavior'` entry — rejected because schema definition is not runtime behavior; the claim type would misrepresent the nature of the source.
- **Alternative considered**: Amending the registry contract through the proper governance route — rejected because this issue scope does not include governance rule changes.
- **Notes path resolution**: Replace nonexistent paths with their current equivalents after confirming the referenced content exists in the new location. Remove embedded line numbers per the constraint.
- **Area ownership**: Set `area = "EventBus"` for all three entries, consistent with `eventbus.core-behavior` and the fact that the persistence schema governs EventBus data.

## Alternatives considered

- One file is the normative schema source and the other is registered under a different claim type or Decision Target: adopted (see above).
- The Decision Target is split into separately registered targets (bootstrap DDL vs. migration): adopted (same as above).
- The registry contract itself is amended through the proper governance route: rejected — outside this issue's scope.

## Implementation

### Target file

`config/documentation_canonical_sources.toml`

### Procedure

1. Read ADR-008 INV-04 and `docs/41_db/db_02_architecture_and_schema-schema-reference.md` to confirm evidence.
2. Replace the existing `eventbus.persistence-schema` entry and update `eventbus.core-behavior` notes.

### Method

Edit `config/documentation_canonical_sources.toml` in-place using targeted edits.

### Details

**Step 1: Evidence Collection**

```bash
# Confirm ADR-008 INV-04 text
rg -n "INV-04.*eventbus.sqlite" docs/10_adr/ADR-008-sqlite-4db-separation.md

# Confirm schema authority statement
rg -n "schema.*authority|build_eventbus_schema_sql|eventbus\.db\.py" docs/41_db/db_02_architecture_and_schema-schema-reference.md

# Confirm EventBus Document Guide Registry deference
rg -n "Canonical Source Rule|Registry" docs/24_eventbus/eventbus_00_document-guide.md
```

**Step 2: Registry Updates**

Replace the existing entries:

Before:
```toml
[[canonical_sources]]
decision_target = "eventbus.core-behavior"
claim_type = "runtime-behavior"
source_paths = ["scripts/eventbus/"]
area = "EventBus"
notes = "docs/06_eventbus_00_document-guide.md line 41 states code (scripts/eventbus/) is canonical for behavior."

[[canonical_sources]]
decision_target = "eventbus.persistence-schema"
claim_type = "database-schema"
source_paths = ["scripts/db/schema_sql.py", "scripts/eventbus/db.py"]
area = "Shared/DB"
notes = "docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md line 49 states scripts/db/schema_sql.py::build_eventbus_schema_sql() and scripts/eventbus/db.py are schema authority, backed by ADR-008."
```

After:
```toml
[[canonical_sources]]
decision_target = "eventbus.core-behavior"
claim_type = "runtime-behavior"
source_paths = ["scripts/eventbus/"]
area = "EventBus"
notes = "EventBus Document Guide defers to the Registry for canonical sources."

[[canonical_sources]]
decision_target = "eventbus.persistence-schema.bootstrap-ddl"
claim_type = "database-schema"
source_paths = ["scripts/db/schema_sql.py"]
area = "EventBus"
notes = "Bootstrap DDL for eventbus.sqlite schema, backed by ADR-008."

[[canonical_sources]]
decision_target = "eventbus.persistence-schema.incremental-migration"
claim_type = "migration-script"
source_paths = ["scripts/eventbus/db.py"]
area = "EventBus"
notes = "Incremental migration at service startup for eventbus.sqlite, backed by ADR-008."
```

Key changes:
1. Split `eventbus.persistence-schema` into two Decision Targets.
2. Fix `eventbus.core-behavior` notes path from nonexistent `docs/06_eventbus_00_document-guide.md` to current guide.
3. Remove embedded line numbers from all notes fields.
4. Align `area` field to `EventBus` for all three entries.

## Compatibility considerations

- The split Decision Targets preserve the semantic distinction between bootstrap DDL and incremental migration.
- Existing references to the original `eventbus.persistence-schema` Decision Target must be updated to reference the new targets.
- The `area` field alignment to `EventBus` may affect downstream tooling that relies on area-based grouping.

## Security considerations

N/A: documentation-only change; no runtime security surface.

## Rollback considerations

Restore the original Registry entries and revert document alignment changes.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `config/documentation_canonical_sources.toml` | Registry validation | `uv run python tools/check_canonical_source_registry.py` | Pass (exit 0) |
| All affected docs | Conflict detection | `uv run python tools/check_canonical_source_conflicts.py` | Pass (may have false positives due to canon003) |

## Completion criteria

- `uv run python tools/check_canonical_source_registry.py` exits 0.
- No Registry `notes` value cites a nonexistent path or a document line number.
- Each `database-schema` Decision Target in the Registry has exactly one normative source.
- If the decision could not be made, a Canonical Source Conflict entry exists with Decision Target, competing sources, evidence, and required decision, and this is reported instead of claiming resolution.

## Out of scope

Aligning referencing documents (REQ-002–REQ-004). Adding Canonical Source Conflict entry (REQ-005). Changes to EventBus schema DDL or migration code. Policy `## Area Canonical Maps` cleanup (canon001). Fixing CANONICAL-006 false positives (canon003). Adding Registry entries for other areas.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Evidence Collection | Pending | — | — | REQ-001 |
| 2 | Phase 2: Decision Making | Pending | — | — | REQ-001 |
| 3 | Phase 3: Registry Updates | Pending | — | — | REQ-001 |

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
- **Requirement ID**: REQ-001 — resolve Registry validation failure for eventbus.persistence-schema and stale notes paths
- **Source issue**: N/A: no standalone requirement document is generated
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-222937_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-224701
- **Related target files**: config/documentation_canonical_sources.toml
