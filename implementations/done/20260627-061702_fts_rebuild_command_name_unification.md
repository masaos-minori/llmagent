## Goal

Unify the FTS rebuild command name across implementation, CLI help, and RAG operations docs by correcting `/db fts-rebuild` to `/db rebuild-fts`.

## Scope

**In-Scope**:
- Correct `/db fts-rebuild` to `/db rebuild-fts` in `03_rag_05_configuration_and_operations.md` (line 340)

**Out-of-Scope**:
- Redesigning /db command architecture
- Changing unrelated DB maintenance commands

## Assumptions

1. `/db rebuild-fts` is the canonical command name — confirmed by implementation in `cmd_db.py:67` and CLI help text
2. No alias exists for `/db fts-rebuild` in the current implementation

## Implementation

### Target file: docs/03_rag_05_configuration_and_operations.md

**Procedure**: Correct FTS rebuild command name from `/db fts-rebuild` to `/db rebuild-fts`.

**Method**: Modify line 340 of the RAG operations documentation.

**Details**:
1. Line 340: Change `/db fts-rebuild` to `/db rebuild-fts`
2. Verify all docs agree on canonical command name by cross-checking all remaining references in docs and implementation

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_05_configuration_and_operations.md | Verify FTS rebuild command name corrected | Check line 340 | `/db rebuild-fts` present, no `/db fts-rebuild` |
| All docs + implementation | Verify all references use canonical name | Search for both patterns across all files | Zero `/db fts-rebuild` references; all use `/db rebuild-fts` |

## Risks

- **Risk**: No risks identified — this is a straightforward documentation correction to match existing implementation | **Likelihood**: N/A | **Mitigation**: N/A | False
