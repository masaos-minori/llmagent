# Implementation Procedure: Align db_02_architecture_and_schema-schema-reference.md with Registry

## Goal

Update `docs/41_db/db_02_architecture_and_schema-schema-reference.md` to align its schema authority statement with the final Registry content after splitting `eventbus.persistence-schema` into two Decision Targets.

## Scope

- Modify only `docs/41_db/db_02_architecture_and_schema-schema-reference.md`.
- In-Scope: Updating the schema authority statement to reference the two separate Decision Targets instead of listing both files as co-equal authorities under a single target.
- Out-of-Scope: Updating the Registry (REQ-001); verifying EventBus Document Guide consistency (REQ-003); checking persistence schema doc for schema authority statements (REQ-004); adding Canonical Source Conflict entry (REQ-005).

## Assumptions

- Line 49 of this document contains the schema authority statement that needs updating.
- The split Decision Targets are: `eventbus.persistence-schema.bootstrap-ddl` and `eventbus.persistence-schema.incremental-migration`.
- The current statement reads: "Schema authority: `scripts/db/schema_sql.py::build_eventbus_schema_sql()` (bootstrap DDL) and `scripts/eventbus/db.py` (incremental migration at service startup — see [db_03_architecture_and_schema-migration-and-scaling.md](db_03_architecture_and_schema-migration-and-scaling.md) section 8b)."

## Design decisions

- **Approach**: Update the schema authority statement to explicitly reference the two Decision Targets, making clear they are now separate entries in the Registry rather than co-equal authorities under a single target.
- **Alternative considered**: Deleting the schema authority statement entirely — rejected because it provides useful context about how the EventBus schema is managed.

## Alternatives considered

- Keep the current statement and add a note about the split — rejected because the current statement implies a single Decision Target, which is misleading after the split.
- Delete the schema authority statement — rejected because it provides useful operational context.

## Implementation

### Target file

`docs/41_db/db_02_architecture_and_schema-schema-reference.md`

### Procedure

1. Locate the schema authority statement on line 49.
2. Replace it with an updated version that references the two Decision Targets.

### Method

Edit `docs/41_db/db_02_architecture_and_schema-schema-reference.md` in-place using targeted edit on line 49.

### Details

**Step 1: Locate the schema authority statement**

```bash
rg -n "schema.*authority|build_eventbus_schema_sql|eventbus\.db\.py" docs/41_db/db_02_architecture_and_schema-schema-reference.md
```

**Step 2: Update the statement**

Before:
> Schema authority: `scripts/db/schema_sql.py::build_eventbus_schema_sql()` (bootstrap DDL) and `scripts/eventbus/db.py` (incremental migration at service startup — see [db_03_architecture_and_schema-migration-and-scaling.md](db_03_architecture_and_schema-migration-and-scaling.md) section 8b).

After:
> Schema authority: `scripts/db/schema_sql.py::build_eventbus_schema_sql()` (bootstrap DDL, Decision Target `eventbus.persistence-schema.bootstrap-ddl`) and `scripts/eventbus/db.py` (incremental migration at service startup, Decision Target `eventbus.persistence-schema.incremental-migration`).

## Compatibility considerations

- Existing references to the original `eventbus.persistence-schema` Decision Target in this document must be updated to reference the new targets.
- The link to `db_03_architecture_and_schema-migration-and-scaling.md` should remain valid if the file still exists.

## Security considerations

N/A: documentation-only change; no runtime security surface.

## Rollback considerations

Revert the schema authority statement to its original form.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Structure check | `uv run python tools/check_docs_structure.py` | Pass |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Quality check | `uv run python tools/check_docs_quality.py` | Pass |

## Completion criteria

- The schema authority statement explicitly references both Decision Targets (`eventbus.persistence-schema.bootstrap-ddl` and `eventbus.persistence-schema.incremental-migration`).
- No reference to the original `eventbus.persistence-schema` Decision Target remains in the statement.
- The document does not contradict the Registry content.

## Out of scope

Updating the Registry (REQ-001). Verifying EventBus Document Guide consistency (REQ-003). Checking persistence schema doc for schema authority statements (REQ-004). Adding Canonical Source Conflict entry (REQ-005). Changes to EventBus schema DDL or migration code. Policy `## Area Canonical Maps` cleanup (canon001). Fixing CANONICAL-006 false positives (canon003).

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate the schema authority statement | Pending | — | — | REQ-002 |
| 2 | Update the statement to reference Decision Targets | Pending | — | — | REQ-002 |

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
- **Requirement ID**: REQ-002 — resolve Registry validation failure for eventbus.persistence-schema and stale notes paths
- **Source issue**: N/A: no standalone requirement document is generated
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-222937_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-224701
- **Related target files**: docs/41_db/db_02_architecture_and_schema-schema-reference.md
