# Implementation Procedure: Verify EventBus Document Guide consistency with Registry

## Goal

Verify that `docs/24_eventbus/eventbus_00_document-guide.md` is consistent with the final Registry content after splitting `eventbus.persistence-schema` into two Decision Targets. Confirm no changes are needed since the guide already defers to the Registry.

## Scope

- Read only `docs/24_eventbus/eventbus_00_document-guide.md`.
- In-Scope: Verifying consistency with the final Registry content; confirming no changes are needed.
- Out-of-Scope: Modifying the Registry (REQ-001); aligning schema authority statement (REQ-002); checking persistence schema doc for schema authority statements (REQ-004); adding Canonical Source Conflict entry (REQ-005).

## Assumptions

- The EventBus Document Guide currently defers to the Registry for canonical sources (confirmed during canon002 investigation).
- The guide's deference means it will automatically reflect any Registry updates without needing modification.

## Design decisions

- **Approach**: Read the document and verify that it defers to the Registry. If it does, no changes are needed. If it maintains its own canonical-source mapping, update it per the same pattern used in other area guides.
- **Decision**: Based on canon002 evidence collection, the guide already defers to the Registry — no change required.

## Alternatives considered

- Update the guide proactively even though it already defers — rejected because unnecessary changes risk introducing errors.
- Add explicit references to the two new Decision Targets — rejected because the guide's deference to the Registry makes this redundant.

## Implementation

### Target file

`docs/24_eventbus/eventbus_00_document-guide.md`

### Procedure

1. Read the document and locate the canonical-source section.
2. Verify it defers to the Registry.
3. Confirm no changes are needed.

### Method

Read `docs/24_eventbus/eventbus_00_document-guide.md` and verify consistency. No edits required based on canon002 evidence collection.

### Details

**Step 1: Read the document**

```bash
cat docs/24_eventbus/eventbus_00_document-guide.md
```

**Step 2: Verify Registry deference**

Search for the canonical-source section:

```bash
rg -n "Canonical Source Rule|Registry" docs/24_eventbus/eventbus_00_document-guide.md
```

Expected result: The guide states that canonical sources are defined in the Registry and does not maintain its own mapping.

**Step 3: Confirm no changes needed**

Based on canon002 evidence collection, the guide already defers to the Registry. No modifications required.

## Compatibility considerations

- None expected — the guide already defers to the Registry.

## Security considerations

N/A: read-only verification; no runtime security surface.

## Rollback considerations

N/A — no changes made.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/24_eventbus/eventbus_00_document-guide.md` | Manual verification | `rg -n "Canonical Source Rule|Registry" docs/24_eventbus/eventbus_00_document-guide.md` | Confirms Registry deference |

## Completion criteria

- The EventBus Document Guide defers to the Registry for canonical sources.
- No contradictory canonical source declaration remains in the guide.
- No changes are needed — the guide is already consistent with the Registry.

## Out of scope

Updating the Registry (REQ-001). Aligning schema authority statement (REQ-002). Checking persistence schema doc for schema authority statements (REQ-004). Adding Canonical Source Conflict entry (REQ-005). Changes to EventBus schema DDL or migration code. Policy `## Area Canonical Maps` cleanup (canon001). Fixing CANONICAL-006 false positives (canon003).

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read the document and locate canonical-source section | Pending | — | — | REQ-003 |
| 2 | Verify Registry deference | Pending | — | — | REQ-003 |
| 3 | Confirm no changes needed | Pending | — | — | REQ-003 |

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
- **Requirement ID**: REQ-003 — resolve Registry validation failure for eventbus.persistence-schema and stale notes paths
- **Source issue**: N/A: no standalone requirement document is generated
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-222937_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-224701
- **Related target files**: docs/24_eventbus/eventbus_00_document-guide.md
