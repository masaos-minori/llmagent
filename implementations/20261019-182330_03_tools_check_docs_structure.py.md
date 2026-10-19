## Goal
- Make `tools/check_docs_structure.py` read the ADR ID from the new file name shape and key the size exceptions by the new names (`REQ-003` (update name-shape patterns and size ceilings)).

## Scope
- In scope: `tools/check_docs_structure.py` only.
- Out of scope: every other file (they have their own procedure documents), ADR content, and historical archives.

## Assumptions
- The Plan's group registry and new names are accepted (Plan Assumptions, UNK-02).
- The 14 renames happen in this one change, so no intermediate state is published.

## Design decisions
- Group 1 of the regex stays the ADR ID so existing consumers need no change.
- Ceilings equal the accepted size, following the file's practice.

## Alternatives considered
- Trim ADR body text to fit the old ceilings: rejected as default (changes ADR content); remains an owner option.

## Implementation
### Target file

`tools/check_docs_structure.py`

### Procedure
1. Change `ADR_ID_RE` to `^adr_02_\d{2}_(\d{3})_` so group 1 stays the three-digit ADR ID; both consumers (`check_unique_adr_ids` and the `## Related ADRs` check) keep working.
2. Rekey `SIZE_EXCEPTIONS` from the four old basenames to the new basenames (ADR-003, ADR-004, ADR-006, ADR-008).
3. After the Phase 3 replacement, measure the new sizes and set the ceilings: ADR-003 and ADR-004 raised to the measured size, and a new entry for ADR-007 (projected 26602, 32305, and 24596; the measured values win).
4. Update the comment above `SIZE_EXCEPTIONS` if it names the old shape.
### Method
- Edit the constant at line 291 and the dictionary entries; the existing owner-accepted-exception practice (ceiling equals accepted size) is followed (Plan assumption, UNK-01).
### Details
- Order: the regex and key changes are made first (tests from step 01 turn green); the three ceiling values are set only after the replacement step has produced the final file sizes (`wc -c`).

## Compatibility considerations
- The regex rejects the old shape by design; the old and new shapes never coexist after the commit.

## Security considerations
- N/A: no security impact.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools -q`
- `uv run python tools/check_docs_structure.py` (live run on the renamed tree)
- `rules/toolchain.md` sequence for the changed Python file.

## Completion criteria
- The pattern accepts the new shape and captures the ADR ID.
- The tests of step 01 and 02 pass against it.

## Out of Scope
- Modifying any file other than the target file; ADR decisions, IDs, status, and invariants; `issues/done/`, `plans/done/`, `implementations/done/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change `ADR_ID_RE` | Pending | — | — | |
| 2 | Rekey `SIZE_EXCEPTIONS` and set the three ceilings after measurement | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: issues/done/20261019-170548_adrname001_group-adr-file-names-by-theme.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-173513_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-182330
- **Related target files**: tools/check_docs_structure.py
