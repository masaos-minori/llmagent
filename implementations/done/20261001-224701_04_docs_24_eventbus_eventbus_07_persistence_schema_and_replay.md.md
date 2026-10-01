# Implementation Procedure: Check persistence schema doc for schema authority alignment

## Goal

Check whether `docs/24_eventbus/eventbus_07_persistence_schema_and_replay.md` restates schema authority and align it with the final Registry content if needed.

## Scope

- Modify only `docs/24_eventbus/eventbus_07_persistence_schema_and_replay.md` if it contains schema authority statements that need updating.
- In-Scope: Checking for schema authority statements; aligning them with the two Decision Targets if found.
- Out-of-Scope: Updating the Registry (REQ-001); aligning schema authority statement in db_02_architecture_and_schema-schema-reference.md (REQ-002); verifying EventBus Document Guide consistency (REQ-003); adding Canonical Source Conflict entry (REQ-005).

## Assumptions

- This document may contain schema authority statements that reference the original single `eventbus.persistence-schema` Decision Target.
- If no schema authority statements exist in this document, no changes are needed.

## Design decisions

- **Approach**: Search for schema authority statements in the document. If found, update them to reference the two Decision Targets (`eventbus.persistence-schema.bootstrap-ddl` and `eventbus.persistence-schema.incremental-migration`). If not found, confirm no changes are needed.
- **Alternative considered**: Proactively updating all schema-related references — rejected because only confirmed statements should be changed.

## Alternatives considered

- Update all schema-related references even if not explicitly stated as authority — rejected because only authoritative statements should be updated.
- Leave the document unchanged if no explicit schema authority is stated — adopted if no statements are found.

## Implementation

### Target file

`docs/24_eventbus/eventbus_07_persistence_schema_and_replay.md`

### Procedure

1. Search for schema authority statements in the document.
2. If found, update them to reference the two Decision Targets.
3. If not found, confirm no changes are needed.

### Method

Edit `docs/24_eventbus/eventbus_07_persistence_schema_and_replay.md` in-place using targeted edits if schema authority statements are found.

### Details

**Step 1: Search for schema authority statements**

```bash
rg -n "schema.*authority|persistence-schema|build_eventbus_schema_sql|eventbus\.db\.py" docs/24_eventbus/eventbus_07_persistence_schema_and_replay.md
```

**Step 2: If schema authority statements are found**

Update each statement to reference the two Decision Targets:

Before:
> Schema authority: `scripts/db/schema_sql.py::build_eventbus_schema_sql()` (bootstrap DDL) and `scripts/eventbus/db.py` (incremental migration at service startup).

After:
> Schema authority: `scripts/db/schema_sql.py::build_eventbus_schema_sql()` (bootstrap DDL, Decision Target `eventbus.persistence-schema.bootstrap-ddl`) and `scripts/eventbus/db.py` (incremental migration at service startup, Decision Target `eventbus.persistence-schema.incremental-migration`).

**Step 3: If no schema authority statements are found**

Confirm no changes are needed. Document this finding in the execution status.

## Compatibility considerations

- Existing references to the original `eventbus.persistence-schema` Decision Target must be updated to reference the new targets if they exist in this document.

## Security considerations

N/A: documentation-only change; no runtime security surface.

## Rollback considerations

Revert any schema authority statement changes to their original form.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/24_eventbus/eventbus_07_persistence_schema_and_replay.md` | Structure check | `uv run python tools/check_docs_structure.py` | Pass |
| `docs/24_eventbus/eventbus_07_persistence_schema_and_replay.md` | Quality check | `uv run python tools/check_docs_quality.py` | Pass |

## Completion criteria

- If schema authority statements exist: they explicitly reference both Decision Targets (`eventbus.persistence-schema.bootstrap-ddl` and `eventbus.persistence-schema.incremental-migration`).
- If no schema authority statements exist: confirmed and documented.
- The document does not contradict the Registry content.

## Out of scope

Updating the Registry (REQ-001). Aligning schema authority statement in db_02_architecture_and_schema-schema-reference.md (REQ-002). Verifying EventBus Document Guide consistency (REQ-003). Adding Canonical Source Conflict entry (REQ-005). Changes to EventBus schema DDL or migration code. Policy `## Area Canonical Maps` cleanup (canon001). Fixing CANONICAL-006 false positives (canon003).

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Search for schema authority statements | Pending | — | — | REQ-004 |
| 2 | Update statements if found | Pending | — | — | REQ-004 |
| 3 | Confirm no changes if not found | Pending | — | — | REQ-004 |

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
- **Requirement ID**: REQ-004 — resolve Registry validation failure for eventbus.persistence-schema and stale notes paths
- **Source issue**: N/A: no standalone requirement document is generated
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-222937_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-224701
- **Related target files**: docs/24_eventbus/eventbus_07_persistence_schema_and_replay.md
