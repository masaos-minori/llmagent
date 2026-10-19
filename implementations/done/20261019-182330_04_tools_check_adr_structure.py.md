## Goal
- Make `tools/check_adr_structure.py` recognise ADR files of the new shape (`REQ-003` (update name-shape patterns and size ceilings)).

## Scope
- In scope: `tools/check_adr_structure.py` only.
- Out of scope: every other file (they have their own procedure documents), ADR content, and historical archives.

## Assumptions
- The Plan's group registry and new names are accepted (Plan Assumptions, UNK-02).
- The 14 renames happen in this one change, so no intermediate state is published.

## Design decisions
- Keep a strict anchored pattern so only ADR files are checked.

## Alternatives considered
- Loosen to `^adr_02_.*\.md$`: rejected, it would accept malformed names.

## Implementation
### Target file

`tools/check_adr_structure.py`

### Procedure
1. Change `_ADR_FILE_RE` (line 174) to `^adr_02_\d{2}_\d{3}_.*\.md$`.
2. Update the module docstring item that cites `adr_02_NNN_*.md`.
### Method
- Edit the regex and the docstring; the two uses (lines 193 and 237) need no change.
### Details
- A non-matching name is skipped silently by both checks, so the guard tests in the tests row are the proof that the regex matches the real files.

## Compatibility considerations
- The old shape no longer matches by design.

## Security considerations
- N/A: no security impact.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools -q`
- `uv run python tools/check_adr_structure.py` (live run on the renamed tree)
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
| 1 | Change `_ADR_FILE_RE` and the docstring | Completed | 20261019-205728 | 20261019-205728 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261019-205728 | 20261019-205728 | Targeted tests (tests/tools 1049 passed), ruff/mypy/lint-imports pass, doc checkers pass. Full suite NOT run: denied by auto-mode classifier. Pending user decision; not archived. Stale clean. ruff/mypy/lint-imports/bandit ok; tests/tools 1049 passed; full suite (user-run) 9577 passed, 22 skipped; /opt/llm snapshot identical; doc checkers pass. Step 4 full-suite shared across the batch. |

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
- **Related target files**: tools/check_adr_structure.py