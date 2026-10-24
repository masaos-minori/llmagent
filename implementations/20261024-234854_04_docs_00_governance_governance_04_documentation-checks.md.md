## Goal
- State in section 8 of `docs/00_governance/governance_04_documentation-checks.md` that an empty or partial glob match set is an error (`REQ-005`: document the empty-match error).

## Scope
- Edit section "8. Documentation Structure Validation (`check_docs_structure.py`)" only: one bullet or sentence near the `Usage:` block.

## Assumptions
- Section 8 spans lines 167-181 at time of writing and has no empty-match statement (read 2026-10-24).
- No GV table row is added: the refusal is an invocation-usage contract (Plan Assumptions).
- The document is English; the new text MUST be English and MUST NOT introduce a Related section.

## Design decisions
- Add a sentence under the validation list: when any supplied glob matches no file the tool prints `no files matched the given glob(s): ...` to stderr and exits non-zero.

## Alternatives considered
N/A: documentation-only row.

## Implementation
### Target file
`docs/00_governance/governance_04_documentation-checks.md`

### Procedure
1. Insert the sentence between the validation bullet list and the `**Usage:**` block of section 8.
2. Keep the existing usage commands unchanged.

### Method
- Edit in place; do not renumber sections or touch the GV table.

### Details
- Do not name the exit code literal beyond "non-zero"; the docs content policy discourages implementation detail.

## Compatibility considerations
N/A: documentation-only.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py "docs/**/*.md"`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria
- Section 8 states the empty and partial match failure; all four checkers report no findings.

## Out of Scope
- Other governance sections, the GV table, and any other docs chapter.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the empty/partial-match statement to section 8 | Pending | — | — | |
| 2 | Run the docs checkers named in Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (document the empty-match error)
- **Source issue**: `issues/20261024-124138_docs010_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-214856_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-234854
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`
