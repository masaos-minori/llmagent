## Goal
- Update the stale ADR file name or shape cited in `tools/check_adr_preservation.py` (`REQ-002` (replace old ADR file names)).

## Scope
- In scope: `tools/check_adr_preservation.py` only.
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

`tools/check_adr_preservation.py`

### Procedure
1. Update the stale ADR file name or shape in the docstring or comment.
### Method
- Edit only the mention described in the Plan evidence: the usage example `docs/10_adr/adr_02_008_sqlite-4db-separation.md`. No code logic changes.
### Details
- Docstring or comment text only; behavior is unchanged.

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
| 1 | Update the mention | Completed | 20261019-205730 | 20261019-205730 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261019-205730 | 20261019-205730 | Targeted tests (tests/tools 1049 passed), ruff/mypy/lint-imports pass, doc checkers pass. Full suite NOT run: denied by auto-mode classifier. Pending user decision; not archived. Stale clean. ruff/mypy/lint-imports/bandit ok; tests/tools 1049 passed; full suite (user-run) 9577 passed, 22 skipped; /opt/llm snapshot identical; doc checkers pass. Step 4 full-suite shared across the batch. |

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
- **Related target files**: tools/check_adr_preservation.py