## Goal
- Update the stale ADR file name or shape cited in `scripts/shared/tool_routing_validation.py` (`REQ-002` (replace old ADR file names)).

## Scope
- In scope: `scripts/shared/tool_routing_validation.py` only.
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

`scripts/shared/tool_routing_validation.py`

### Procedure
1. Replace the ADR-003 file name in the module docstring.
### Method
- Edit only the mention described in the Plan evidence: docstring path to ADR-003. No code logic changes.
### Details
- Docstring or comment text only; behavior is unchanged. Because the file is part of the production binaries, `tools/manage_binaries.py check` will report them stale until the next deploy; no behavior change.

## Compatibility considerations
- N/A: no behavior change.

## Security considerations
- N/A: no security impact.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run ruff check` and `uv run ruff format --check` on the file, then `uv run mypy` for the Python files (`rules/toolchain.md`).
- `uv run python tools/check_docs_consistency.py --domain overview` is not required; run the checker named in the Plan row's Related Tests if it exists.

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
- **Requirement ID**: `REQ-002`
- **Source issue**: issues/done/20261019-170548_adrname001_group-adr-file-names-by-theme.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-173513_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-182330
- **Related target files**: scripts/shared/tool_routing_validation.py
