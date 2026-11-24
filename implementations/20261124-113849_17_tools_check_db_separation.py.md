## Goal
Update the rule reference in the module docstring to the new path (REQ-003).

## Scope
**Release unit**: adr008-rename

- Edits only `tools/check_db_separation.py`; part of the single rename commit, because a renamed file with an unupdated reference fails the reference, link, and ceiling checks.

## Assumptions
- The rename and all reference updates land in one commit; the rename procedure (seq 01) runs first, so after it the old file name no longer exists.
- This procedure names the old and the new file name as plain text (not in backticks) so the stale check does not look for a file that the rename has moved; the new path is declared `(new)` once, in the rename procedure.
- Only the old-name references listed in Procedure change; no other text of the file is edited, and no archived issue, plan, or procedure is touched.

## Design decisions
- A pure name replacement; no wording, order, or format change.

## Alternatives considered
N/A: mechanical rename; the Plan fixes the approach.

## Implementation
### Target file
`tools/check_db_separation.py`

### Procedure
1. In the module docstring rule line, replace the path docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md with docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md.

### Method
- Use the Edit tool on the docstring line.

### Details
- Docstring only; no code change.

## Compatibility considerations
N/A: a path or name change only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_db_separation.py`; `uv run pytest tests/tools/test_check_db_separation.py -q`; `uv run ruff format tools/check_db_separation.py`, `uv run ruff check tools/check_db_separation.py`, `uv run mypy tools/check_db_separation.py`, `uv run bandit tools/check_db_separation.py`.
- `uv run python tools/check_docs_quality.py` for document targets.

## Completion criteria
- The docstring names the new path; the tool validations are clean and the check reports no violation.

## Out of Scope
- Any other file, any content edit, archived issues, plans, and procedures, and the two status baseline files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the tool file per Implementation | Pending | — | — | |
| 2 | Run the tool tests per Validation plan | Pending | — | — | |
| 3 | Run ruff, mypy, and bandit on the file | Pending | — | — | Release unit adr008-rename |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261124-112759_adrren001_rename-adr-008-file.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-113352_adrren001_rename-adr-008-file.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-113849
- **Related target files**: `tools/check_db_separation.py`
