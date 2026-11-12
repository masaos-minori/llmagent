## Goal
Update `tools/TOOL_DESCRIPTIONS.md` for the changed checkers and list the new helper module (`REQ-007` / `AC-7`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `check_tool_descriptions_sync.py` requires a row for each `tools/*.py`, including `_docs_content_policy_helpers.py`; rows for `check_docs_content_policy.py` (lines 86 and 180) and `check_known_deviation_sync.py` (lines 93 and 170) need the new behavior (verified 2026-11-12; both tools appear in a summary table and a detail table).
- Overlap: `plans/20261112-122408_rmcompat008_compat-checker-patterns.md` also edits this file (different rows; compatible).

## Design decisions
- One new row for the helper; edit the two existing tools' descriptions in place.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Add the helper row.
2. Update the two descriptions.
3. Run `check_tool_descriptions_sync.py`.

### Method
- Describe purpose and failure behavior only, matching the surrounding rows.

### Details
- Do not change other tools' rows.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` — pass; docs checkers pass.

## Completion criteria
- Every `tools/*.py` has a description row; the changed tools' rows describe the new behavior.

## Out of Scope
- Other tools' descriptions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-223108 | 20261112-224437 | Helper row added to the Index table and the shared-base detail table; check_docs_content_policy.py rows (Index and detail) and check_known_deviation_sync.py rows (Index and detail) updated for the widened header shape and the bullet-without-ID ERROR; no other rows touched |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112-224437 | 20261112-224437 | check_tool_descriptions_sync.py: No issues found (exit 0); full suite 12167 pass |

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
- **Requirement ID**: `REQ-007` — tool descriptions match the changed tools
- **Source issue**: issues/20261109-113351_adrrev018_docs-checker-harden.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-111505_adrrev018_docs-checker-harden.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124203
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`