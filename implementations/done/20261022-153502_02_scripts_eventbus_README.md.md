## Goal

Reword the schema-layer line in `scripts/eventbus/README.md` to "Schema definition and creation", matching `scripts/eventbus/schema.py`'s own self-description and dropping the removed "migration logic" responsibility (REQ-002; AC-2).

## Scope

- Modify `scripts/eventbus/README.md` line 10 only (the schema-layer description).
- Leave every other README section, including the "Stub Module Pattern" rule, unchanged.

## Assumptions

- The README line should mirror the wording `schema.py` already uses for itself ("schema definition and creation").

## Design decisions

- Change "migration logic" to "creation" to match `schema.py`'s docstring rather than inventing new wording. The schema-migration paths were removed (commit `31f8c3be9`), so "migration logic" describes code that is not there.

## Alternatives considered

- Reword to "schema definition" only — rejected: REQ-002 specifies the exact phrase "Schema definition and creation", which mirrors `schema.py`'s own self-description.

## Implementation

### Target file

`scripts/eventbus/README.md`

### Procedure

1. Edit line 10's schema-layer description.
2. Confirm the change with a manual review / `rg`.

### Method

Replace line 10:

> 2. **Schema layer** (`schema.py`): Schema definition, migration logic

with:

> 2. **Schema layer** (`schema.py`): Schema definition and creation

### Details

- Evidence in-file: line 10 currently reads "2. **Schema layer** (`schema.py`): Schema definition, migration logic".
- REQ-002 requires the line to read "Schema definition and creation".
- `scripts/eventbus/schema.py` line 1 already uses this exact wording ("Schema layer: schema definition and creation.").
- The README is outside `docs/`, so `check_docs_structure.py` does not apply to it (that checker reports a missing `## Keywords` section for non-docs markdown); validate by manual review.

## Compatibility considerations

N/A: documentation-only change; no runtime contract is affected.

## Security considerations

N/A: no auth, authorization, or input-handling path is described here.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/README.md` | Manual review | `rg -i "migration logic" scripts/eventbus/README.md` | No match; line reads "Schema definition and creation" |

## Completion criteria

Line 10 reads "Schema definition and creation", `rg -i "migration logic" scripts/eventbus/README.md` returns no match, and the README still states that `db.py` is the single entry point.

## Out of Scope

- Editing any other README section, including the "Stub Module Pattern" rule (which already documents `db.py` as the single entry point).
- Any `docs/*.md` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the README schema-layer line to "Schema definition and creation" | Completed | 2026-10-22 | 2026-10-22 | |
| 3 | Run the validation sequence (manual review / `rg`) | Completed | 2026-10-22 | 2026-10-22 | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-10-22 | 2026-10-22 | |

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
- **Requirement ID**: `REQ-002` — reword the README schema-layer line to "Schema definition and creation"
- **Source issue**: `issues/20261022-124204_ebdocwording_align-eventbus-facade-wording.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130514_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-153502
- **Related target files**: `scripts/eventbus/README.md`
