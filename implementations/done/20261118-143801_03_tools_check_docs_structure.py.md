## Goal
Record the accepted size of ADR-008 in the size exceptions (`REQ-008`) so the documentation structure gate passes after procedure 02.

## Scope
**Release unit**: adr008-size
- In scope: the ADR-008 entry of the per-file size exceptions and its comment (scope amendment decided by the maintainer for this Plan).

## Assumptions
- Procedure 02 has changed `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`; the accepted size is its final byte count (`wc -c`), read after the last ADR-008 edit.
- The entry currently records 37291 and the ceiling equals the accepted size, so further growth fails.

## Design decisions
- Set the value to the exact final size; keep the neighbouring entries untouched.

## Alternatives considered
N/A: the maintainer's earlier direction allows exceeding the document size limit for an ADR.

## Implementation
### Target file
`tools/check_docs_structure.py`

### Procedure
1. Read the final size of `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` with `wc -c`.
2. Replace `37291` in the `"adr_02_05_008_db-sqlite-4db-separation.md"` entry with that size and extend the entry's comment with one line: the ceiling was re-accepted at the new size for the six-database scope, rules, and inventory.

### Method
- The value is an `int` literal in the `SIZE_EXCEPTIONS` mapping; no other line changes.

### Details
- If a later edit of ADR-008 changes its size, re-run `wc -c` and update the value again.
- `tools/check_docs_structure.py` is a tool file: pass its path to `uv run mypy` explicitly (`routing.md` "Adding a new tool").

## Compatibility considerations
N/A: a ceiling value only.

## Security considerations
N/A: no new input.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_structure.py`, `uv run pytest tests/tools/test_check_docs_structure.py`, `uv run ruff check tools/check_docs_structure.py`, `uv run mypy tools/check_docs_structure.py`, `uv run python tools/check_module_size.py`.

## Completion criteria
- The entry equals the final ADR-008 size and `check_docs_structure.py` reports no finding.

## Out of Scope
- Other entries and the default limit.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the ADR-008 size ceiling (Implementation > Procedure) | Completed | 20261118-150735 | 20261118-150735 | Changed: tools/check_docs_structure.py (ADR-008 ceiling 44006). ruff, mypy, tests pass. |
| 2 | Add or update tests per Validation plan: no test change needed; run the existing test | Completed | 20261118-150735 | 20261118-150735 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-150735 | 20261118-150735 | — |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20261117-123008_adrchk008_db-data-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-142957_adrchk008_db-data-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-143801
- **Related target files**: `tools/check_docs_structure.py`
