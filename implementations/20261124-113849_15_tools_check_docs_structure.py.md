## Goal
Rename the size-ceiling key of the renamed ADR to the new base name, value unchanged (REQ-003).

## Scope
**Release unit**: adr008-rename

- Edits only `tools/check_docs_structure.py`; part of the single rename commit, because a renamed file with an unupdated reference fails the reference, link, and ceiling checks.

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
`tools/check_docs_structure.py`

### Procedure
1. In `SIZE_EXCEPTIONS`, change the key adr_02_05_008_db-sqlite-4db-separation.md to adr_02_05_008_db-six-sqlite-store-separation.md; keep the value 46907 and the comment block above it.
2. Re-record three ceilings by the bytes the longer name adds (measured in Step 3a): governance_03 36807 to 36837, adr_01_index 41389 to 41401, and the ADR-006 file 39575 to 39581; add a comment line to each entry stating the new value and that the ceiling equals the accepted size (the existing convention of the dictionary).
3. Leave the short form `adr_02_05_008` in the comment unchanged.

### Method
- Use the Edit tool on the one dictionary line.

### Details
- Without the key rename the renamed ADR falls back to the 32768-byte default; without the re-record three documents exceed their ceilings.
- Re-record only after the document procedures are applied, and use `wc -c` of each document, not the arithmetic in this procedure, if they differ.
- Do not change any other ceiling here.

## Compatibility considerations
N/A: a path or name change only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_structure.py`; `uv run pytest tests/tools/test_check_docs_structure.py -q`; `uv run ruff format tools/check_docs_structure.py`, `uv run ruff check tools/check_docs_structure.py`, `uv run mypy tools/check_docs_structure.py`, `uv run bandit tools/check_docs_structure.py`.
- `uv run python tools/check_docs_quality.py` for document targets.

## Completion criteria
- The key names the new base name with value 46907, the three ceilings equal the new sizes, `check_docs_structure.py` passes, and the tool validations are clean.

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
- **Related target files**: `tools/check_docs_structure.py`
