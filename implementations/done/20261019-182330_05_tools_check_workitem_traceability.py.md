## Goal
- Make the ADR-number resolver in `tools/check_workitem_traceability.py` find files of the new shape (`REQ-003` (update name-shape patterns and size ceilings)).

## Scope
- In scope: `tools/check_workitem_traceability.py` only.
- Out of scope: every other file (they have their own procedure documents), ADR content, and historical archives.

## Assumptions
- The Plan's group registry and new names are accepted (Plan Assumptions, UNK-02).
- The 14 renames happen in this one change, so no intermediate state is published.

## Design decisions
- A `??` wildcard keeps the lookup keyed by ADR number only.

## Alternatives considered
- Resolve through `adr_01_index.md`: rejected, a larger change than needed.

## Implementation
### Target file

`tools/check_workitem_traceability.py`

### Procedure
1. Change the glob at line 333 to `docs/10_adr/adr_02_??_{id}_*.md` (two-character group wildcard before the ADR number).
### Method
- Edit the f-string glob in the ADR mention resolver; no other change.
### Details
- Verify with `ADR-002` and `ADR-014` mentions in an active work item (or the existing traceability tests) that the glob returns exactly one file.

## Compatibility considerations
- The old shape would match nothing after the rename; both never coexist.

## Security considerations
- N/A: no security impact.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools -q`
- `uv run python tools/check_workitem_traceability.py` (live run on the renamed tree)
- `rules/toolchain.md` sequence for the changed Python file.

## Completion criteria
- The glob resolves every `ADR-NNN` mentioned by active work items.

## Out of Scope
- Modifying any file other than the target file; ADR decisions, IDs, status, and invariants; `issues/done/`, `plans/done/`, `implementations/done/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change the glob | Completed | 20261019-205729 | 20261019-205729 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261019-205729 | 20261019-205729 | Targeted tests (tests/tools 1049 passed), ruff/mypy/lint-imports pass, doc checkers pass. Full suite NOT run: denied by auto-mode classifier. Pending user decision; not archived. Stale clean. ruff/mypy/lint-imports/bandit ok; tests/tools 1049 passed; full suite (user-run) 9577 passed, 22 skipped; /opt/llm snapshot identical; doc checkers pass. Step 4 full-suite shared across the batch. |

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
- **Related target files**: tools/check_workitem_traceability.py