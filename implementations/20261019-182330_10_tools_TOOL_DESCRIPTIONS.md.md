## Goal
- Update the stale ADR file name or shape cited in `tools/TOOL_DESCRIPTIONS.md` (`REQ-005` (state the naming rule and registry)).

## Scope
- In scope: `tools/TOOL_DESCRIPTIONS.md` only.
- Out of scope: every other file (they have their own procedure documents), ADR content, and historical archives.

## Assumptions
- The Plan's group registry and new names are accepted (Plan Assumptions, UNK-02).
- The 14 renames happen in this one change, so no intermediate state is published.

## Design decisions
- Documentation text only; use the new name or shape verbatim.

## Alternatives considered
- N/A: a stale mention has no sensible alternative.

## Implementation
### Target file

`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Update the `check_adr_structure.py` row for the new shape.
### Method
- Edit only the mention described in the Plan evidence: row for `check_adr_structure.py` mentions the old shape. No code logic changes.
### Details
- Docstring or comment text only; behavior is unchanged.

## Compatibility considerations
- N/A: no behavior change.

## Security considerations
- N/A: no security impact.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py`

## Completion criteria
- No old ADR file name or shape remains in the file.

## Out of Scope
- Modifying any file other than the target file; ADR decisions, IDs, status, and invariants; `issues/done/`, `plans/done/`, `implementations/done/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the mention | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/done/20261019-170548_adrname001_group-adr-file-names-by-theme.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-173513_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-182330
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
