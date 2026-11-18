## Goal
Re-record the ADR-004 per-file size ceiling at the accepted size after procedure 06 (REQ-010).

## Scope
**Release unit**: N/A: not part of a release unit
- The one `SIZE_EXCEPTIONS` value of ADR-004; fallout of procedure 06.

## Assumptions
- Fallout file: it is outside the Issue's Target Files list and is reported to the owner as a scope amendment.
- The ceiling equals the accepted size, as the neighboring entries do; the value is read after procedure 06 (`wc -c`).
- The module is not baselined for size growth (it is under the tools size limit); a value with the same number of digits changes no byte count. Run the size gate to confirm.

## Design decisions
- Change the integer only; add no comment unless the module-size gate allows it.

## Alternatives considered
Trimming ADR-004 to fit was rejected: it would rewrite unrelated decision text.

## Implementation
### Target file
`tools/check_docs_structure.py`
### Procedure
1. After procedure 06, read the byte size of the ADR-004 file.
2. Set its `SIZE_EXCEPTIONS` value to that size.
3. Run the structure check and the module size gate.
### Method
Edit the integer in place; do not touch other entries.
### Details
- If procedure 06 was not applied (decision pending), this procedure is not run.

## Compatibility considerations
N/A: a size limit value.

## Security considerations
N/A: a size limit value.

## Rollback considerations
Revert only this procedure's own changes with `git checkout -- <path>` on each changed path (single-path revert; no bulk form).

## Validation plan
- `uv run python tools/check_docs_structure.py`
- `uv run pytest tests/tools/test_check_docs_structure.py`
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`
- `uv run ruff format <changed files>`, `uv run ruff check <changed files>`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`

## Completion criteria
- `tools/check_docs_structure.py` passes with the ADR-004 ceiling equal to its size (AC-9).

## Out of Scope
- Raising any other ceiling.
- Changing the default limit.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read the ADR-004 size after procedure 06 | Pending | — | — | Skip the procedure if procedure 06 was not applied |
| 2 | Set the ceiling to that size | Pending | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: `REQ-010`: ADR-004 size ceiling
- **Source issue**: issues/20261117-123006_adrchk006_rag-failure-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-124317_adrchk006_rag-failure-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-124938
- **Related target files**: `tools/check_docs_structure.py`
