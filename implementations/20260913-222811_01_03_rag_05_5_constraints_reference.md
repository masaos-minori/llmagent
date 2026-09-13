## Goal

Add the `chunking_strategy` field's "no enum enforced in code" Needs Confirmation item to `docs/03_rag_05_5-constraints-reference.md`'s Constraints table, mirroring the existing `lang` row's format and evidence citation style (REQ-001, REQ-002).

## Scope

- Add one row to the Constraints table documenting `chunking_strategy` validation scope
- Extend the Evidence section with a bullet citing `pipeline_utils.py:217` and the `"text"`/`"heading"` convention values

## Assumptions

- The Constraints Reference table (`docs/03_rag_05_5-constraints-reference.md`) is the correct, established tracking location for this class of item
- The existing `lang` row's format (line 29) is the precedent to follow exactly
- `pipeline_utils.py:217` remains the current validation call site for `chunking_strategy`

## Design decisions

1. Mirror the `lang` row's exact format (field name, validation scope, convention note, Needs Confirmation parenthetical) rather than inventing a new format
2. Do not create a new "Known Issues inventory" document — the Constraints Reference table already serves this purpose for field-level validation-scope Needs Confirmation questions

## Alternatives considered

1. Creating a dedicated "Known Issues inventory" document for the RAG ingestion pipeline — rejected because no such document exists in this repository area, unlike the MCP documentation area which has `docs/04_mcp_90_inconsistencies_and_known_issues.md`
2. Adding the item only inline in `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` — insufficient because the repository's convention is to surface such items in the centralized Constraints Reference table

## Implementation

### Target file

`docs/03_rag_05_5-constraints-reference.md`

### Procedure

1. Confirm the exact current evidence line numbers before citing them
2. Add a `chunking_strategy validation scope` row to the Constraints table, immediately after the `lang validation scope` row (line 29)
3. Extend the Evidence section with a bullet citing `pipeline_utils.py:217` and the `"text"`/`"heading"` convention values

### Method

Phase 1: Preparation — confirm evidence line numbers
- Re-confirm `pipeline_utils.py:217`'s `_validate_str(data, "chunking_strategy", "chunk")` call is still the current validation site before citing it (REQ-002; `docs/03_rag_05_5-constraints-reference.md`)

Phase 2: Core Logic — add the row and evidence bullet
- Add a `chunking_strategy validation scope` row to the Constraints table, immediately after the `lang validation scope` row, mirroring its format (REQ-001; `docs/03_rag_05_5-constraints-reference.md`)
- Extend the Evidence section with a bullet citing `pipeline_utils.py:217` and the `"text"`/`"heading"` convention values (REQ-002; `docs/03_rag_05_5-constraints-reference.md`)

### Details

**Phase 1:** Verify via `rg -n "_validate_str.*chunking_strategy" scripts/rag/ingestion/pipeline_utils.py` that line 217 still contains the validation call. Current source confirms: `chunking_strategy = _validate_str(data, "chunking_strategy", "chunk")`.

**Phase 2:** Insert the following row into the Constraints table after the `lang validation scope` row (line 29):

```
| `chunking_strategy` validation scope | Any non-empty string accepted at parse time (`_validate_str`); the `"text"`/`"heading"` value set is a convention only, not enforced in code (Needs confirmation: whether a closed value set is intended) |
```

Extend the Evidence section with a bullet referencing `pipeline_utils.py:217` and the `"text"`/`"heading"` convention values, consistent with the existing `lang` row's evidence citation pattern at lines 34-37.

## Compatibility considerations

This is a documentation-only additive change. No backward compatibility concerns.

## Security considerations

No security impact — documentation addition only.

## Rollback considerations

Simple revert: remove the added row from the Constraints table and the corresponding Evidence bullet.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_05_5-constraints-reference.md | Manual — review new row/evidence bullet for format consistency | `rg -n "chunking_strategy" docs/03_rag_05_5-constraints-reference.md` | New row and evidence bullet present, no duplication |

## Completion criteria

- [ ] `docs/03_rag_05_5-constraints-reference.md`'s Constraints table contains a `chunking_strategy` row stating it accepts any non-empty string, that `"text"`/`"heading"` are convention-only, and that enforcement is an open Needs Confirmation question (REQ-001)
- [ ] The Evidence section cites `pipeline_utils.py:217` (or the current accurate line reference at implementation time) as the concrete validation call site (REQ-002)
- [ ] The new row's wording and structure matches the existing `lang` row's pattern (field name, validation scope, convention note, Needs Confirmation parenthetical) (REQ-001)

## Out of scope

- Implementing enum validation for `chunking_strategy` itself (this Plan tracks the open question, it does not resolve it)
- Creating a new "Known Issues inventory" document

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Confirm the exact current evidence line numbers | Pending | — | — | |
| 2 | Phase 2: Add the row and evidence bullet | Pending | — | — | |
| 3 | Verification: manual review | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260913-183004_chunking_strategy_enforcement_needs_confirmation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-203130_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-222811
- **Related target files**: docs/03_rag_05_5-constraints-reference.md
