## Goal
List the new ADR structure checks in the check documentation (fallout of REQ-009 and REQ-010).

## Scope
**Release unit**: N/A: not part of a release unit
- `### 10. ADR Structure Check` only.

## Assumptions
- Fallout file: it is outside the Issue's Target Files list and is reported to the owner as a scope amendment.
- `### 18. ADR Section Header Compliance` covers headings only and needs no change.

## Design decisions
- Two bullets in the existing list style; no GV rule row exists for this checker.

## Alternatives considered
N/A: single list addition.

## Implementation
### Target file
`docs/00_governance/governance_04_documentation-checks.md`
### Procedure
Add two bullets: the ADR `## Status` value must be in the set the policy governance document defines (Error); each `Current Decision Approval (pending)` bullet must cite an ADR approval ledger ID that resolves (Error).
### Method
Edit in place after the existing four bullets.
### Details
- Mirror the wording of row 16's checks; do not copy the allowed values (name the policy document instead).

## Compatibility considerations
N/A: wording-only.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`

## Completion criteria
- `### 10. ADR Structure Check` lists the Status and pending-form checks.

## Out of Scope
- Adding a GV rule row.
- Editing `### 18. ADR Section Header Compliance`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the checker procedure (row 16) is done | Completed | 20261118-110351 | 20261118-110351 | Stop if not Checker procedure (row 16) is done |
| 2 | Add the two bullets | Completed | 20261118-110036 | 20261118-110351 | Two bullets added to ### 10. ADR Structure Check. The owner instructed that the size limit may be exceeded and set the docs limit to 32KB (session 2026-11-18): MAX_SIZE is now 32768 in tools/check_docs_structure.py (a scope addition by the owner's decision) and the per-file ceilings at or below 32768 were removed; ADR-004 and ADR-008 keep theirs. tools/check_docs_structure.py shrank to 20257 B, so its stale entry was removed from tools/check_module_size_tools_baseline.txt |
| 3 | Run the documentation checkers listed in Validation plan | Completed | 20261118-110351 | 20261118-110351 | docs structure/quality/content-policy/japanese, adr_structure, tool_descriptions_sync, module size, ruff, mypy, bandit, tests/tools/test_check_docs_structure.py (82 pass): pass; full suite 12705 passed, 7 skipped; diff-cover N/A (no scripts/ change) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | governance_04 exceeds its per-file size ceiling in tools/check_docs_structure.py (outside this procedure's scope) | Yes: the owner raised the docs size limit to 32768 B (tools/check_docs_structure.py) | 20261118 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-009`: Status value check; `REQ-010`: pending-form check (documentation sync)
- **Source issue**: issues/20261117-123011_adrchk011_adr-approval-governance.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-092611_adrchk011_adr-approval-governance.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-093859
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`
